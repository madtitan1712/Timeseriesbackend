import os
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import audit, auth, categories, compare, diagnostics, export, forecast, freshness, recommendations, \
    trends, data_upload

app = FastAPI(title="Pharma Sales Dashboard API")
from app.data.database import init_db
init_db()
allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
).split(",")

# Browsers block cross-origin requests unless the API explicitly allows the
# frontend origin. Keep this list explicit instead of a wildcard because
# wildcard origins are not compatible with credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(recommendations.router)
app.include_router(auth.router)
app.include_router(data_upload.router)
@app.get("/health")
def health_check():
    """Liveness check for the dashboard build spec."""
    return {"status": "ok", "message": "Pharma Sales Backend is running."}