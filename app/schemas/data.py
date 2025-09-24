from pydantic import BaseModel, field_validator
from datetime import date

class UpdateDataRequest(BaseModel):
    ticker: str
    start: date
    end: date
    sma_fast: int = 20
    sma_slow: int = 50
    atr_window: int = 14

    @field_validator("ticker")
    @classmethod
    def strip_up(cls, v: str) -> str:
        return v.strip()

class UpdateDataResponse(BaseModel):
    symbol_id: int
    inserted_prices: int
    inserted_indicators: int
