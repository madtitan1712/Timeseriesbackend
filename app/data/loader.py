import pandas as pd
from sqlalchemy import text
from app.core.config import settings
from app.data.database import engine

_DATA_CACHE: dict[str, pd.DataFrame] = {}


def load_dataset(granularity: str) -> pd.DataFrame:
    if granularity in _DATA_CACHE:
        return _DATA_CACHE[granularity]

    query = text("SELECT date AS datum, category, value FROM sales WHERE granularity = :g ORDER BY date")
    with engine.connect() as conn:
        long_df = pd.read_sql_query(query, conn, params={"g": granularity}, parse_dates=["datum"])

    if long_df.empty:
        return pd.DataFrame()

    df = long_df.pivot(index="datum", columns="category", values="value").reset_index()
    df = df.sort_values(by="datum").reset_index(drop=True)

    _DATA_CACHE[granularity] = df
    return df


def get_categories(granularity: str = "monthly") -> list[str]:
    df = load_dataset(granularity)
    if df.empty:
        return []
    cols = [c for c in df.columns if c in settings.CATEGORY_COLUMNS]
    return sorted(cols)


def get_category_history(category: str, granularity: str) -> pd.Series:
    df = load_dataset(granularity)
    if df.empty or category not in df.columns:
        return pd.Series(dtype=float)
    return df[category].dropna().reset_index(drop=True)