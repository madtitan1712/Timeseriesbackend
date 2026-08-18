# SalesPrediction — Time-series Sales Prediction Backend

**Summary**

A lightweight FastAPI backend that serves sales time-series forecasts and related utilities for a Pharma sales dashboard. Includes pre-trained models, data ingestion scripts, and automatic DB initialization.

---

## Components

- **app/**: FastAPI application and API routes (forecast, trends, categories, auth, export, diagnostics, etc.).
- **app/data/**: Database connection and initialization logic (Postgres).
- **models/**: Serialized model artifacts (e.g., .joblib files) used for predictions.
- **scripts/**: Utilities for data upload, backtesting and migrations.
- **pyproject.toml**: Project metadata and Python dependencies (Python 3.12+).

---

## Quick start

1. **Create & activate a virtual environment (Windows)**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate
   ```

2. **Install dependencies**

   - If you use UV:
     ```bash
     uv sync
     ```
   - Otherwise, install from the project metadata:
     ```bash
     pip install -e .
     ```

3. **Configure environment variables**

   - Copy `.env.example` to `.env` if provided, or set variables directly.
   - Provide either a full `DATABASE_URL` or the Postgres pieces: `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE`.
   - Optionally set `CORS_ALLOWED_ORIGINS` (defaults allow common localhost origins).

4. **Run the API (development)**

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify**

   - Interactive docs: /docs
   - Health check: `GET /health` → returns JSON with status
