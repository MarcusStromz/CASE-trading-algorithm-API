# Trading API — Case Dev Jr

API em FastAPI que:
- baixa cotações (yfinance) e salva em Postgres (`prices`, `symbols`)
- calcula indicadores (SMA/ATR) e salva em `indicators`
- executa backtests com Backtrader (SMA cross com sizing por risco/ATR)
- persiste resultados (`backtests`, `trades`, `daily_positions`, `metrics`)
- expõe endpoints REST

## Stack
- Python 3.11 • FastAPI • Uvicorn
- SQLAlchemy + Alembic
- Postgres
- Pandas • yfinance • Backtrader
- Docker / docker compose

## Subir o projeto

```bash
docker compose up -d --build
# serviços: trading_app (API em :8000) e trading_db (Postgres :5432)
