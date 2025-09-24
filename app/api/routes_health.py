from fastapi import APIRouter
from sqlalchemy import text 
from app.db.session import get_engine

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  
        db_ok = True
    except Exception as e:
        print("Health check DB error:", e)  
        db_ok = False
    return {"status": "ok", "db": db_ok}
