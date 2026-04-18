# backend/model/features.py
from collections import defaultdict
import numpy as np
import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    """Load and clean the international football results CSV."""
    df = pd.read_csv(path, parse_dates=['date'])
    df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce')
    df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce')
    df = df.dropna(subset=['home_score', 'away_score'])
    df['home_score'] = df['home_score'].astype(int)
    df['away_score'] = df['away_score'].astype(int)
    df = df.sort_values('date').reset_index(drop=True)
    return df


# K-factors by tournament importance
K_FACTORS = {
    'FIFA World Cup': 60,
    'UEFA Euro': 50,
    'Copa America': 50,
    'AFC Asian Cup': 45,
    'African Cup of Nations': 45,
    'Gold Cup': 40,
    'Friendly': 20,
}


def _get_k_factor(tournament: str) -> float:
    for key, k in K_FACTORS.items():
        if key in tournament:
            return k
    return 30  # qualifiers and other competitions


def compute_elo_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute each team's ELO rating at the time of each match (before the result).
    df must be sorted by date (ascending). Starting ELO: 1500 for all teams.
    Returns a new DataFrame with 'home_elo_before' and 'away_elo_before' columns.
    """
    elo: dict[str, float] = defaultdict(lambda: 1500.0)
    home_elos: list[float] = []
    away_elos: list[float] = []

    for _, row in df.iterrows():
        h, a = row['home_team'], row['away_team']
        h_elo, a_elo = elo[h], elo[a]

        home_elos.append(h_elo)
        away_elos.append(a_elo)

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

    result = df.copy()
    result['home_elo_before'] = home_elos
    result['away_elo_before'] = away_elos
    return result


def compute_recent_form(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    For each match, compute each team's average points per game over their
    last n matches (Win=3, Draw=1, Loss=0). Returns values in [0, 3].
    Teams with no prior history get 0.0.
    df must be sorted by date (ascending).
    """
    team_history: dict[str, list[float]] = defaultdict(list)
    home_forms: list[float] = []
    away_forms: list[float] = []

    for _, row in df.iterrows():
        h, a = row['home_team'], row['away_team']

        h_last = team_history[h][-n:]
        a_last = team_history[a][-n:]

        home_forms.append(sum(h_last) / len(h_last) if h_last else 0.0)
        away_forms.append(sum(a_last) / len(a_last) if a_last else 0.0)

        if row['home_score'] > row['away_score']:
            team_history[h].append(3.0)
            team_history[a].append(0.0)
        elif row['home_score'] < row['away_score']:
            team_history[h].append(0.0)
            team_history[a].append(3.0)
        else:
            team_history[h].append(1.0)
            team_history[a].append(1.0)

    result = df.copy()
    result['home_form'] = home_forms
    result['away_form'] = away_forms
    return result
