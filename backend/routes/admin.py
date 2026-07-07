# backend/routes/admin.py
"""Admin endpoints — protected by X-Admin-Token header."""

import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Match
from backend.schemas import ResultRequest
from backend.services.scoring import score_match
from backend.services import results_csv

router = APIRouter(prefix="/admin")


def _verify_token(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    expected = os.getenv("ADMIN_TOKEN", "changeme")
    if x_admin_token != expected:
        raise HTTPException(status_code=403, detail="Invalid admin token")


@router.post("/update-result")
def update_result(
    request: ResultRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_token),
):
    """Atomic result flow: save score → recalc ELO/form source → score predictions → leaderboard.

    Marks the match final, awards points via the shared scorer, appends the result to
    data/results.csv (so ELO/form update on the next retrain), and clears the model cache.
    """
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    actual, scored = score_match(
        db, match, request.home_score, request.away_score,
        penalty_home=request.penalty_home,
        penalty_away=request.penalty_away,
        went_to_extra_time=request.went_to_extra_time,
    )

    # ELO/form feed: append this result to the training CSV (deduped, canonical names).
    # Penalty ties count as draws for ELO — store the level score.
    csv_home, csv_away = request.home_score, request.away_score
    if match.went_to_penalties:
        csv_home = csv_away = min(request.home_score, request.away_score)
    results_csv.append_result(
        match.match_date.date().isoformat(),
        match.home_team, match.away_team, csv_home, csv_away,
    )

    db.commit()

    # Retrain on next /predict so the new result influences ELO/form.
    from backend.routes.predictions import get_predictor
    get_predictor.cache_clear()

    return {
        "match_id": request.match_id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "score": f"{request.home_score}–{request.away_score}",
        "actual_outcome": actual,
        "predictions_scored": scored,
    }


@router.post("/set-live")
def set_live(
    body: dict,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_token),
):
    """Mark a match as live (in-play)."""
    match_id = body.get("match_id")
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    match.status = "live"
    db.commit()
    return {"match_id": match_id, "status": "live"}


@router.post("/retrain")
def retrain(_: None = Depends(_verify_token)):
    """Clear XGBoost model cache so it retrains on next prediction request."""
    from backend.routes.predictions import get_predictor
    get_predictor.cache_clear()
    return {"status": "cache cleared — model retrains on next /predict call"}


@router.post("/sync")
def sync(_: None = Depends(_verify_token)):
    """Pull live results from football-data.org and bring the whole bracket current."""
    from backend.services.sync_service import run_sync
    return run_sync()
