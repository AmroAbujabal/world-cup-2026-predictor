# backend/services/sync_service.py
"""Self-driving tournament sync.

Pulls every WC match from football-data.org and upserts the DB's 31 knockout slots
automatically — teams, kickoff, status, scores (penalty-aware), and live model
Win/Draw/Loss probabilities — then scores user predictions. No manual entry: as each
real result lands, one sync call brings the whole bracket current.
"""
from datetime import datetime

from backend.db.models import Match
from backend.services.football_data import normalize
from backend.services.scoring import score_match

# football-data.org stage -> our DB slot id range (ordering within a stage follows
# the match id, which tracks the official bracket structure)
STAGE_SLOTS = {
    "LAST_32": range(1, 17),
    "LAST_16": range(17, 25),
    "QUARTER_FINALS": range(25, 29),
    "SEMI_FINALS": range(29, 31),
    "FINAL": range(31, 32),
}


def _extract_result(score: dict):
    """(home, away, pen_home, pen_away, went_pens, went_et) for a finished match.

    Penalty ties are recorded at their level 120' score so they score as a DRAW;
    the shootout only decides who advances.
    """
    duration = score.get("duration")
    ft = score.get("fullTime", {}) or {}
    rt = score.get("regularTime", {}) or {}
    et = score.get("extraTime", {}) or {}
    pens = score.get("penalties", {}) or {}
    if duration == "PENALTY_SHOOTOUT":
        h = (rt.get("home") or 0) + (et.get("home") or 0)
        a = (rt.get("away") or 0) + (et.get("away") or 0)
        return h, a, pens.get("home"), pens.get("away"), True, True
    if duration == "EXTRA_TIME":
        return ft.get("home"), ft.get("away"), None, None, False, True
    return ft.get("home"), ft.get("away"), None, None, False, False


def _predict_probs(home: str, away: str):
    """Model 3-way probs (home, draw, away), or None if the model is unavailable."""
    try:
        from backend.routes.predictions import get_predictor
        p = get_predictor().predict(home, away, neutral=True)
        return (round(p.prob_home_win, 3), round(p.prob_draw, 3), round(p.prob_away_win, 3))
    except Exception:
        return None


def _is_real(name: str | None) -> bool:
    return bool(name) and "TBD" not in name


def sync_matches(db, matches: list[dict]) -> dict:
    """Upsert all knockout slots from a football-data.org match list. Commits once."""
    by_ext = {m.external_id: m for m in db.query(Match).all() if m.external_id}
    updated = scored = advanced = 0

    for stage, slot_range in STAGE_SLOTS.items():
        fixtures = sorted(
            (m for m in matches if m.get("stage") == stage),
            key=lambda m: m["id"],
        )
        for i, fd in enumerate(fixtures):
            ext = fd["id"]
            db_match = by_ext.get(ext)
            if db_match is None:
                if i >= len(slot_range):
                    continue
                db_match = db.query(Match).filter(Match.id == slot_range[i]).first()
            if db_match is None:
                continue

            home = normalize((fd.get("homeTeam") or {}).get("name") or "")
            away = normalize((fd.get("awayTeam") or {}).get("name") or "")
            if _is_real(home) and _is_real(away) and not _is_real(db_match.home_team):
                advanced += 1  # a TBD slot just got its real teams
            if _is_real(home):
                db_match.home_team = home
            if _is_real(away):
                db_match.away_team = away
            if fd.get("utcDate"):
                db_match.match_date = datetime.fromisoformat(fd["utcDate"].replace("Z", "+00:00"))
            db_match.external_id = ext

            fd_status = fd.get("status", "")
            if fd_status in ("FINISHED", "AWARDED"):
                h, a, ph, pa, pens, et = _extract_result(fd.get("score", {}))
                if h is not None and a is not None:
                    already = db_match.is_locked and db_match.home_score == h and db_match.away_score == a
                    if not already:
                        # win-probabilities as they stood pre-result → flag upsets automatically
                        probs = _predict_probs(db_match.home_team, db_match.away_team)
                        _, n = score_match(
                            db, db_match, h, a,
                            penalty_home=ph, penalty_away=pa, went_to_extra_time=et,
                        )
                        scored += n
                        if probs:
                            db_match.prob_home, db_match.prob_draw, db_match.prob_away = probs
                            winner_home = h > a or (pens and ph and ph > pa)
                            win_p = probs[0] if winner_home else probs[2]
                            lose_p = probs[2] if winner_home else probs[0]
                            db_match.is_upset = win_p < lose_p
                        updated += 1
            elif fd_status in ("IN_PLAY", "PAUSED", "HALFTIME"):
                if db_match.status != "live":
                    updated += 1
                db_match.status = "live"
            else:
                if not db_match.is_locked:
                    db_match.status = "upcoming"

    db.commit()

    refreshed = _refresh_upcoming_probs(db)
    return {"updated": updated, "scored": scored, "advanced": advanced, "probs_refreshed": refreshed}


def _refresh_upcoming_probs(db) -> int:
    """Store live model W/D/L probabilities on every not-yet-final knockout match."""
    n = 0
    upcoming = db.query(Match).filter(Match.status != "final").all()
    for m in upcoming:
        if not (_is_real(m.home_team) and _is_real(m.away_team)):
            continue
        probs = _predict_probs(m.home_team, m.away_team)
        if probs:
            m.prob_home, m.prob_draw, m.prob_away = probs
            n += 1
    if n:
        db.commit()
    return n


def run_sync() -> dict:
    """Open a session, pull all WC matches, sync, and return a summary."""
    from backend.db.database import SessionLocal
    from backend.services.football_data import sync_get_wc_matches

    matches = sync_get_wc_matches()
    db = SessionLocal()
    try:
        return sync_matches(db, matches)
    finally:
        db.close()
