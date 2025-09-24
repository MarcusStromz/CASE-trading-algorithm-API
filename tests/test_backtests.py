def test_run_backtest_and_results(client):

    upd = {
        "ticker": "PETR4.SA",
        "start": "2022-01-01",
        "end": "2022-12-31",
        "sma_fast": 3,
        "sma_slow": 5,
        "atr_window": 3
    }
    r1 = client.post("/data/update", json=upd)
    assert r1.status_code == 200

    body = {
        "ticker": "PETR4.SA",
        "start_date": "2022-01-01",
        "end_date": "2022-12-31",
        "initial_cash": 100000,
        "commission": 0.0005,
        "sma_fast": 3,
        "sma_slow": 5,
        "atr_window": 3,
        "atr_k": 2.0,
        "risk_perc": 0.01,
        "strategy_type": "sma_cross",
        "strategy_params": {}
    }
    r2 = client.post("/backtests/run", json=body)
    assert r2.status_code == 200
    j2 = r2.json()
    assert "backtest_id" in j2
    assert "metrics" in j2
    bt_id = j2["backtest_id"]
    assert bt_id > 0

    r3 = client.get(f"/backtests/{bt_id}/results")
    assert r3.status_code == 200
    j3 = r3.json()
    assert j3["backtest_id"] == bt_id

    assert "trades" in j3
    assert "daily_positions" in j3
    assert "metrics" in j3
