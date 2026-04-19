# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Match, User, UserPrediction
from backend.schemas import LeaderboardEntry, LeaderboardResponse, ResultRequest

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
        entries.append(LeaderboardEntry(
            rank=rank,
            username=user.username,
            total_points=user.total_points,
            correct_predictions=correct,
        ))
    return LeaderboardResponse(entries=entries)


@router.post("/results")
def score_results(request: ResultRequest, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.home_score = request.home_score
    match.away_score = request.away_score
    match.is_locked = True

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

    scored = 0
    for pred in unscored:
        points = 3 if pred.predicted_outcome == actual else 0
        pred.points_awarded = points
        user = db.query(User).filter(User.id == pred.user_id).first()
        if user:
            user.total_points += points
        scored += 1

    db.commit()
    return {"scored_predictions": scored, "actual_outcome": actual}
