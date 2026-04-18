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
