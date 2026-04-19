# backend/model/predict.py
from collections import defaultdict
from dataclasses import dataclass
import pandas as pd
from backend.model.features import (
    load_data, compute_elo_ratings, compute_recent_form, compute_h2h,
    build_features, FEATURE_COLS, _get_k_factor,
)
from backend.model.train import train_model


@dataclass
class MatchPrediction:
    home_team: str
    away_team: str
    prob_home_win: float
    prob_draw: float
    prob_away_win: float


class PredictorService:
    """Trains on full historical data and exposes predict() for arbitrary matches."""

    def __init__(self, data_path: str):
        df = load_data(data_path)
        X, y = build_features(df)
        self._model = train_model(X, y)
        self._current_elo = self._compute_final_elo(df)
        self._current_form = self._compute_final_form(df)
        self._df_enriched = compute_h2h(compute_recent_form(compute_elo_ratings(df)))

    def _compute_final_elo(self, df: pd.DataFrame) -> dict[str, float]:
        """Return each team's ELO after processing the entire dataset."""
        elo: dict[str, float] = defaultdict(lambda: 1500.0)
        for _, row in df.iterrows():
            h, a = row['home_team'], row['away_team']
            h_elo, a_elo = elo[h], elo[a]
            k = _get_k_factor(row['tournament'])
            home_expected = 1.0 / (1.0 + 10.0 ** ((a_elo - h_elo) / 400.0))
            if row['home_score'] > row['away_score']:
                home_actual = 1.0
            elif row['home_score'] < row['away_score']:
                home_actual = 0.0
            else:
                home_actual = 0.5
            elo[h] = h_elo + k * (home_actual - home_expected)
            elo[a] = a_elo + k * ((1.0 - home_actual) - (1.0 - home_expected))
        return dict(elo)

    def _compute_final_form(self, df: pd.DataFrame, n: int = 5) -> dict[str, float]:
        """Return each team's form (avg pts/game over last n matches) at end of dataset."""
        history: dict[str, list[float]] = defaultdict(list)
        for _, row in df.iterrows():
            h, a = row['home_team'], row['away_team']
            if row['home_score'] > row['away_score']:
                history[h].append(3.0); history[a].append(0.0)
            elif row['home_score'] < row['away_score']:
                history[h].append(0.0); history[a].append(3.0)
            else:
                history[h].append(1.0); history[a].append(1.0)
        return {
            team: sum(pts[-n:]) / len(pts[-n:]) if pts else 0.0
            for team, pts in history.items()
        }

    def _get_h2h(self, home_team: str, away_team: str) -> tuple[int, int, int]:
        """Get most recent H2H counts (home_wins, draws, away_wins) from dataset."""
        mask = (
            ((self._df_enriched['home_team'] == home_team) &
             (self._df_enriched['away_team'] == away_team)) |
            ((self._df_enriched['home_team'] == away_team) &
             (self._df_enriched['away_team'] == home_team))
        )
        recent = self._df_enriched[mask].tail(10)
        if recent.empty:
            return 0, 0, 0
        hw = int(((recent['home_team'] == home_team) & (recent['home_score'] > recent['away_score'])).sum() +
                 ((recent['away_team'] == home_team) & (recent['away_score'] > recent['home_score'])).sum())
        d = int((recent['home_score'] == recent['away_score']).sum())
        aw = int(((recent['home_team'] == away_team) & (recent['home_score'] > recent['away_score'])).sum() +
                 ((recent['away_team'] == away_team) & (recent['away_score'] > recent['home_score'])).sum())
        return hw, d, aw

    def predict(self, home_team: str, away_team: str, neutral: bool = True) -> MatchPrediction:
        h_elo = self._current_elo.get(home_team, 1500.0)
        a_elo = self._current_elo.get(away_team, 1500.0)
        h_form = self._current_form.get(home_team, 0.0)
        a_form = self._current_form.get(away_team, 0.0)
        h2h_hw, h2h_d, h2h_aw = self._get_h2h(home_team, away_team)

        X = pd.DataFrame([{
            'elo_diff': h_elo - a_elo,
            'home_elo_before': h_elo,
            'away_elo_before': a_elo,
            'home_form': h_form,
            'away_form': a_form,
            'h2h_home_wins': h2h_hw,
            'h2h_draws': h2h_d,
            'h2h_away_wins': h2h_aw,
            'is_neutral': int(neutral),
        }])

        proba = self._model.predict_proba(X)[0]
        return MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            prob_home_win=round(float(proba[0]), 3),
            prob_draw=round(float(proba[1]), 3),
            prob_away_win=round(float(proba[2]), 3),
        )
