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


from backend.model.features import compute_h2h


def test_h2h_columns_added():
    df = load_data("data/results.csv")
    result = compute_h2h(df)
    assert 'h2h_home_wins' in result.columns
    assert 'h2h_draws' in result.columns
    assert 'h2h_away_wins' in result.columns


def test_h2h_first_encounter_is_zero():
    df = load_data("data/results.csv")
    result = compute_h2h(df)
    assert result['h2h_home_wins'].iloc[0] == 0
    assert result['h2h_draws'].iloc[0] == 0
    assert result['h2h_away_wins'].iloc[0] == 0


def test_h2h_counts_non_negative():
    df = load_data("data/results.csv")
    result = compute_h2h(df)
    assert (result['h2h_home_wins'] >= 0).all()
    assert (result['h2h_draws'] >= 0).all()
    assert (result['h2h_away_wins'] >= 0).all()


def test_h2h_does_not_mutate_input():
    df = load_data("data/results.csv")
    original_cols = list(df.columns)
    compute_h2h(df)
    assert list(df.columns) == original_cols


from backend.model.features import build_features

EXPECTED_FEATURE_COLS = [
    'elo_diff', 'home_elo_before', 'away_elo_before',
    'home_form', 'away_form',
    'h2h_home_wins', 'h2h_draws', 'h2h_away_wins',
    'is_neutral',
]


def test_build_features_returns_x_and_y():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    assert X.shape[0] == len(df)
    assert y.shape[0] == len(df)


def test_build_features_correct_columns():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    for col in EXPECTED_FEATURE_COLS:
        assert col in X.columns, f"Missing feature column: {col}"


def test_build_features_target_three_classes():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    assert set(y.unique()).issubset({0, 1, 2})


def test_build_features_no_nulls():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    assert not X.isnull().any().any(), "X contains null values"
    assert not y.isnull().any(), "y contains null values"
