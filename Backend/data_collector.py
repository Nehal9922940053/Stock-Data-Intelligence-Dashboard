

import time
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from database import store_data
from data_cleaner import clean as clean_dataframe

logger = logging.getLogger(__name__)


_HIST_CACHE: dict = {}     
_LIVE_CACHE: dict = {}    

HIST_CACHE_TTL = 3600      
LIVE_CACHE_TTL = 60        




def _resolve_ticker(symbol: str) -> tuple:
    """
    Try NSE (.NS) then BSE (.BO).
    Returns (yf.Ticker, suffix) or (None, '') — NEVER uses bare symbol
    because yfinance would silently return a US-market ticker instead.
    """
    for suffix in (".NS", ".BO"):
        try:
            t = yf.Ticker(symbol + suffix)
            probe = t.history(period="5d")
            if not probe.empty:
                return t, suffix
        except Exception:
            continue
    logger.warning("[%s] Not found on NSE or BSE — skipping.", symbol)
    return None, ""




def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich OHLCV DataFrame with derived columns."""
    df = df.copy()


    df["Daily_Return"] = (df["Close"] - df["Open"]) / df["Open"]

  
    df["MA_7D"] = df["Close"].rolling(window=7, min_periods=1).mean()

  
    df["High_52W"] = df["High"].rolling(window=252, min_periods=1).max()
    df["Low_52W"]  = df["Low"].rolling(window=252, min_periods=1).min()


    daily_vol = df["Daily_Return"].rolling(window=20, min_periods=5).std()
    df["Volatility"] = (daily_vol * (252 ** 0.5)).round(4)

    return df




def fetch_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Return a DataFrame of OHLCV + computed metrics for `symbol`.
    Results are cached for HIST_CACHE_TTL seconds and persisted to SQLite.
    """
    cache_key = f"{symbol}_{period}"
    if cache_key in _HIST_CACHE:
        ts, cached = _HIST_CACHE[cache_key]
        if time.time() - ts < HIST_CACHE_TTL:
            return cached.copy()

    ticker, suffix = _resolve_ticker(symbol)
    if ticker is None:
        return pd.DataFrame()

    try:
        hist = ticker.history(period=period)
    except Exception as exc:
        logger.error("[%s] history() failed: %s", symbol, exc)
        return pd.DataFrame()

    if hist.empty:
        logger.warning("[%s] Empty history (suffix=%s)", symbol, suffix)
        return pd.DataFrame()


    hist = clean_dataframe(hist, symbol)
    if hist.empty:
        logger.warning("[%s] Empty after cleaning — skipping.", symbol)
        return pd.DataFrame()

    
    df = compute_metrics(hist)
    store_data(symbol, df)
    _HIST_CACHE[cache_key] = (time.time(), df)
    logger.info("[%s] Stored %d rows (suffix=%s)", symbol, len(df), suffix)
    return df




def fetch_live_quote(symbol: str) -> dict:
    """
    Return a near-real-time price snapshot using yfinance fast_info.
    Data is cached for LIVE_CACHE_TTL (60 s) to avoid API rate limits.

    Returned dict keys:
        symbol, exchange, last_price, open, day_high, day_low,
        prev_close, change, change_pct, volume, market_cap, currency
    On failure: { symbol, error }
    """
    if symbol in _LIVE_CACHE:
        ts, cached = _LIVE_CACHE[symbol]
        if time.time() - ts < LIVE_CACHE_TTL:
            return cached

    ticker, suffix = _resolve_ticker(symbol)
    if ticker is None:
        return {"symbol": symbol, "error": "Symbol not found on NSE/BSE"}

    try:
        fi    = ticker.fast_info
        last  = float(fi.last_price  or 0)
        prev  = float(fi.previous_close or 0)
        chg   = last - prev
        chg_p = (chg / prev * 100) if prev else 0.0

        result = {
            "symbol":      symbol,
            "exchange":    "NSE" if suffix == ".NS" else "BSE",
            "last_price":  round(last,        2),
            "open":        round(float(fi.open      or 0), 2),
            "day_high":    round(float(fi.day_high  or 0), 2),
            "day_low":     round(float(fi.day_low   or 0), 2),
            "prev_close":  round(prev,         2),
            "change":      round(chg,          2),
            "change_pct":  round(chg_p,        2),
            "volume":      int(fi.last_volume  or 0),
            "market_cap":  int(fi.market_cap   or 0),
            "currency":    str(fi.currency     or "INR"),
        }
    except Exception as exc:
        logger.error("[%s] fast_info failed: %s", symbol, exc)
        result = {"symbol": symbol, "error": str(exc)}

    _LIVE_CACHE[symbol] = (time.time(), result)
    return result




def update_all_symbols(symbols: list) -> None:
    """Refresh historical data for every symbol in the watchlist."""
    logger.info("Refreshing %d symbols…", len(symbols))
    for sym in symbols:
        try:
            fetch_stock_data(sym)
        except Exception as exc:
            logger.error("[%s] update failed: %s", sym, exc)
    logger.info("Bulk refresh complete.")