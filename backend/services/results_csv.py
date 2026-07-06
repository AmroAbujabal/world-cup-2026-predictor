# backend/services/results_csv.py
"""Append finished knockout results to data/results.csv.

These rows feed ELO / recent-form / H2H the next time the model retrains. Names are
translated to the CSV's canonical spellings, and appends are deduped by
(date, home_team, away_team) so seeding / admin posts are safe to re-run.
"""
import csv
import os

DATA_PATH = "data/results.csv"

# DB / frontend spelling -> canonical spelling used throughout results.csv history
CSV_NAME_MAP = {
    "USA": "United States",
    "Curacao": "Curaçao",
}


def to_csv_name(name: str) -> str:
    return CSV_NAME_MAP.get(name, name)


def row_exists(date_str: str, home: str, away: str, path: str = DATA_PATH) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["date"] == date_str and row["home_team"] == home and row["away_team"] == away:
                return True
    return False


def append_result(
    date_str: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    tournament: str = "FIFA World Cup",
    city: str = "",
    country: str = "",
    neutral: bool = True,
    path: str = DATA_PATH,
) -> bool:
    """Append one match row (canonical names). Skips if the row already exists.

    Returns True if a row was written, False if it was a duplicate.
    """
    home = to_csv_name(home_team)
    away = to_csv_name(away_team)
    if row_exists(date_str, home, away, path):
        return False
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([
            date_str, home, away, int(home_score), int(away_score),
            tournament, city, country, "True" if neutral else "False",
        ])
    return True
