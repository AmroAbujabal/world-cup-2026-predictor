# backend/model/features.py
from collections import defaultdict
import numpy as np
import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    """Load and clean the international football results CSV."""
    df = pd.read_csv(
        path,
        parse_dates=['date'],
        dtype={'home_team': 'category', 'away_team': 'category', 'tournament': 'category'},
    )
    df['home_score'] = pd.to_numeric(df['home_score'], errors='coerce')
    df['away_score'] = pd.to_numeric(df['away_score'], errors='coerce')
    df = df.dropna(subset=['home_score', 'away_score'])
    df['home_score'] = df['home_score'].astype('int16')
    df['away_score'] = df['away_score'].astype('int16')
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


def compute_h2h(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    For each match, compute the H2H record between the two teams from
    their last n encounters. Counts wins/draws/losses from the current
    home team's perspective. df must be sorted by date (ascending).
    """
    # key: frozenset of (team1, team2) -> list of winner strings or 'draw'
    h2h_records: dict[frozenset, list[str]] = defaultdict(list)
    h2h_hw: list[int] = []
    h2h_d: list[int] = []
    h2h_aw: list[int] = []

    for _, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        key = frozenset([home_team, away_team])

        past = h2h_records[key][-n:]
        home_wins = sum(1 for r in past if r == home_team)
        draws = sum(1 for r in past if r == 'draw')
        away_wins = sum(1 for r in past if r == away_team)

        h2h_hw.append(home_wins)
        h2h_d.append(draws)
        h2h_aw.append(away_wins)

        if row['home_score'] > row['away_score']:
            h2h_records[key].append(home_team)
        elif row['home_score'] < row['away_score']:
            h2h_records[key].append(away_team)
        else:
            h2h_records[key].append('draw')

    result = df.copy()
    result['h2h_home_wins'] = h2h_hw
    result['h2h_draws'] = h2h_d
    result['h2h_away_wins'] = h2h_aw
    return result


FEATURE_COLS = [
    'elo_diff', 'home_elo_before', 'away_elo_before',
    'home_form', 'away_form',
    'h2h_home_wins', 'h2h_draws', 'h2h_away_wins',
    'is_neutral',
]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Apply all feature engineering steps and return (X, y, enriched_df).
    X: DataFrame with FEATURE_COLS columns.
    y: Series with values 0=home win, 1=draw, 2=away win.
    enriched_df: full dataframe with all feature columns (for ELO/form/H2H extraction).
    """
    df = compute_elo_ratings(df)
    df = compute_recent_form(df)
    df = compute_h2h(df)

    df['elo_diff'] = df['home_elo_before'] - df['away_elo_before']
    df['is_neutral'] = df['neutral'].astype('int8')

    X = df[FEATURE_COLS].copy()

    conditions = [
        df['home_score'] > df['away_score'],
        df['home_score'] == df['away_score'],
        df['home_score'] < df['away_score'],
    ]
    y = pd.Series(
        np.select(conditions, [0, 1, 2]),
        name='outcome',
        dtype='int8',
    )
    return X, y, df
