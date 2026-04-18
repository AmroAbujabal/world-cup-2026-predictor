# tests/test_features.py
import pandas as pd
import pytest
from backend.model.features import load_data


def test_load_data_returns_dataframe():
    df = load_data("data/results.csv")
    assert isinstance(df, pd.DataFrame)


def test_load_data_has_required_columns():
    df = load_data("data/results.csv")
    required = {'date', 'home_team', 'away_team', 'home_score', 'away_score', 'tournament', 'neutral'}
    assert required.issubset(df.columns)


def test_load_data_date_is_datetime():
    df = load_data("data/results.csv")
    assert pd.api.types.is_datetime64_any_dtype(df['date'])


def test_load_data_sorted_by_date():
    df = load_data("data/results.csv")
    assert df['date'].is_monotonic_increasing


def test_load_data_no_null_scores():
    df = load_data("data/results.csv")
    assert df['home_score'].notna().all()
    assert df['away_score'].notna().all()


from backend.model.features import compute_elo_ratings


def test_elo_columns_added():
    df = load_data("data/results.csv")
    result = compute_elo_ratings(df)
    assert 'home_elo_before' in result.columns
    assert 'away_elo_before' in result.columns


def test_elo_initial_rating_is_1500():
    """First match ever — both teams start at 1500."""
    df = load_data("data/results.csv")
    result = compute_elo_ratings(df)
    assert result['home_elo_before'].iloc[0] == pytest.approx(1500.0)
    assert result['away_elo_before'].iloc[0] == pytest.approx(1500.0)


def test_elo_ratings_in_plausible_range():
    df = load_data("data/results.csv")
    result = compute_elo_ratings(df)
    assert result['home_elo_before'].between(900, 2500).all()
    assert result['away_elo_before'].between(900, 2500).all()


def test_elo_does_not_mutate_input():
    df = load_data("data/results.csv")
    original_cols = list(df.columns)
    compute_elo_ratings(df)
    assert list(df.columns) == original_cols


from backend.model.features import compute_recent_form


def test_recent_form_columns_added():
    df = load_data("data/results.csv")
    result = compute_recent_form(df)
    assert 'home_form' in result.columns
    assert 'away_form' in result.columns


def test_recent_form_first_match_is_zero():
    """Teams with no match history yet should have form 0."""
    df = load_data("data/results.csv")
    result = compute_recent_form(df)
    assert result['home_form'].iloc[0] == pytest.approx(0.0)
    assert result['away_form'].iloc[0] == pytest.approx(0.0)


def test_recent_form_in_range():
    """Average points per game is in [0, 3]."""
    df = load_data("data/results.csv")
    result = compute_recent_form(df)
    assert result['home_form'].between(0.0, 3.0).all()
    assert result['away_form'].between(0.0, 3.0).all()


def test_recent_form_does_not_mutate_input():
    df = load_data("data/results.csv")
    original_cols = list(df.columns)
    compute_recent_form(df)
    assert list(df.columns) == original_cols
