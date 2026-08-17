# app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import audit, categories, compare, diagnostics, export, forecast, freshness, trends
from app.models.registry import warm_up_models

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Blocks startup until every model is loaded, so the first real request
    # is never the one paying for TimesFM's cold start — trade a slower
    # deploy/restart for consistently fast requests afterward.
    warm_up_models()
    yield


app = FastAPI(title="Pharma Sales Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(compare.router)
app.include_router(freshness.router)
app.include_router(forecast.router)
app.include_router(trends.router)
app.include_router(diagnostics.router)
app.include_router(export.router)
app.include_router(audit.router)


@app.get("/health")
def health_check():
    """Liveness check for the dashboard build spec."""
    return {"status": "ok", "message": "Pharma Sales Backend is running."}