# backend/model/features.py
from collections import defaultdict
import numpy as np
import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    """Load and clean the international football results CSV."""
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.dropna(subset=['home_score', 'away_score'])
    df['home_score'] = df['home_score'].astype(int)
    df['away_score'] = df['away_score'].astype(int)
    df = df.sort_values('date').reset_index(drop=True)
    return df
