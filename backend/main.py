# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine
from backend.db.models import Base

Base.metadata.create_all(bind=engine)

# ── Seed WC 2026 knockout matches once ───────────────────────────────────────
def _seed_matches():
    from backend.db.database import SessionLocal
    from backend.db.models import Match
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        if db.query(Match).count() > 0:
            return
        R32 = [
            ("Mexico", "Canada"), ("Switzerland", "South Korea"),
            ("Brazil", "Turkey"), ("United States", "Morocco"),
            ("Germany", "Japan"), ("Netherlands", "Ecuador"),
            ("Belgium", "Uruguay"), ("Spain", "Egypt"),
            ("France", "Austria"), ("Argentina", "Senegal"),
            ("Portugal", "Croatia"), ("England", "Colombia"),
            ("South Africa", "Bosnia and Herzegovina"), ("Scotland", "Paraguay"),
            ("Ivory Coast", "Sweden"), ("Iran", "Norway"),
        ]
        rows = []
        for i, (home, away) in enumerate(R32, start=1):
            rows.append(Match(id=i, home_team=home, away_team=away,
                              match_date=datetime(2026, 6, 20, tzinfo=timezone.utc),
                              tournament="FIFA World Cup 2026"))
        for start, n, label, month, day in [
            (17, 8, "R16",   6, 28),
            (25, 4, "QF",    7,  4),
            (29, 2, "SF",    7, 10),
            (31, 1, "Final", 7, 19),
        ]:
            for j in range(n):
                rows.append(Match(id=start + j,
                                  home_team=f"{label} TBD", away_team=f"{label} TBD",
                                  match_date=datetime(2026, month, day, tzinfo=timezone.utc),
                                  tournament="FIFA World Cup 2026"))
        db.add_all(rows)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

_seed_matches()

app = FastAPI(title="World Cup Predictor API", version="1.0.0")

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

ALLOWED_ORIGINS = re.compile(
    r"^(http://localhost:\d+|https://[\w-]+-amrabujabal35-2594s-projects\.vercel\.app|https://frontend-nine-alpha-56\.vercel\.app)$"
)

class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin", "")
        response = await call_next(request)
        if ALLOWED_ORIGINS.match(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(DynamicCORSMiddleware)

# Preflight handler
@app.options("/{rest_of_path:path}")
async def preflight(rest_of_path: str, request: StarletteRequest):
    from fastapi import Response
    origin = request.headers.get("origin", "")
    headers = {}
    if ALLOWED_ORIGINS.match(origin):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    return Response(status_code=204, headers=headers)


@app.get("/health")
def health():
    return {"status": "ok"}


from backend.routes.predictions import router as predictions_router
app.include_router(predictions_router)

from backend.routes.users import router as users_router
app.include_router(users_router)
