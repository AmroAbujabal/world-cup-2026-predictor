# tests/test_sync.py
"""Sync must record a result it hasn't recorded yet, and never undo one it has."""
from datetime import datetime

import pytest

from backend.db.database import SessionLocal
from backend.db.models import Match
from backend.services import sync_service


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()  # keep test fixtures out of dev.db
        session.close()


@pytest.fixture(autouse=True)
def no_model(monkeypatch):
    """Skip the (slow) XGBoost train — this suite is about the sync bookkeeping."""
    monkeypatch.setattr(sync_service, "_predict_probs", lambda home, away: None)


def _fixture_match(db, **kw):
    m = Match(
        home_team="Testland", away_team="Examplia",
        match_date=datetime(2026, 7, 7), tournament="Test Cup",
        external_id=999_001, **kw,
    )
    db.add(m)
    db.flush()
    return m


def _payload(status, score):
    return [{
        "id": 999_001, "stage": "LAST_16", "status": status,
        "utcDate": "2026-07-07T20:00:00Z",
        "homeTeam": {"name": "Testland"}, "awayTeam": {"name": "Examplia"},
        "score": score,
    }]


def test_goalless_penalty_tie_is_recorded_over_a_live_00(db, monkeypatch):
    """Regression: a live 0–0 that ends 0–0 on penalties is still an unrecorded result."""
    monkeypatch.setattr(db, "commit", db.flush)  # don't persist the fixture
    match = _fixture_match(db, status="live", is_locked=True, home_score=0, away_score=0)

    sync_service.sync_matches(db, _payload("FINISHED", {
        "duration": "PENALTY_SHOOTOUT",
        "fullTime": {"home": 4, "away": 3},
        "regularTime": {"home": 0, "away": 0},
        "extraTime": {"home": 0, "away": 0},
        "penalties": {"home": 4, "away": 3},
    }))

    assert match.status == "final"
    assert (match.home_score, match.away_score) == (0, 0)
    assert match.went_to_penalties is True
    assert (match.penalty_home, match.penalty_away) == (4, 3)


def test_in_play_does_not_downgrade_a_final_match(db, monkeypatch):
    """A provider flipping FINISHED → IN_PLAY must not unmark a recorded result."""
    monkeypatch.setattr(db, "commit", db.flush)
    match = _fixture_match(db, status="final", is_locked=True, home_score=2, away_score=1)

    sync_service.sync_matches(db, _payload("IN_PLAY", {"fullTime": {"home": None, "away": None}}))

    assert match.status == "final"
    assert (match.home_score, match.away_score) == (2, 1)


def test_third_place_playoff_lands_in_slot_32(db, monkeypatch):
    """The THIRD_PLACE stage fills slot 32 — the real one is France 4–6 England."""
    monkeypatch.setattr(db, "commit", db.flush)
    slot = db.query(Match).filter(Match.id == 32).first()
    assert slot is not None, "slot 32 should be seeded by _ensure_third_place()"

    sync_service.sync_matches(db, [{
        "id": 537_389, "stage": "THIRD_PLACE", "status": "FINISHED",
        "utcDate": "2026-07-18T19:00:00Z",
        "homeTeam": {"name": "France"}, "awayTeam": {"name": "England"},
        "score": {"duration": "REGULAR", "fullTime": {"home": 4, "away": 6}},
    }])

    assert (slot.home_team, slot.away_team) == ("France", "England")
    assert (slot.home_score, slot.away_score) == (4, 6)
    assert slot.status == "final"
    assert slot.external_id == 537_389
