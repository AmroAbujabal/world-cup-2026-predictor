# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Match, User, UserPrediction
from backend.schemas import LeaderboardEntry, LeaderboardResponse, ResultRequest
from backend.services.scoring import score_match, outcome_from_scores

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.total_points.desc()).limit(50).all()
    entries = []
    for rank, user in enumerate(users, start=1):
        correct = db.query(func.count(UserPrediction.id)).filter(
            UserPrediction.user_id == user.id,
            UserPrediction.points_awarded > 0,
        ).scalar() or 0
        total = db.query(func.count(UserPrediction.id)).filter(
            UserPrediction.user_id == user.id,
            UserPrediction.points_awarded.isnot(None),
        ).scalar() or 0
        entries.append(LeaderboardEntry(
            rank=rank,
            username=user.username,
            total_points=user.total_points,
            correct_predictions=correct,
            total_predictions=total,
        ))
    return LeaderboardResponse(entries=entries)


@router.post("/results")
def score_results(request: ResultRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    actual, scored = score_match(
        db, match, request.home_score, request.away_score,
        penalty_home=request.penalty_home,
        penalty_away=request.penalty_away,
        went_to_extra_time=request.went_to_extra_time,
    )
    db.commit()
    return {"scored_predictions": scored, "actual_outcome": actual}


@router.get("/user/{username}/predictions")
def user_predictions(username: str, db: Session = Depends(get_db)):
    """Every prediction a user made, with the actual result and points earned."""
    from backend.routes.predictions import _stage_label

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    preds = (
        db.query(UserPrediction, Match)
        .join(Match, UserPrediction.match_id == Match.id)
        .filter(UserPrediction.user_id == user.id)
        .order_by(Match.id)
        .all()
    )

    items = []
    for pred, match in preds:
        if match.home_score is not None and match.away_score is not None:
            actual = outcome_from_scores(match.home_score, match.away_score)
        else:
            actual = None
        items.append({
            "match_id": match.id,
            "stage": _stage_label(match.id),
            "home_team": match.home_team,
            "away_team": match.away_team,
            "status": match.status or "upcoming",
            "home_score": match.home_score,
            "away_score": match.away_score,
            "went_to_penalties": match.went_to_penalties,
            "penalty_home": match.penalty_home,
            "penalty_away": match.penalty_away,
            "predicted_outcome": pred.predicted_outcome,
            "actual_outcome": actual,
            "points_awarded": pred.points_awarded,
        })

    return {
        "username": user.username,
        "total_points": user.total_points,
        "predictions": items,
    }
