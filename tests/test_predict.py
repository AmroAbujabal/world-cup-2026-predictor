# tests/test_predict.py
import pytest
from backend.model.predict import PredictorService, MatchPrediction


@pytest.fixture(scope="module")
def svc():
    return PredictorService("data/results.csv")


def test_predict_returns_match_prediction(svc):
    result = svc.predict("Brazil", "Argentina")
    assert isinstance(result, MatchPrediction)


def test_predict_probabilities_sum_to_one(svc):
    result = svc.predict("Brazil", "Argentina")
    total = result.prob_home_win + result.prob_draw + result.prob_away_win
    assert abs(total - 1.0) < 0.01


def test_predict_team_names_preserved(svc):
    result = svc.predict("France", "Germany")
    assert result.home_team == "France"
    assert result.away_team == "Germany"


def test_predict_unknown_teams_still_works(svc):
    """Unknown teams fall back to default ELO 1500; should still return valid probabilities."""
    result = svc.predict("FakeTeamA", "FakeTeamB")
    total = result.prob_home_win + result.prob_draw + result.prob_away_win
    assert abs(total - 1.0) < 0.01
