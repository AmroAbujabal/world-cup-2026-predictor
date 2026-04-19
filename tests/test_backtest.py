# tests/test_backtest.py
import pytest
from backend.model.backtest import run_backtest, BacktestResult


def test_run_backtest_returns_result():
    result = run_backtest("data/results.csv")
    assert isinstance(result, BacktestResult)


def test_backtest_accuracy_fields_exist():
    result = run_backtest("data/results.csv")
    assert hasattr(result, 'accuracy_2018')
    assert hasattr(result, 'accuracy_2022')
    assert hasattr(result, 'accuracy_combined')


def test_backtest_accuracy_is_valid_proportion():
    result = run_backtest("data/results.csv")
    assert 0.0 <= result.accuracy_2018 <= 1.0
    assert 0.0 <= result.accuracy_2022 <= 1.0
    assert 0.0 <= result.accuracy_combined <= 1.0


def test_backtest_has_predictions():
    result = run_backtest("data/results.csv")
    assert len(result.predictions_2018) > 0
    assert len(result.predictions_2022) > 0


def test_backtest_prediction_has_required_keys():
    result = run_backtest("data/results.csv")
    pred = result.predictions_2018[0]
    required_keys = {'date', 'home_team', 'away_team', 'actual', 'predicted',
                     'prob_home_win', 'prob_draw', 'prob_away_win', 'correct'}
    assert required_keys.issubset(pred.keys())
