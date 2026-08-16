import pandas as pd
import os
from app.core.config import settings

# In-memory cache to prevent reloading CSVs on every request
_DATA_CACHE: dict[str, pd.DataFrame] = {}


def load_dataset(granularity: str) -> pd.DataFrame:
    """Loads and caches data from the wide-format CSVs."""
    if granularity in _DATA_CACHE:
        return _DATA_CACHE[granularity]

    # Maps 'monthly' to 'salesmonthly.csv', 'weekly' to 'salesweekly.csv', etc.
    filename = f"sales{granularity}.csv"
    file_path = os.path.join(settings.DATA_DIR, filename)

    if not os.path.exists(file_path):
        return pd.DataFrame()

    df = pd.read_csv(file_path)

    # Ensure the time column is parsed and sorted properly
    if 'datum' in df.columns:
        df['datum'] = pd.to_datetime(df['datum'])
        df = df.sort_values(by=['datum']).reset_index(drop=True)

    _DATA_CACHE[granularity] = df
    return df


def get_categories(granularity: str = "monthly") -> list[str]:
    # Bug Fix: Read from the requested granularity instead of hardcoding "monthly"
    df = load_dataset(granularity)
    if df.empty:
        return []

    # Assuming the first column is 'datum', the rest are categories
    cols = list(df.columns)
    if 'datum' in cols:
        cols.remove('datum')
    return sorted(cols)


def get_category_history(category: str, granularity: str) -> pd.Series:
    """Returns the historical values for a specific category column."""
    df = load_dataset(granularity)

    if df.empty or category not in df.columns:
        return pd.Series(dtype=float)

    # Extract just the specific category column, drop any accidental empty trailing rows
    return df[category].dropna().reset_index(drop=True)