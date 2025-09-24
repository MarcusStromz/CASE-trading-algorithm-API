# tests/conftest.py
import os
import sys

# garante que a raiz do projeto está no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# importa a app e o Base
from app.api.main import app
from app.db.base import Base

# IMPORTE OS MODELOS ANTES DE create_all, para registrar as tabelas no Base.metadata
import app.db.models as models  # noqa: F401

# módulos onde vamos monkeypatchar
from app.db import session as session_mod
from app.services import data_service as data_service_mod
from app.adapters import market_data as market_mod


@pytest.fixture(scope="session")
def test_engine():
    """
    Engine SQLite que compartilha a MESMA base em memória entre conexões/threads.
    Isso é essencial para o TestClient.
    """
    engine = create_engine(
        "sqlite://",                               # compartilhar em memória
        connect_args={"check_same_thread": False}, # permitir entre threads
        poolclass=StaticPool,                      # uma única conexão para todos
        future=True,
    )
    # criar todas as tabelas (já que importamos app.db.models acima)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _override_db_dependency(monkeypatch, TestSessionLocal, test_engine):
    """
    Sobrescreve:
      - get_session_local() para usar o SessionLocal de teste (SQLite)
      - get_engine() para retornar o engine de teste (cobre casos como /health)
    E também substitui a referência DENTRO de app.services.data_service.
    """
    def _get_session_local():
        return TestSessionLocal

    def _get_engine():
        return test_engine

    # no módulo raiz de sessão
    monkeypatch.setattr(session_mod, "get_session_local", _get_session_local)
    monkeypatch.setattr(session_mod, "get_engine", _get_engine)

    # IMPORTANTE: no data_service foi feito "from app.db.session import get_session_local"
    # então precisamos monkeypatchar lá também:
    monkeypatch.setattr(data_service_mod, "get_session_local", _get_session_local)


@pytest.fixture(autouse=True)
def _mock_market_data(monkeypatch):
    """
    Mock do yfinance: retorna um pequeno OHLCV consistente para não depender de internet.
    """
    def fake_fetch_ohlcv_yf(ticker: str, start: str, end: str) -> pd.DataFrame:
        data = {
            "date": pd.to_datetime(
                ["2022-01-03", "2022-01-04", "2022-01-05", "2022-01-06", "2022-01-07"]
            ),
            "open":   [28.54, 29.16, 29.19, 28.53, 28.90],
            "high":   [29.22, 29.40, 29.27, 29.10, 29.35],
            "low":    [28.53, 28.91, 27.94, 28.05, 28.70],
            "close":  [29.09, 29.20, 28.07, 28.90, 29.10],
            "volume": [52704700, 51739200, 78459800, 60000000, 55000000],
        }
        return pd.DataFrame(data)

    monkeypatch.setattr(market_mod, "fetch_ohlcv_yf", fake_fetch_ohlcv_yf)


@pytest.fixture
def client():
    return TestClient(app)
