from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy import select, and_
from app.schemas.backtests import RunBacktestRequest, RunBacktestResponse  # <- tire ResultsResponse daqui
from app.services.backtest_service import run_backtest
from app.services.backtest_results_service import get_backtest_results
from app.db.session import get_session_local
from app.db.models import Backtest
import math

router = APIRouter(prefix="/backtests", tags=["backtests"])

# --- helper para limpar NaN/Inf recursivamente ---
def _clean(o):
    try:
        import numpy as np
        np_float = (np.floating,)
        np_int = (np.integer,)
    except Exception:
        np_float = tuple()
        np_int = tuple()

    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(x) for x in o]
    if np_float and isinstance(o, np_float):
        o = float(o)
    if np_int and isinstance(o, np_int):
        o = int(o)
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    # datas: converte para ISO se tiver .isoformat
    if hasattr(o, "isoformat"):
        try:
            return o.isoformat()
        except Exception:
            return None
    return o
# ----------------------------------------

@router.post("/run", response_model=RunBacktestResponse)
def run(body: RunBacktestRequest):
    res = run_backtest(
        ticker=body.ticker,
        start=body.start_date,
        end=body.end_date,
        initial_cash=body.initial_cash,
        commission=body.commission,
        sma_fast=body.sma_fast,
        sma_slow=body.sma_slow,
        atr_window=body.atr_window,
        atr_k=body.atr_k,
        risk_perc=body.risk_perc,
        strategy_type=body.strategy_type,
        strategy_params=body.strategy_params,
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return RunBacktestResponse(**res)

@router.get("/{bt_id}/results")
def results(bt_id: int):
    data = get_backtest_results(bt_id)
    if not data:
        raise HTTPException(status_code=404, detail="Backtest não encontrado")
    return JSONResponse(content=_clean(data))

@router.get("", response_model=list[dict])
def list_backtests(
    ticker: Optional[str] = None,
    strategy_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        conds = []
        if ticker:
            conds.append(Backtest.ticker == ticker)
        if strategy_type:
            conds.append(Backtest.strategy_type == strategy_type)

        stmt = select(Backtest)
        if conds:
            stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(Backtest.created_at.desc()).limit(limit).offset(offset)

        rows = db.execute(stmt).scalars().all()
        out = []
        for r in rows:
            out.append(_clean({
                "id": r.id,
                "ticker": r.ticker,
                "strategy_type": r.strategy_type,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "created_at": r.created_at,
                "metrics": r.metrics or {},
            }))
        return out
