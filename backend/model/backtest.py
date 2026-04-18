# backend/model/backtest.py
from dataclasses import dataclass, field
from typing import Any
import pandas as pd
from backend.model.features import load_data, build_features
from backend.model.train import train_model

LABEL_MAP = {0: 'home_win', 1: 'draw', 2: 'away_win'}


@dataclass
class BacktestResult:
    accuracy_2018: float
    accuracy_2022: float
    accuracy_combined: float
    predictions_2018: list[dict[str, Any]] = field(default_factory=list)
    predictions_2022: list[dict[str, Any]] = field(default_factory=list)


def _backtest_year(df_full: pd.DataFrame, year: int) -> tuple[float, list[dict[str, Any]]]:
    """
    Train on all data strictly before `year`, test on that year's World Cup matches.
    Returns (accuracy, list of per-match prediction dicts).
    """
    wc_mask = (
        (df_full['date'].dt.year == year) &
        (df_full['tournament'].str.contains('FIFA World Cup', na=False))
    )
    train_df = df_full[df_full['date'].dt.year < year].copy()
    test_df = df_full[wc_mask].copy()

    if len(test_df) == 0:
        raise ValueError(f"No FIFA World Cup matches found for {year}")

    X_train, y_train = build_features(train_df)
    X_test, y_test = build_features(test_df)

    model = train_model(X_train, y_train)
    preds = model.predict(X_test)
    proba = model.predict_proba(X_test)

    accuracy = float((preds == y_test.values).mean())

    predictions = []
    for i, (_, row) in enumerate(test_df.iterrows()):
        predictions.append({
            'date': str(row['date'].date()),
            'home_team': row['home_team'],
            'away_team': row['away_team'],
            'actual': LABEL_MAP[y_test.iloc[i]],
            'predicted': LABEL_MAP[int(preds[i])],
            'prob_home_win': round(float(proba[i, 0]), 3),
            'prob_draw': round(float(proba[i, 1]), 3),
            'prob_away_win': round(float(proba[i, 2]), 3),
            'correct': bool(preds[i] == y_test.iloc[i]),
        })

    return accuracy, predictions


def run_backtest(data_path: str) -> BacktestResult:
    """Backtest the model against 2018 and 2022 FIFA World Cup results."""
    df = load_data(data_path)
    acc_2018, preds_2018 = _backtest_year(df, 2018)
    acc_2022, preds_2022 = _backtest_year(df, 2022)

    total = len(preds_2018) + len(preds_2022)
    correct = sum(p['correct'] for p in preds_2018 + preds_2022)

    return BacktestResult(
        accuracy_2018=acc_2018,
        accuracy_2022=acc_2022,
        accuracy_combined=correct / total,
        predictions_2018=preds_2018,
        predictions_2022=preds_2022,
    )
