$ErrorActionPreference = "Stop"

Write-Host "==> Health check" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json

Write-Host "==> Atualizando dados/indicadores" -ForegroundColor Cyan
$upd = @{
  ticker="PETR4.SA"
  start="2022-01-01"
  end="2025-09-01"
  sma_fast=20
  sma_slow=50
  atr_window=14
} | ConvertTo-Json
$updResp = Invoke-RestMethod -Uri "http://localhost:8000/data/update" -Method Post -ContentType "application/json" -Body $upd
$updResp | ConvertTo-Json

Write-Host "==> Rodando backtest (SMA cross)" -ForegroundColor Cyan
$body = @{
  ticker="PETR4.SA"
  start_date="2022-01-01"
  end_date="2025-09-01"
  initial_cash=100000
  commission=0.0005
  sma_fast=20
  sma_slow=50
  atr_window=14
  atr_k=2.0
  risk_perc=0.01
  strategy_type="sma_cross"
} | ConvertTo-Json
$bt = Invoke-RestMethod -Uri "http://localhost:8000/backtests/run" -Method Post -ContentType "application/json" -Body $body
$bt | ConvertTo-Json
$btid = $bt.backtest_id

Write-Host "==> Buscando resultados (id=$btid)" -ForegroundColor Cyan
$results = Invoke-RestMethod -Uri "http://localhost:8000/backtests/$btid/results"
$results.metrics | ConvertTo-Json
"trades: $($results.trades.Count) | daily_points: $($results.daily_positions.Count)" | Write-Host -ForegroundColor Green
