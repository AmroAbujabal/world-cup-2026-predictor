# backend/services/poller.py
"""Background polling task — fetches live WC results every 5 minutes."""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

POLL_INTERVAL = 300  # 5 minutes
TOURNAMENT_START = datetime(2026, 6, 28, tzinfo=timezone.utc)
TOURNAMENT_END = datetime(2026, 7, 20, tzinfo=timezone.utc)


async def poll_loop():
    """Entry point: launched as asyncio background task on app startup."""
    await asyncio.sleep(15)  # let server fully start first
    logger.info("Poller started — checking results every 5 minutes during tournament")
    while True:
        now = datetime.now(timezone.utc)
        if TOURNAMENT_START <= now <= TOURNAMENT_END:
            try:
                await _check_and_update()
            except Exception as exc:
                logger.warning("Poller error: %s", exc)
        await asyncio.sleep(POLL_INTERVAL)


async def _check_and_update():
    from backend.services.football_data import get_wc_matches, normalize
    from backend.db.database import SessionLocal
    from backend.db.models import Match, User, UserPrediction

    # Fetch all knockout matches (covers R32 through Final)
    raw_matches = await get_wc_matches()
    knockout_stages = {"LAST_32", "LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "FINAL"}
    knockout = [m for m in raw_matches if m.get("stage") in knockout_stages]

    if not knockout:
        return

    db = SessionLocal()
    try:
        for m in knockout:
            ext_id = m["id"]
            db_match = db.query(Match).filter(Match.external_id == ext_id).first()
            if not db_match:
                continue

            fd_status = m.get("status", "")
            if fd_status in ("IN_PLAY", "PAUSED", "HALFTIME"):
                new_status = "live"
            elif fd_status in ("FINISHED", "AWARDED"):
                new_status = "final"
            else:
                new_status = "upcoming"

            changed = db_match.status != new_status
            db_match.status = new_status

            if new_status == "final":
                score = m.get("score", {}).get("fullTime", {})
                hs, as_ = score.get("home"), score.get("away")
                if hs is not None and as_ is not None:
                    if db_match.home_score != hs or db_match.away_score != as_:
                        db_match.home_score = hs
                        db_match.away_score = as_
                        db_match.is_locked = True
                        changed = True
                        _score_predictions(db, db_match, hs, as_)

            if changed:
                db.commit()
                logger.info(
                    "Match %d (%s vs %s) → %s",
                    db_match.id, db_match.home_team, db_match.away_team, new_status,
                )
    finally:
        db.close()


def _score_predictions(db, match, home_score: int, away_score: int):
    from backend.db.models import User, UserPrediction
    actual = "home_win" if home_score > away_score else \
             "away_win" if home_score < away_score else "draw"
    unscored = db.query(UserPrediction).filter(
        UserPrediction.match_id == match.id,
        UserPrediction.points_awarded.is_(None),
    ).all()
    for pred in unscored:
        pts = 3 if pred.predicted_outcome == actual else 0
        pred.points_awarded = pts
        user = db.query(User).filter(User.id == pred.user_id).first()
        if user:
            user.total_points += pts
