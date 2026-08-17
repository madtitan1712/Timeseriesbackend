import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("PGUSER", "postgres")
    password = quote_plus(os.getenv("PGPASSWORD", ""))
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE", "postgres")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

DATABASE_URL = _build_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db():
    """Creates both tables if they don't exist. Safe to call on every startup."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                granularity TEXT NOT NULL,
                category TEXT NOT NULL,
                date DATE NOT NULL,
                value REAL NOT NULL,
                UNIQUE(granularity, category, date)
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_sales_lookup ON sales(granularity, category, date)"
        ))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))