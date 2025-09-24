from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, UniqueConstraint, Index, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=True)
    prices = relationship("Price", back_populates="symbol")
    indicators = relationship("Indicator", back_populates="symbol")


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)

    symbol = relationship("Symbol", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("symbol_id", "date", name="uq_price_symbol_date"),
    )

class Backtest(Base):
    __tablename__ = "backtests"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ticker = Column(String(32), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    strategy_type = Column(String(32), nullable=False)
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)
    params = Column(JSON, nullable=True)
    status = Column(String(16), nullable=False, default="finished")
    metrics = Column(JSON, nullable=True)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    side = Column(String(4), nullable=False)  # BUY/SELL
    price = Column(Float, nullable=False)
    size = Column(Integer, nullable=False)
    pnl = Column(Float, nullable=True)

class DailyPosition(Base):
    __tablename__ = "daily_positions"
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    position = Column(Integer, nullable=False)
    cash = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey("backtests.id"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    value = Column(Float, nullable=True)
    __table_args__ = (UniqueConstraint("backtest_id","name", name="uq_metric_per_backtest"),)

class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)  # ex.: "sma_20", "atr_14"
    value = Column(Float, nullable=True)

    symbol = relationship("Symbol", back_populates="indicators")

    __table_args__ = (
        UniqueConstraint("symbol_id","date","name", name="uq_indicator_symbol_date_name"),
    )

