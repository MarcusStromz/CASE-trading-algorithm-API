# app/services/backtest_service.py
from __future__ import annotations

import backtrader as bt
import pandas as pd
from datetime import date
from typing import Optional, Dict, Any

from sqlalchemy import select, and_

from app.db.session import get_session_local
from app.db.models import Price, Symbol, Backtest, Trade, DailyPosition, Metric
from app.core.strategies import SmaCrossRiskATR, DonchianBreakout, MomentumTF
from app.core.collectors import TradeCollector, EquityDailyCollector


# --- Feed Pandas para Backtrader (colunas em lower-case) ---
class PandasDataBT(bt.feeds.PandasData):
    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("openinterest", None),
    )


def _load_df(ticker: str, start: date, end: date) -> pd.DataFrame | None:
    """
    Lê OHLCV do Postgres e devolve DataFrame indexado por data com colunas lower-case.
    """
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        sym = db.execute(select(Symbol).where(Symbol.ticker == ticker)).scalar_one_or_none()
        if not sym:
            return None

        rows = db.execute(
            select(Price.date, Price.open, Price.high, Price.low, Price.close, Price.volume)
            .where(
                and_(
                    Price.symbol_id == sym.id,
                    Price.date >= start,
                    Price.date <= end,
                )
            )
            .order_by(Price.date.asc())
        ).all()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def run_backtest(
    ticker: str,
    start: date,
    end: date,
    initial_cash: float,
    commission: float,
    sma_fast: int,
    sma_slow: int,
    atr_window: int,
    atr_k: float,
    risk_perc: float,
    strategy_type: str = "sma_cross",
    strategy_params: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Executa o backtest, grava resultados no banco e retorna {backtest_id, metrics}.
    """
    df = _load_df(ticker, start, end)
    if df is None or df.empty or df["close"].dropna().empty:
        return {"error": "Sem dados para o período informado. Rode /data/update antes."}

    cerebro = bt.Cerebro()
    datafeed = PandasDataBT(dataname=df)
    cerebro.adddata(datafeed)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    sp = strategy_params or {}
    if strategy_type == "sma_cross":
        cerebro.addstrategy(
            SmaCrossRiskATR,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
            atr_window=atr_window,
            atr_k=atr_k,
            risk_perc=risk_perc,
        )
    elif strategy_type == "donchian_breakout":
        cerebro.addstrategy(
            DonchianBreakout,
            n_high=sp.get("n_high", 20),
            n_low=sp.get("n_low", 10),
            atr_window=atr_window,
            atr_k=atr_k,
            risk_perc=risk_perc,
        )
    elif strategy_type == "momentum":
        cerebro.addstrategy(
            MomentumTF,
            lookback=sp.get("lookback", 60),
            threshold=sp.get("threshold", 0.0),
            atr_window=atr_window,
            atr_k=atr_k,
            risk_perc=risk_perc,
        )
    else:
        return {"error": "strategy_type inválido"}

    # Analyzers
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="dd")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe")
    cerebro.addanalyzer(TradeCollector, _name="tc")
    cerebro.addanalyzer(EquityDailyCollector, _name="ed")

    strat = cerebro.run()[0]

    # --- Métricas
    final_value = float(cerebro.broker.getvalue())
    try:
        sharpe_a = strat.analyzers.sharpe.get_analysis().get("sharperatio", None)
        sharpe_a = float(sharpe_a) if sharpe_a is not None else None
    except Exception:
        sharpe_a = None

    dd_info = strat.analyzers.dd.get_analysis()
    max_dd = None
    if isinstance(dd_info, dict):
        max_dd = dd_info.get("max", {}).get("drawdown", None)
        try:
            max_dd = float(max_dd) if max_dd is not None else None
        except Exception:
            max_dd = None

    ta = strat.analyzers.ta.get_analysis() or {}
    total_trades = ta.get("total", {}).get("total", None)
    won = ta.get("won", {}).get("total", None)
    lost = ta.get("lost", {}).get("total", None)

    metrics = {
        "final_value": final_value,
        "return_pct": (final_value / initial_cash - 1.0) if initial_cash else None,
        "max_drawdown_pct": max_dd,
        "sharpe_a": sharpe_a,
        "total_trades": total_trades,
        "won": won,
        "lost": lost,
    }

    # --- Coleta
    # IMPORTANTE: agora usamos get_analysis() (o seu código anterior olhava .trades)
    trades = strat.analyzers.tc.get_analysis()         # lista de dicts
    daily = strat.analyzers.ed.get_analysis()          # lista de dicts

    # --- Persistência
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        btrow = Backtest(
            ticker=ticker,
            start_date=start,
            end_date=end,
            strategy_type=strategy_type,
            initial_cash=initial_cash,
            commission=commission,
            params={"sma_fast": sma_fast, "sma_slow": sma_slow, "atr_window": atr_window, "atr_k": atr_k, "risk_perc": risk_perc} | sp,
            status="finished",
            metrics=metrics,
        )
        db.add(btrow)
        db.commit()
        db.refresh(btrow)
        backtest_id = btrow.id

        # trades
        for t in trades:
            # normaliza tipos para o SQLAlchemy
            tdate = pd.to_datetime(t["date"]).date() if isinstance(t["date"], str) else t["date"]
            db.add(
                Trade(
                    backtest_id=backtest_id,
                    date=tdate,
                    side=t.get("side"),
                    price=float(t["price"]) if t.get("price") is not None else None,
                    size=int(t["size"]) if t.get("size") is not None else 0,
                    pnl=float(t["pnl"]) if t.get("pnl") is not None else None,
                )
            )

        # série diária
        for d in daily:
            ddate = pd.to_datetime(d["date"]).date() if isinstance(d["date"], str) else d["date"]
            db.add(
                DailyPosition(
                    backtest_id=backtest_id,
                    date=ddate,
                    position=int(d["position"]),
                    cash=float(d["cash"]),
                    equity=float(d["equity"]),
                )
            )

        # métricas
        for k, v in metrics.items():
            db.add(
                Metric(
                    backtest_id=backtest_id,
                    name=k,
                    value=float(v) if v is not None else None,
                )
            )

        db.commit()

    return {"backtest_id": backtest_id, "metrics": metrics}
