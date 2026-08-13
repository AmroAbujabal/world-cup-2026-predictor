# tests/test_scoring.py
"""The shared scorer treats penalty ties as draws for prediction points."""
import uuid
from datetime import datetime

import pytest

from backend.db.database import SessionLocal
from backend.db.models import Match, User, UserPrediction
from backend.services.scoring import score_match, outcome_from_scores


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()  # keep test fixtures out of dev.db
        session.close()


def test_outcome_from_scores():
    assert outcome_from_scores(2, 1) == "home_win"
    assert outcome_from_scores(0, 3) == "away_win"
    assert outcome_from_scores(1, 1) == "draw"


def test_penalty_tie_scores_as_draw(db):
    match = Match(
        home_team="Testland", away_team="Examplia",
        match_date=datetime(2026, 7, 3), tournament="Test Cup", is_locked=False,
    )
    db.add(match)
    db.flush()

    # one voter for each possible outcome
    picks = {}
    for outcome in ("home_win", "draw", "away_win"):
        u = User(username=f"pk_{outcome}_{uuid.uuid4().hex[:6]}")
        db.add(u)
        db.flush()
        db.add(UserPrediction(user_id=u.id, match_id=match.id, predicted_outcome=outcome))
        picks[outcome] = u
    db.flush()  # flush, not commit — the fixture rolls the whole thing back

    # 1–1 decided 4–2 on penalties → outcome is a DRAW
    actual, scored = score_match(db, match, 1, 1, penalty_home=4, penalty_away=2)
    db.flush()

    assert actual == "draw"
    assert scored == 3
    assert match.went_to_penalties is True
    assert match.status == "final"

    for outcome, user in picks.items():
        expected = 3 if outcome == "draw" else 0
        assert user.total_points == expected, f"{outcome} pick should earn {expected}"
