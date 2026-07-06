# backend/services/scoring.py
"""Single source of truth for posting a result and scoring user predictions.

Penalty ties are stored as their 1–1 (level) score, so the outcome is a DRAW for
prediction purposes; the penalty winner only advances the bracket. This keeps every
caller (admin route, /results, poller, seed scripts) consistent.
"""
from backend.db.models import User, UserPrediction

POINTS_CORRECT = 3


def outcome_from_scores(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


def score_match(
    db,
    match,
    home_score: int,
    away_score: int,
    *,
    penalty_home: int | None = None,
    penalty_away: int | None = None,
    went_to_extra_time: bool | None = None,
) -> tuple[str, int]:
    """Apply a final result to `match` and award points to its as-yet-unscored predictions.

    Does NOT commit — the caller owns the transaction. Returns (actual_outcome, num_scored).
    """
    match.home_score = home_score
    match.away_score = away_score
    match.is_locked = True
    match.status = "final"

    if penalty_home is not None and penalty_away is not None:
        match.went_to_penalties = True
        match.penalty_home = penalty_home
        match.penalty_away = penalty_away
    if went_to_extra_time is not None:
        match.went_to_extra_time = went_to_extra_time

    actual = outcome_from_scores(home_score, away_score)

    unscored = db.query(UserPrediction).filter(
        UserPrediction.match_id == match.id,
        UserPrediction.points_awarded.is_(None),
    ).all()
    for pred in unscored:
        pts = POINTS_CORRECT if pred.predicted_outcome == actual else 0
        pred.points_awarded = pts
        user = db.query(User).filter(User.id == pred.user_id).first()
        if user:
            user.total_points += pts

    return actual, len(unscored)
