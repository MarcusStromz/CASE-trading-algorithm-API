
from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict, Any, List, Literal

class RunBacktestRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    initial_cash: float = 100000
    commission: float = 0.0

    sma_fast: int = 20
    sma_slow: int = 50
    atr_window: int = 14
    atr_k: float = 2.0
    risk_perc: float = 0.01

    strategy_type: Literal["sma_cross", "donchian_breakout", "momentum"] = "sma_cross"
    strategy_params: Optional[Dict[str, Any]] = None

class RunBacktestResponse(BaseModel):
    backtest_id: int
    metrics: Dict[str, Any]

class TradeOut(BaseModel):
    date: date
    side: str
    price: float
    size: int
    pnl: float | None = None

class DailyOut(BaseModel):
    date: date
    position: int
    cash: float
    equity: float

class ResultsResponse(BaseModel):
    backtest_id: int
    ticker: str
    strategy_type: str
    metrics: Dict[str, Any]
    trades: List[TradeOut]
    daily_positions: List[DailyOut]
