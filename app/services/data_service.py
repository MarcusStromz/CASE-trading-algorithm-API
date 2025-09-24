from typing import Tuple
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import get_session_local
from app.db.models import Symbol, Price, Indicator
from app.adapters.market_data import fetch_ohlcv_yf
from app.core.indicators import sma, atr

def _f(x):
    return float(x) if pd.notna(x) else None

def upsert_prices(symbol_id: int, df: pd.DataFrame) -> int:
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        total = 0
        for _, row in df.iterrows():
            d = row["date"]
            try:
                d = pd.to_datetime(d).date()
            except Exception:
                pass

            stmt = insert(Price).values(
                symbol_id=symbol_id,
                date=d,
                open=_f(row["open"]),
                high=_f(row["high"]),
                low=_f(row["low"]),
                close=_f(row["close"]),
                volume=_f(row["volume"]),
            ).on_conflict_do_update(
                index_elements=["symbol_id","date"],
                set_={
                    "open":  _f(row["open"]),
                    "high":  _f(row["high"]),
                    "low":   _f(row["low"]),
                    "close": _f(row["close"]),
                    "volume":_f(row["volume"]),
                },
            )
            db.execute(stmt)
            total += 1
        db.commit()
        return total
    
from sqlalchemy import and_, delete  
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

def upsert_indicators(symbol_id: int, idx: pd.Index, name: str, values: pd.Series, params: str | None = None) -> int:
    """
    Insere/atualiza indicadores SEM usar a coluna 'params' (que não existe na sua tabela).
    Estratégia simples: delete+insert para a (symbol_id, date, name).
    """
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        total = 0
        for d, v in values.dropna().items():

            try:
                d = pd.to_datetime(d).date()
            except Exception:
                pass

            db.execute(
                delete(Indicator).where(
                    and_(
                        Indicator.symbol_id == symbol_id,
                        Indicator.date == d,
                        Indicator.name == name,
                    )
                )
            )
            db.execute(
                insert(Indicator).values(
                    symbol_id=symbol_id,
                    date=d,
                    name=name,
                    value=float(v),
                )
            )
            total += 1
        db.commit()
        return total


def ensure_symbol(ticker: str) -> int:
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        sym = db.execute(select(Symbol).where(Symbol.ticker == ticker)).scalar_one_or_none()
        if sym:
            return sym.id
        sym = Symbol(ticker=ticker, name=None)
        db.add(sym); db.commit(); db.refresh(sym)
        return sym.id

def update_prices_and_indicators(ticker: str, start: str, end: str, sma_windows=(20,50), atr_window=14) -> dict:
    symbol_id = ensure_symbol(ticker)
    prices = fetch_ohlcv_yf(ticker, start, end)
    inserted_prices = upsert_prices(symbol_id, prices)

    if prices.empty:
        return { "symbol_id": symbol_id, "inserted_prices": 0, "inserted_indicators": 0 }

    df = prices.set_index('date').sort_index()
    inserted_ind = 0

    for w in sma_windows:
        values = sma(df['close'], w)
        inserted_ind += upsert_indicators(symbol_id, df.index, f"sma_{w}", values, f"window={w}")

    values_atr = atr(df[['high','low','close']], atr_window)
    inserted_ind += upsert_indicators(symbol_id, df.index, f"atr_{atr_window}", values_atr, f"window={atr_window}")

    return {"symbol_id": symbol_id, "inserted_prices": inserted_prices, "inserted_indicators": inserted_ind}
