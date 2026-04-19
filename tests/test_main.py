# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_predict_returns_probabilities(client):
    resp = client.post("/predict", json={"home_team": "Brazil", "away_team": "Argentina", "neutral": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "prob_home_win" in data
    assert "prob_draw" in data
    assert "prob_away_win" in data
    total = data["prob_home_win"] + data["prob_draw"] + data["prob_away_win"]
    assert abs(total - 1.0) < 0.01


def test_predict_returns_correct_team_names(client):
    resp = client.post("/predict", json={"home_team": "France", "away_team": "Germany", "neutral": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["home_team"] == "France"
    assert data["away_team"] == "Germany"


def test_user_predict_invalid_outcome(client):
    resp = client.post("/user/predict", json={
        "username": "alice", "match_id": 999, "predicted_outcome": "invalid"
    })
    assert resp.status_code == 422


def test_user_predict_404_on_missing_match(client):
    resp = client.post("/user/predict", json={
        "username": "alice", "match_id": 99999, "predicted_outcome": "home_win"
    })
    assert resp.status_code == 404


def test_leaderboard_returns_entries_list(client):
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_score_results_updates_user_points(client):
    from backend.db.database import SessionLocal
    from backend.db.models import Match, User, UserPrediction
    from datetime import datetime
    import uuid

    db = SessionLocal()
    match = Match(
        home_team="Brazil", away_team="France",
        match_date=datetime(2026, 7, 1), tournament="Test Cup",
        is_locked=False,
    )
    db.add(match)
    user = User(username=f"scorer_test_{uuid.uuid4().hex[:8]}")
    db.add(user)
    db.flush()
    pred = UserPrediction(
        user_id=user.id, match_id=match.id, predicted_outcome="home_win",
    )
    db.add(pred)
    db.commit()
    match_id = match.id
    db.close()

    resp = client.post("/results", json={"match_id": match_id, "home_score": 2, "away_score": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scored_predictions"] == 1
    assert data["actual_outcome"] == "home_win"
