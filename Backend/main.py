

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sklearn.linear_model import LinearRegression

import models
from data_collector import fetch_live_quote, fetch_stock_data, update_all_symbols
from database import (
    KNOWN_SYMBOLS, get_52w_high_low, get_all_symbols,
    load_data, purge_rogue_symbols
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

WATCHLIST: list[str] = sorted(KNOWN_SYMBOLS)





def safe_float(v):
    try:
        import math
        f = float(v)
        return None if math.isnan(f) else f
    except:
        return None


def _isnan(v):
    try:
        import math
        return math.isnan(float(v))
    except:
        return False


def _require_data(symbol: str, days: int = 30) -> pd.DataFrame:
    df = load_data(symbol, days)
    if df.empty:
        fetch_stock_data(symbol)
        df = load_data(symbol, days)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for '{symbol}'")
    return df


def _risk_label(vol: float) -> str:
    if vol < 0.20: return "Low"
    if vol < 0.40: return "Medium"
    return "High"






@asynccontextmanager
async def lifespan(app: FastAPI):
  
    purge_rogue_symbols()
    update_all_symbols(WATCHLIST)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: update_all_symbols(WATCHLIST),
        trigger="interval",
        minutes=60,
        id="bulk_refresh",
        name="Hourly symbol refresh",
    )
    scheduler.start()
    logger.info("Background scheduler started (60-min interval).")

    yield  


    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="Stock Intelligence API",
    version="2.1.0",
    description="NSE/BSE stock data, live quotes, ML price prediction.",
    lifespan=lifespan,  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)




def _require_data(symbol: str, days: int = 30) -> pd.DataFrame:
    df = load_data(symbol, days)
    if df.empty:
        fetch_stock_data(symbol)
        df = load_data(symbol, days)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for '{symbol}'")
    return df


def _risk_label(vol: float) -> str:
    if vol < 0.20: return "Low"
    if vol < 0.40: return "Medium"
    return "High"


def _isnan(v) -> bool:
    try:
        import math
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False




@app.get("/companies", response_model=List[str])
async def companies():
    syms = get_all_symbols()
    return syms if syms else WATCHLIST


@app.get("/data/{symbol}", response_model=List[models.StockDataPoint])
async def stock_data(symbol: str, days: int = Query(30, ge=1, le=365)):
    symbol = symbol.upper()
    df = _require_data(symbol, days)
    hl = get_52w_high_low(symbol)
    result = []
    for idx, row in df.iterrows():
        result.append(models.StockDataPoint(
            date         = idx.date(),
            # open         = float(row.get("Open",  0)),
            # high         = float(row.get("High",  0)),
            # low          = float(row.get("Low",   0)),
            # close        = float(row.get("Close", 0)),
            # volume       = int(  row.get("Volume", 0)),
            # daily_return = row.get("Daily_Return") if not _isnan(row.get("Daily_Return")) else None,
            # ma_7d        = row.get("MA_7D")        if not _isnan(row.get("MA_7D")) else None,
            # volatility   = row.get("Volatility")   if not _isnan(row.get("Volatility")) else None,
            open         = float(row.get("open",  0)),
            high         = float(row.get("high",  0)),
            low          = float(row.get("low",   0)),
            close        = float(row.get("close", 0)),
            volume       = int(  row.get("volume", 0)),
            daily_return = row.get("daily_return") if not _isnan(row.get("daily_return")) else None,
            ma_7d        = row.get("ma_7d")        if not _isnan(row.get("ma_7d"))        else None,
            volatility   = row.get("volatility")   if not _isnan(row.get("volatility"))   else None,
            high_52w     = hl["high_52w"],
            low_52w      = hl["low_52w"],
        ))
    return result


@app.get("/summary/{symbol}", response_model=models.CompanySummary)
async def summary(symbol: str):
    symbol = symbol.upper()
    stats = get_52w_high_low(symbol)
    if stats["last_close"] == 0:
        fetch_stock_data(symbol)
        stats = get_52w_high_low(symbol)
    return models.CompanySummary(
        symbol     = symbol,
        high_52w   = stats["high_52w"],
        low_52w    = stats["low_52w"],
        avg_close  = stats["avg_close"],
        last_close = stats["last_close"],
        volatility = stats.get("volatility"),
    )


@app.get("/live/{symbol}", response_model=models.LiveQuote)
async def live_quote(symbol: str):
    symbol = symbol.upper()
    data = fetch_live_quote(symbol)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return models.LiveQuote(**data)


