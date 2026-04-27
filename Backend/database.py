

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import (
    Column, Date, Float, Integer, String,
    UniqueConstraint, create_engine, text
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./stocks.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)




class Base(DeclarativeBase):
    pass


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
    )

    id           = Column(Integer,  primary_key=True, index=True)
    symbol       = Column(String,   nullable=False,   index=True)
    date         = Column(Date,     nullable=False,   index=True)
    open         = Column(Float)
    high         = Column(Float)
    low          = Column(Float)
    close        = Column(Float)
    volume       = Column(Integer)
    daily_return = Column(Float,    nullable=True)
    ma_7d        = Column(Float,    nullable=True)
    volatility   = Column(Float,    nullable=True)   


Base.metadata.create_all(bind=engine)


with engine.connect() as conn:
    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(stock_prices)")).fetchall()]
    if "volatility" not in cols:
        conn.execute(text("ALTER TABLE stock_prices ADD COLUMN volatility REAL"))
        conn.commit()
        logger.info("Migrated: added `volatility` column.")




# KNOWN_SYMBOLS = {
#     "INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK",
#     "SBIN", "BHARTIARTL", "ITC", "WIPRO", "TATAMOTORS",
# }

KNOWN_SYMBOLS = {
    "INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK",
    "SBIN", "BHARTIARTL", "ITC", "WIPRO", "BAJFINANCE",
}


def purge_rogue_symbols() -> None:
    """
    Delete any rows whose symbol is NOT in KNOWN_SYMBOLS.
    This removes legacy contamination like T (AT&T) and TC (US stock)
    that crept in via the old bare-symbol yfinance fallback.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT symbol FROM stock_prices")).fetchall()
        all_db_syms = {r[0] for r in result}
        rogues = all_db_syms - KNOWN_SYMBOLS
        if rogues:
            for sym in rogues:
                conn.execute(
                    text("DELETE FROM stock_prices WHERE symbol = :s"),
                    {"s": sym}
                )
            conn.commit()
            logger.warning("Purged rogue symbols from DB: %s", rogues)
        else:
            logger.info("No rogue symbols found in DB.")




def store_data(symbol: str, df: pd.DataFrame) -> None:
    """
    Upsert OHLCV + metrics rows for `symbol`.
    Rows with an existing (symbol, date) pair are updated in-place.
    """
    session = SessionLocal()
    try:
        for ts, row in df.iterrows():
            row_date = ts.date() if hasattr(ts, "date") else ts
            existing = (
                session.query(StockPrice)
                .filter_by(symbol=symbol, date=row_date)
                .first()
            )
            if existing:
                existing.open         = float(row.get("Open",         existing.open))
                existing.high         = float(row.get("High",         existing.high))
                existing.low          = float(row.get("Low",          existing.low))
                existing.close        = float(row.get("Close",        existing.close))
                existing.volume       = int(  row.get("Volume",       existing.volume))
                existing.daily_return = _safe_float(row.get("Daily_Return"))
                existing.ma_7d        = _safe_float(row.get("MA_7D"))
                existing.volatility   = _safe_float(row.get("Volatility"))
            else:
                session.add(StockPrice(
                    symbol       = symbol,
                    date         = row_date,
                    open         = float(row.get("Open",  0)),
                    high         = float(row.get("High",  0)),
                    low          = float(row.get("Low",   0)),
                    close        = float(row.get("Close", 0)),
                    volume       = int(  row.get("Volume", 0)),
                    daily_return = _safe_float(row.get("Daily_Return")),
                    ma_7d        = _safe_float(row.get("MA_7D")),
                    volatility   = _safe_float(row.get("Volatility")),
                ))
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("[%s] store_data failed: %s", symbol, exc)
    finally:
        session.close()


def _safe_float(value) -> float | None:
    try:
        import math
        f = float(value)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None




def load_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """Return the last `days` rows for `symbol`, sorted ascending by date."""
    session = SessionLocal()
    try:
        query = (
            session.query(StockPrice)
            .filter(StockPrice.symbol == symbol)
            .order_by(StockPrice.date.desc())
            .limit(days)
        )
        df = pd.read_sql(query.statement, session.bind)
    finally:
        session.close()

    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df.sort_index()


def get_all_symbols() -> list[str]:

    session = SessionLocal()
    try:
        all_syms = [r[0] for r in session.query(StockPrice.symbol).distinct().all()]
    finally:
        session.close()
    return sorted(s for s in all_syms if s in KNOWN_SYMBOLS)


def get_52w_high_low(symbol: str) -> dict:
    """52-week summary stats for a symbol."""
    session = SessionLocal()
    try:
        year_ago = date.today() - timedelta(days=365)
        query = (
            session.query(StockPrice)
            .filter(StockPrice.symbol == symbol, StockPrice.date >= year_ago)
            .order_by(StockPrice.date)
        )
        df = pd.read_sql(query.statement, session.bind)
    finally:
        session.close()

    if df.empty:
        return {"high_52w": 0, "low_52w": 0, "avg_close": 0, "last_close": 0, "volatility": None}

    return {
        "high_52w":   float(df["high"].max()),
        "low_52w":    float(df["low"].min()),
        "avg_close":  float(df["close"].mean()),
        "last_close": float(df.iloc[-1]["close"]),
        "volatility": float(df["volatility"].dropna().iloc[-1]) if "volatility" in df.columns and df["volatility"].notna().any() else None,
    }