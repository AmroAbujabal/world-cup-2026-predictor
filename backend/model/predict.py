# backend/model/predict.py
from collections import defaultdict
from dataclasses import dataclass
import pandas as pd
from backend.model.features import load_data, build_features
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
        # Run feature pipeline once — reuse enriched df for ELO/form/H2H extraction
        X, y, enriched = build_features(df)
        del df  # free raw df immediately

        # Extract final ELO and form from last row each team appears in
        self._current_elo = self._extract_final_elo(enriched)
        self._current_form = self._extract_final_form(enriched)
        # Compact H2H dict: frozenset(team1,team2) -> list of result strings
        self._h2h = self._extract_h2h(enriched)
        del enriched  # free enriched df before training (biggest memory spike)

        self._model = train_model(X, y)
        del X, y

    def _extract_final_elo(self, enriched: pd.DataFrame) -> dict[str, float]:
        """Extract each team's latest ELO from the enriched dataframe."""
        elo: dict[str, float] = {}
        for _, row in enriched[['home_team', 'away_team', 'home_elo_before', 'away_elo_before']].iterrows():
            elo[row['home_team']] = row['home_elo_before']
            elo[row['away_team']] = row['away_elo_before']
        return elo

    def _extract_final_form(self, enriched: pd.DataFrame) -> dict[str, float]:
        """Extract each team's latest form from the enriched dataframe."""
        form: dict[str, float] = {}
        for _, row in enriched[['home_team', 'away_team', 'home_form', 'away_form']].iterrows():
            form[row['home_team']] = row['home_form']
            form[row['away_team']] = row['away_form']
        return form

    def _extract_h2h(self, enriched: pd.DataFrame) -> dict:
        """Build compact H2H dict from enriched dataframe."""
        records: dict = defaultdict(list)
        for _, row in enriched[['home_team', 'away_team', 'home_score', 'away_score']].iterrows():
            h, a = row['home_team'], row['away_team']
            key = frozenset([h, a])
            if row['home_score'] > row['away_score']:
                records[key].append(h)
            elif row['home_score'] < row['away_score']:
                records[key].append(a)
            else:
                records[key].append('draw')
        return dict(records)

    def _get_h2h(self, home_team: str, away_team: str) -> tuple[int, int, int]:
        """Get most recent H2H counts (home_wins, draws, away_wins)."""
        key = frozenset([home_team, away_team])
        past = self._h2h.get(key, [])[-10:]
        if not past:
            return 0, 0, 0
        hw = sum(1 for r in past if r == home_team)
        d = sum(1 for r in past if r == 'draw')
        aw = sum(1 for r in past if r == away_team)
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
