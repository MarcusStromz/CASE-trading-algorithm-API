def test_data_update_minimal(client):
    body = {
        "ticker": "PETR4.SA",
        "start": "2022-01-01",
        "end": "2022-12-31",
        "sma_fast": 3,
        "sma_slow": 5,
        "atr_window": 3
    }
    r = client.post("/data/update", json=body)
    assert r.status_code == 200
    j = r.json()
    
    assert j["inserted_prices"] > 0
    assert j["inserted_indicators"] > 0
    assert j["symbol_id"] >= 1