@app.get("/compare", response_model=models.ComparisonData)
async def compare(symbol1: str = Query(...), symbol2: str = Query(...)):
    s1, s2 = symbol1.upper(), symbol2.upper()
    df1 = _require_data(s1, 30)
    df2 = _require_data(s2, 30)
    common = df1.index.intersection(df2.index)
    if len(common) == 0:
        raise HTTPException(status_code=404, detail="No overlapping trading dates")
    return models.ComparisonData(
        dates   = [d.date() for d in common],
        symbol1 = df1.loc[common, "close"].round(2).tolist(),
        symbol2 = df2.loc[common, "close"].round(2).tolist(),
    )




@app.get("/correlation", response_model=models.CorrelationResult)
async def correlation(
    symbol1: str = Query(...),
    symbol2: str = Query(...),
    days: int = Query(90, ge=10, le=365),
):
    """
    Pearson correlation of daily returns between two symbols.
    Returns r ∈ [-1, +1] and a plain-English interpretation.
    """
    s1, s2 = symbol1.upper(), symbol2.upper()

    if s1 == s2:
        raise HTTPException(status_code=400, detail="symbol1 and symbol2 must be different")

    df1 = _require_data(s1, days)
    df2 = _require_data(s2, days)

    common = df1.index.intersection(df2.index)
    if len(common) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(common)} overlapping days — need at least 10"
        )

    r1 = df1.loc[common, "daily_return"].dropna()
    r2 = df2.loc[common, "daily_return"].dropna()
    common2 = r1.index.intersection(r2.index)

    if len(common2) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough valid daily_return data after removing NaN rows"
        )

    r = float(np.corrcoef(r1.loc[common2].values, r2.loc[common2].values)[0, 1])
    r = round(r, 4)

    if r >= 0.7:   interp = "Strongly correlated — tend to move together"
    elif r >= 0.4: interp = "Moderately correlated"
    elif r >= 0.1: interp = "Weakly correlated"
    elif r >= -0.1:interp = "Essentially uncorrelated"
    elif r >= -0.4:interp = "Weakly inverse — slight opposite movement"
    elif r >= -0.7:interp = "Moderately inverse"
    else:          interp = "Strongly inverse — tend to move in opposite directions"

    return models.CorrelationResult(
        symbol1        = s1,
        symbol2        = s2,
        pearson_r      = r,
        interpretation = interp,
        days_used      = len(common2),
    )


@app.get("/movers", response_model=List[models.MoverItem])
async def top_movers(n: int = Query(5, ge=1, le=20)):
    symbols = get_all_symbols() or WATCHLIST
    results: list[models.MoverItem] = []
    for sym in symbols:
        df = load_data(sym, days=5)
        if df is None or len(df) < 2:
            continue
        last_close = float(df.iloc[-1]["close"])
        prev_close = float(df.iloc[-2]["close"])
        if prev_close == 0:
            continue
        change_pct = round((last_close - prev_close) / prev_close * 100, 2)
        results.append(models.MoverItem(symbol=sym, change_pct=change_pct, last_price=round(last_close, 2)))
    results.sort(key=lambda x: x.change_pct, reverse=True)
    gainers = [m for m in results if m.change_pct >= 0][:n]
    losers  = sorted([m for m in results if m.change_pct < 0], key=lambda x: x.change_pct)[:n]
    return gainers + losers


@app.get("/predict/{symbol}", response_model=models.PredictionResult)
async def predict_price(symbol: str, forecast_days: int = Query(7, ge=1, le=30)):
    symbol = symbol.upper()
    df = _require_data(symbol, 60)
    close_vals = df["close"].dropna().values
    if len(close_vals) < 10:
        raise HTTPException(status_code=400, detail="Not enough data points (need ≥ 10)")
    X = np.arange(len(close_vals)).reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, close_vals)
    future_X = np.arange(len(close_vals), len(close_vals) + forecast_days).reshape(-1, 1)
    forecast = [round(float(v), 2) for v in model.predict(future_X)]
    return models.PredictionResult(symbol=symbol, forecast=forecast)


@app.get("/volatility", response_model=List[models.VolatilityItem])
async def volatility_scores():
    symbols = get_all_symbols() or WATCHLIST
    items: list[models.VolatilityItem] = []
    for sym in symbols:
        stats = get_52w_high_low(sym)
        vol = stats.get("volatility")
        if vol is not None:
            items.append(models.VolatilityItem(symbol=sym, volatility=round(vol, 4), risk_label=_risk_label(vol)))
    items.sort(key=lambda x: x.volatility, reverse=True)
    return items


@app.post("/refresh/{symbol}", status_code=200)
async def refresh_symbol(symbol: str):
    symbol = symbol.upper()
    df = fetch_stock_data(symbol)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for '{symbol}'")
    return {"symbol": symbol, "rows_stored": len(df), "status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)