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
