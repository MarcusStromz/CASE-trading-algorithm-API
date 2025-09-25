# Trading API — Case Dev Jr

API em FastAPI que:
- baixa cotações (yfinance) e salva em Postgres (`prices`, `symbols`)
- calcula indicadores (SMA/ATR) e salva em `indicators`
- executa backtests com Backtrader (SMA cross com sizing por risco/ATR)
- persiste resultados (`backtests`, `trades`, `daily_positions`, `metrics`)
- expõe endpoints REST
- oferece notebooks para exploração de dados, análise de backtests e protótipo de modelo de ML (Random Forest)

## Stack
- Python 3.11 • FastAPI • Uvicorn  
- SQLAlchemy + Alembic  
- Postgres  
- Pandas • yfinance • Backtrader • scikit-learn  
- Matplotlib • Mplfinance • Seaborn  
- Docker / docker compose  

## Subir o projeto

```bash
git clone https://github.com/MarcusStromz/CASE-trading-algorithm-API.git
cd CASE-trading-algorithm-API

docker compose up -d --build

serviços: trading_app (API em :8000) e trading_db (Postgres :5432)
```
A API ficará disponível em:
 http://localhost:8000
 
## Tests/Scripts
```bash
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
pytest --cov=app --cov-report=term-missing -q
```
Script de verificação rápida (`scripts/smoke.ps1`), executa todo o fluxo da aplicação:
```bash
powershell -ExecutionPolicy Bypass -File .\scripts\smoke.ps1
```

## Endpoints principais

- GET /health — Status da API e conexão com DB
- POST /data/update — Atualiza cotações e indicadores
- POST /backtests/run — Executa um backtest
- GET /backtests/{id}/results — Retorna métricas e trades

## Notebooks

- **data_exploration.ipynb** (Prices & Indicators): visualização de candles com SMA(20/50) e ATR(14).
- **backtest_analysis.ipynb**: análise de métricas, trades e equity.
- **ML_model.ipynb**: protótipo de modelo de Machine Learning para prever a direção do próximo candle.

## Resultados do modelo (protótipo ML)

- Algoritmo: Random Forest Classifier
- Accuracy ≈ 0.58
- ROC-AUC ≈ 0.63
