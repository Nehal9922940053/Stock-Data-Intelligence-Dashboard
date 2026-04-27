
from __future__ import annotations

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)



REQUIRED_COLS = {"Open", "High", "Low", "Close", "Volume"}


OUTLIER_THRESHOLD = 0.50  




def clean(df: pd.DataFrame, symbol: str = "") -> pd.DataFrame:
    """
    Full cleaning pipeline. Returns a cleaned DataFrame.
    Each step is logged so problems are visible in server output.
    """
    if df is None or df.empty:
        logger.warning("[%s] clean() received empty DataFrame — skipping.", symbol)
        return pd.DataFrame()

    df = df.copy()

    df = _normalise_column_names(df, symbol)
    df = _fix_date_index(df, symbol)
    df = _remove_duplicate_dates(df, symbol)
    df = _drop_all_nan_rows(df, symbol)
    df = _fix_column_types(df, symbol)
    df = _handle_missing_values(df, symbol)
    df = _flag_outliers(df, symbol)
    df = _sort_by_date(df)

    logger.info("[%s] Cleaning complete — %d rows retained.", symbol, len(df))
    return df




def _normalise_column_names(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    yfinance sometimes returns multi-level columns (ticker, field).
    Flatten and standardise to Title Case: Open, High, Low, Close, Volume.
    """
    if isinstance(df.columns, pd.MultiIndex):
        # e.g. ('Close', 'INFY.NS') → 'Close'
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        logger.debug("[%s] Flattened multi-level columns.", symbol)


    df.columns = [str(c).strip() for c in df.columns]


    rename_map = {
        "close": "Close", "open": "Open", "high": "High",
        "low": "Low", "volume": "Volume", "adj close": "Close",
        "Adj Close": "Close", "adj_close": "Close",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})


    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        logger.warning("[%s] Missing expected columns after normalisation: %s", symbol, missing)

    return df




def _fix_date_index(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Ensure the index is a timezone-naive DatetimeIndex.
    yfinance returns tz-aware (UTC) index on some versions — strip the tz.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index, utc=True)
            logger.debug("[%s] Converted index to DatetimeIndex.", symbol)
        except Exception as exc:
            logger.error("[%s] Could not convert index to datetime: %s", symbol, exc)
            return df

    if df.index.tz is not None:
        df.index = df.index.tz_convert("Asia/Kolkata").tz_localize(None)
        logger.debug("[%s] Converted tz-aware index to IST naive.", symbol)


    df.index = df.index.normalize()
    df.index.name = "Date"
    return df




def _remove_duplicate_dates(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    n_before = len(df)
    df = df[~df.index.duplicated(keep="last")]
    n_dropped = n_before - len(df)
    if n_dropped:
        logger.warning("[%s] Dropped %d duplicate date rows.", symbol, n_dropped)
    return df




def _drop_all_nan_rows(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in df.columns]
    if not price_cols:
        return df
    mask = df[price_cols].isna().all(axis=1)
    n = mask.sum()
    if n:
        logger.warning("[%s] Dropping %d rows where all price columns are NaN.", symbol, n)
        df = df[~mask]
    return df




def _fix_column_types(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Cast price columns to float64 and Volume to int64.
    Coerce unparseable values to NaN so subsequent steps handle them.
    """
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(np.int64)

    return df




def _handle_missing_values(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Strategy per column type:
      - Price columns (Open/High/Low/Close): forward-fill then backward-fill.
        Forward-fill carries the last known price across a weekend/holiday gap.
        Backward-fill handles NaN at the very beginning of the series.
      - Volume: fill with 0 (no trade = zero volume).
      - Any remaining NaN after both fills: drop the row.
    """
    price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in df.columns]
    vol_cols   = [c for c in ["Volume"] if c in df.columns]

    before = df[price_cols].isna().sum().sum()

  
    df[price_cols] = df[price_cols].ffill().bfill()

    if vol_cols:
        df[vol_cols] = df[vol_cols].fillna(0)

    after = df[price_cols].isna().sum().sum()
    if before:
        logger.info("[%s] Imputed %d missing price values (ffill + bfill). Remaining NaN: %d",
                    symbol, before, after)


    if after:
        df = df.dropna(subset=price_cols)
        logger.warning("[%s] Dropped %d rows with un-imputable NaN after fill.", symbol, after)

    return df



def _flag_outliers(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Detect rows where the daily Close change exceeds OUTLIER_THRESHOLD.
    We log a warning but do NOT silently remove them — the analyst should
    verify whether it's a real corporate action (split, bonus) or bad data.
    We add an 'is_outlier' boolean flag column so downstream code can filter.
    """
    if "Close" not in df.columns or len(df) < 2:
        return df

    pct_change = df["Close"].pct_change().abs()
    outlier_mask = pct_change > OUTLIER_THRESHOLD
    n_outliers = outlier_mask.sum()

    df["is_outlier"] = outlier_mask.fillna(False)

    if n_outliers:
        bad_dates = df.index[outlier_mask].strftime("%Y-%m-%d").tolist()
        logger.warning(
            "[%s] %d potential price outliers detected (>%.0f%% daily change): %s",
            symbol, n_outliers, OUTLIER_THRESHOLD * 100, bad_dates
        )

    return df




def _sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_index()




def validate_report(df: pd.DataFrame, symbol: str = "") -> dict:
    """
    Returns a dict summarising data quality after cleaning.
    Useful for debugging — call this in a notebook or script.

    Example:
        from data_cleaner import validate_report
        report = validate_report(df, "INFY")
        print(report)
    """
    if df.empty:
        return {"symbol": symbol, "status": "empty"}

    price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in df.columns]
    return {
        "symbol":          symbol,
        "rows":            len(df),
        "date_range":      f"{df.index.min().date()} → {df.index.max().date()}",
        "missing_prices":  int(df[price_cols].isna().sum().sum()),
        "zero_volume_pct": round(float((df["Volume"] == 0).mean() * 100), 1) if "Volume" in df.columns else None,
        "outlier_rows":    int(df["is_outlier"].sum()) if "is_outlier" in df.columns else 0,
        "duplicate_dates": int(df.index.duplicated().sum()),
        "dtypes":          {c: str(df[c].dtype) for c in price_cols},
        "status":          "ok",
    }