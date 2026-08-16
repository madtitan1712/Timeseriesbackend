from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import audit, categories, compare, diagnostics, export, forecast, freshness, trends

app = FastAPI(title="Pharma Sales Dashboard API")

# allow_credentials=False here deliberately: allow_origins=["*"] combined
# with allow_credentials=True is rejected by browsers per the CORS spec
# (a wildcard origin can't be paired with credentialed requests). This app
# doesn't use cookies/auth, so there's nothing to gain from credentials
# support — if that changes later, set an explicit origin list instead of
# "*" and turn allow_credentials back on.
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