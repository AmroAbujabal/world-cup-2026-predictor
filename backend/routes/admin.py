# backend/routes/admin.py
"""Admin endpoints — protected by X-Admin-Token header."""

import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Match, User, UserPrediction
from backend.schemas import ResultRequest

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
    """Post a match result: scores predictions, updates leaderboard, marks match final."""
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.home_score = request.home_score
    match.away_score = request.away_score
    match.is_locked = True
    match.status = "final"

    if request.home_score > request.away_score:
        actual = "home_win"
    elif request.home_score < request.away_score:
        actual = "away_win"
    else:
        actual = "draw"

    unscored = db.query(UserPrediction).filter(
        UserPrediction.match_id == request.match_id,
        UserPrediction.points_awarded.is_(None),
    ).all()

    for pred in unscored:
        pts = 3 if pred.predicted_outcome == actual else 0
        pred.points_awarded = pts
        user = db.query(User).filter(User.id == pred.user_id).first()
        if user:
            user.total_points += pts

    db.commit()
    return {
        "match_id": request.match_id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "score": f"{request.home_score}–{request.away_score}",
        "actual_outcome": actual,
        "predictions_scored": len(unscored),
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
