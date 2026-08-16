from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import freshness, forecast, trends, diagnostics, compare, export, audit
from app.services import trends_service

app = FastAPI(title="Pharma Sales Dashboard API")

# Allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to "http://localhost:5173" if you want strictness
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

@app.get("/categories")
def list_categories():
    """List categories + available granularities."""
    from app.data.loader import get_categories
    categories = get_categories()
    return {
        "categories": categories,
        "granularities": ["daily", "weekly", "monthly"]
    }
