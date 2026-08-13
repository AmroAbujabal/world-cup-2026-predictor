# backend/main.py
import asyncio
import re
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from backend.db.database import engine, SessionLocal
from backend.db.models import Base


# ── DB setup & migrations ─────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)


def _migrate_db():
    """Add new columns to existing SQLite DBs without Alembic."""
    with engine.connect() as conn:
        for col, defn in [
            ("status",             "VARCHAR DEFAULT 'upcoming'"),
            ("external_id",        "INTEGER"),
            ("went_to_penalties",  "BOOLEAN"),
            ("penalty_home",       "INTEGER"),
            ("penalty_away",       "INTEGER"),
            ("went_to_extra_time", "BOOLEAN"),
            ("is_upset",           "BOOLEAN"),
            ("prob_home",          "REAL"),
            ("prob_draw",          "REAL"),
            ("prob_away",          "REAL"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE matches ADD COLUMN {col} {defn}"))
                conn.commit()
            except Exception:
                pass  # column already exists


_migrate_db()


# ── Seed knockout fixtures (runs only when matches table is empty) ─────────────

def _seed_matches():
    """
    Seed 31 WC 2026 knockout slots.
    R32 slots (1–16) are placeholders — run scripts/seed_wc2026.py to replace
    them with actual fixtures from football-data.org.
    """
    from datetime import datetime, timezone
    from backend.db.models import Match

    db = SessionLocal()
    try:
        if db.query(Match).count() > 0:
            return

        rows = []
        for i in range(1, 17):
            rows.append(Match(
                id=i,
                home_team="R32 TBD", away_team="R32 TBD",
                match_date=datetime(2026, 6, 29, tzinfo=timezone.utc),
                tournament="FIFA World Cup 2026",
            ))
        for start, n, label, month, day in [
            (17, 8, "R16",   7,  4),
            (25, 4, "QF",    7, 10),
            (29, 2, "SF",    7, 15),
            (31, 1, "Final", 7, 19),
        ]:
            for j in range(n):
                rows.append(Match(
                    id=start + j,
                    home_team=f"{label} TBD", away_team=f"{label} TBD",
                    match_date=datetime(2026, month, day, tzinfo=timezone.utc),
                    tournament="FIFA World Cup 2026",
                ))
        db.add_all(rows)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


_seed_matches()


def _ensure_third_place():
    """Add the third-place playoff (slot 32) to DBs seeded before it existed.

    Separate from _seed_matches() because that only runs on an empty table — every
    deployed DB already has slots 1–31. The sync fills in teams/date/result from
    football-data.org's THIRD_PLACE stage.
    """
    from datetime import datetime, timezone
    from backend.db.models import Match

    db = SessionLocal()
    try:
        if db.query(Match).filter(Match.id == 32).first():
            return
        db.add(Match(
            id=32,
            home_team="3rd Place TBD", away_team="3rd Place TBD",
            match_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            tournament="FIFA World Cup 2026",
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


_ensure_third_place()


# ── App ───────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background poller — only starts if an API key is set. Its tournament window
    # (Jun 28 – Jul 19 2026) has passed, so it exits immediately in practice.
    if os.getenv("FOOTBALL_DATA_API_KEY"):
        from backend.services.poller import poll_loop
        asyncio.create_task(poll_loop())
    yield


app = FastAPI(title="World Cup Predictor API", version="1.0.0", lifespan=lifespan)

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


@app.options("/{rest_of_path:path}")
async def preflight(rest_of_path: str, request: StarletteRequest):
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


# ── Routers ───────────────────────────────────────────────────────────────────

from backend.routes.predictions import router as predictions_router
from backend.routes.users import router as users_router
from backend.routes.admin import router as admin_router

app.include_router(predictions_router)
app.include_router(users_router)
app.include_router(admin_router)
