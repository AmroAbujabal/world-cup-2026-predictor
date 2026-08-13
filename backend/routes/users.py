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


@router.get("/model-performance")
def model_performance(db: Session = Depends(get_db)):
    """How the model actually did: its stored pre-kickoff probabilities vs the real results.

    Every finished knockout match carries the Win/Draw/Loss probabilities the model held
    before the result landed (written by the sync), so this is a straight scorecard —
    the model's most likely outcome against what happened.
    """
    from backend.routes.predictions import _stage_label

    matches = (
        db.query(Match)
        # Slots 1–31 only: the scorecard is scoped to the bracket users played, so the
        # third-place playoff (slot 32, nobody predicted it) stays out of the denominator.
        .filter(Match.id <= 31, Match.status == "final", Match.prob_home.isnot(None))
        .order_by(Match.id)
        .all()
    )

    stages: dict[str, dict] = {}
    misses = []
    correct = brier_total = 0

    for m in matches:
        probs = {"home_win": m.prob_home, "draw": m.prob_draw, "away_win": m.prob_away}
        predicted = max(probs, key=probs.get)
        actual = outcome_from_scores(m.home_score, m.away_score)
        hit = predicted == actual
        correct += hit
        # multi-class Brier score: 0 = perfect, 2 = maximally wrong
        brier_total += sum((p - (k == actual)) ** 2 for k, p in probs.items())

        stage = _stage_label(m.id)
        tally = stages.setdefault(stage, {"stage": stage, "correct": 0, "total": 0})
        tally["total"] += 1
        tally["correct"] += hit

        if not hit:
            misses.append({
                "match_id": m.id,
                "stage": stage,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "score": f"{m.home_score}–{m.away_score}",
                "went_to_penalties": bool(m.went_to_penalties),
                "predicted_outcome": predicted,
                "actual_outcome": actual,
                "confidence": round(probs[predicted], 3),
            })

    total = len(matches)
    return {
        "matches_scored": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else None,
        "brier_score": round(brier_total / total, 4) if total else None,
        "random_baseline": round(1 / 3, 4),
        "by_stage": list(stages.values()),
        "misses": misses,
        "champion": _champion(db),
    }


def _champion(db) -> dict | None:
    """Who won the final (match 31), and whether the model's top pick was that team.

    Not the same as "match 31 wasn't a miss": a final decided on penalties is stored as
    a draw, so the model can score the outcome right while naming the wrong champion.
    """
    final = db.query(Match).filter(Match.id == 31, Match.status == "final").first()
    if not final or final.home_score is None:
        return None
    home_won = final.home_score > final.away_score or (
        final.went_to_penalties and (final.penalty_home or 0) > (final.penalty_away or 0)
    )
    probs = {"home_win": final.prob_home, "draw": final.prob_draw, "away_win": final.prob_away}
    has_probs = all(p is not None for p in probs.values())
    return {
        "team": final.home_team if home_won else final.away_team,
        "runner_up": final.away_team if home_won else final.home_team,
        "score": f"{final.home_score}–{final.away_score}",
        "went_to_penalties": bool(final.went_to_penalties),
        "model_probability": final.prob_home if home_won else final.prob_away,
        "model_called_it": has_probs
        and max(probs, key=probs.get) == ("home_win" if home_won else "away_win"),
    }


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
