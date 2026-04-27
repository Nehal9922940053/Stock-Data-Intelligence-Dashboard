
from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel




class StockDataPoint(BaseModel):
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    daily_return: Optional[float] = None
    ma_7d: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    volatility: Optional[float] = None



class CompanySummary(BaseModel):
    symbol:     str
    high_52w:   float
    low_52w:    float
    avg_close:  float
    last_close: float
    volatility: Optional[float] = None


class LiveQuote(BaseModel):
    symbol:     str
    exchange:   str = "NSE"
    last_price: float
    open:       float
    day_high:   float
    day_low:    float
    prev_close: float
    change:     float
    change_pct: float
    volume:     int
    market_cap: int
    currency:   str = "INR"
    error:      Optional[str] = None


class ComparisonData(BaseModel):
    dates:   List[date]
    symbol1: List[float]
    symbol2: List[float]


class PredictionResult(BaseModel):
    symbol:   str
    forecast: List[float]


class MoverItem(BaseModel):
    symbol:     str
    change_pct: float
    last_price: float



class CorrelationResult(BaseModel):
    symbol1:        str
    symbol2:        str
    pearson_r:      float
    interpretation: str
    days_used:      int


class VolatilityItem(BaseModel):
    symbol:     str
    volatility: float      
    risk_label: str        