from .session import get_session_local
from .models import Symbol

def seed_symbols():
    SessionLocal = get_session_local()
    with SessionLocal() as db:
        base = [
            ("PETR4.SA", "Petrobras PN"),
            ("VALE3.SA", "Vale ON"),
            ("ITUB4.SA", "Itaú PN"),
        ]
        for t, n in base:
            if not db.query(Symbol).filter_by(ticker=t).first():
                db.add(Symbol(ticker=t, name=n))
        db.commit()

if __name__ == "__main__":
    seed_symbols()
