from sqlalchemy import select
from app.db.session import get_session_local
from app.db.models import Backtest, Trade, DailyPosition
import math

def _num(x):
    """float seguro para JSON: None se NaN/Inf ou erro."""
    try:
        f = float(x)
        return f if math.isfinite(f) else None
    except Exception:
        return None

def _iso(d):
    try:
        return d.isoformat() if d is not None else None
    except Exception:
        return None

def get_backtest_results(bt_id: int):
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        bt = db.execute(select(Backtest).where(Backtest.id == bt_id)).scalar_one_or_none()
        if not bt:
            return None

        trades_rows = db.execute(
            select(Trade).where(Trade.backtest_id == bt_id).order_by(Trade.date.asc())
        ).scalars().all()

        daily_rows = db.execute(
            select(DailyPosition).where(DailyPosition.backtest_id == bt_id).order_by(DailyPosition.date.asc())
        ).scalars().all()

        raw_metrics = bt.metrics or {}
        metrics = {k: _num(v) if isinstance(v, (int, float)) else v for k, v in raw_metrics.items()}

        trades = [
            {
                "date": _iso(t.date),
                "side": t.side,
                "price": _num(t.price),
                "size": int(t.size) if t.size is not None else 0,
                "pnl": _num(t.pnl),
            }
            for t in trades_rows
        ]

        daily = [
            {
                "date": _iso(d.date),
                "position": int(d.position) if d.position is not None else 0,
                "cash": _num(d.cash),
                "equity": _num(d.equity),
            }
            for d in daily_rows
        ]

        return {
            "backtest_id": bt.id,
            "ticker": bt.ticker,
            "strategy_type": bt.strategy_type,
            "metrics": metrics,
            "trades": trades,
            "daily_positions": daily,
        }
