from fastapi import APIRouter
from app.schemas.data import UpdateDataRequest, UpdateDataResponse
from app.services.data_service import update_prices_and_indicators

router = APIRouter(prefix="/data", tags=["data"])

@router.post("/update", response_model=UpdateDataResponse)
def update_data(body: UpdateDataRequest):
    res = update_prices_and_indicators(
        ticker=body.ticker,
        start=str(body.start),
        end=str(body.end),
        sma_windows=(body.sma_fast, body.sma_slow),
        atr_window=body.atr_window
    )
    return UpdateDataResponse(**res)
