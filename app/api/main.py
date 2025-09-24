from fastapi import FastAPI
from app.api.routes_health import router as health_router
from app.api.routes_data import router as data_router
from app.api.routes_backtests import router as bt_router

app = FastAPI(title="Trading API", version="0.2.0")

app.include_router(health_router)
app.include_router(data_router)
app.include_router(bt_router)

@app.get("/")
async def root():
    return {"message": "Trading API up"}
