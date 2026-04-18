# World Cup Match Outcome Predictor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app that predicts Win/Draw/Loss probabilities for international football matches using historical FIFA data, with user prediction tracking and a leaderboard.

**Architecture:** ML pipeline (XGBoost trained on ELO + form + H2H features from results.csv) → FastAPI backend with PostgreSQL for user/match state → React frontend. Three subsystems executed sequentially; each is independently testable.

**Tech Stack:** Python 3.11, pandas, scikit-learn, XGBoost, joblib, FastAPI, SQLAlchemy, PostgreSQL, React 18, Vite, Tailwind CSS, React Router

---

## File Map

```
world-cup-predictor/
├── data/results.csv                     # Kaggle dataset (pre-existing)
├── requirements.txt
├── .env.example
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app, CORS, router registration
│   ├── schemas.py                       # Pydantic request/response models
│   ├── model/
│   │   ├── __init__.py
│   │   ├── features.py                  # load_data, ELO, form, H2H, build_features
│   │   ├── train.py                     # train_model, save_model, load_model
│   │   ├── predict.py                   # PredictorService (loads model, predicts)
│   │   └── backtest.py                  # run_backtest on 2018/2022 WC
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── predictions.py               # POST /predict, POST /user/predict
│   │   └── users.py                     # GET /leaderboard, POST /results
│   └── db/
│       ├── __init__.py
│       ├── database.py                  # SQLAlchemy engine, SessionLocal, get_db
│       └── models.py                    # Match, User, UserPrediction ORM models
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx                      # BrowserRouter, nav, routes
        ├── api/
        │   └── client.js               # axios instance + API functions
        ├── components/
        │   ├── ProbabilityBar.jsx       # Animated progress bar for probabilities
        │   └── TeamSelector.jsx         # Dropdown for team selection
        └── pages/
            ├── MatchPredictor.jsx       # Match selector + AI output + user pick form
            └── Leaderboard.jsx          # Rankings table
```

---

## Subsystem 1: ML Pipeline

### Task 0: Project Scaffold

**Files:**
- Create: `world-cup-predictor/` directory tree
- Create: `requirements.txt`
- Create: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p world-cup-predictor/{backend/{model,routes,db},data,tests,docs/superpowers/plans}
touch world-cup-predictor/backend/__init__.py
touch world-cup-predictor/backend/model/__init__.py
touch world-cup-predictor/backend/routes/__init__.py
touch world-cup-predictor/backend/db/__init__.py
touch world-cup-predictor/tests/__init__.py
```

- [ ] **Step 2: Create `requirements.txt`**

```
# world-cup-predictor/requirements.txt
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.0
xgboost==2.0.3
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
python-dotenv==1.0.1
pydantic==2.7.1
pytest==8.2.2
httpx==0.27.0
joblib==1.4.2
```

- [ ] **Step 3: Install dependencies**

```bash
cd world-cup-predictor && pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 4: Copy dataset and verify**

Place the Kaggle CSV at `world-cup-predictor/data/results.csv`, then:

```bash
head -3 data/results.csv
```

Expected header row: `date,home_team,away_team,home_score,away_score,tournament,city,country,neutral`

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
backend/model/trained_model.pkl
.pytest_cache/
frontend/node_modules/
frontend/dist/
dev.db
```

- [ ] **Step 6: Initialize git**

```bash
cd world-cup-predictor && git init
git add requirements.txt .gitignore
git commit -m "chore: project scaffold"
```

---

### Task 1: Data Loading

**Files:**
- Create: `backend/model/features.py`
- Create: `tests/test_features.py`

- [ ] **Step 1: Write failing tests for data loading**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd world-cup-predictor && pytest tests/test_features.py -v
```

Expected: `ImportError` — `features.py` doesn't exist yet.

- [ ] **Step 3: Implement `load_data`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_features.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/features.py tests/test_features.py
git commit -m "feat: data loading with column and dtype validation"
```

---

### Task 2: ELO Rating Feature Engineering

**Files:**
- Modify: `backend/model/features.py`
- Modify: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_features.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_features.py -k "elo" -v
```

Expected: `ImportError: cannot import name 'compute_elo_ratings'`

- [ ] **Step 3: Implement `compute_elo_ratings`**

Append to `backend/model/features.py` (after `load_data`):

```python
# K-factors by tournament importance
K_FACTORS = {
    'FIFA World Cup': 60,
    'UEFA Euro': 50,
    'Copa America': 50,
    'AFC Asian Cup': 45,
    'Africa Cup of Nations': 45,
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_features.py -k "elo" -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/features.py tests/test_features.py
git commit -m "feat: ELO rating computation with tournament-weighted K-factors"
```

---

### Task 3: Recent Form Feature

**Files:**
- Modify: `backend/model/features.py`
- Modify: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_features.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_features.py -k "form" -v
```

Expected: `ImportError: cannot import name 'compute_recent_form'`

- [ ] **Step 3: Implement `compute_recent_form`**

Append to `backend/model/features.py`:

```python
def compute_recent_form(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    For each match, compute each team's average points per game over their
    last n matches (Win=3, Draw=1, Loss=0). Returns values in [0, 3].
    Teams with no prior history get 0.0.
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_features.py -k "form" -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/features.py tests/test_features.py
git commit -m "feat: recent form feature (avg points/game over last 5 matches)"
```

---

### Task 4: Head-to-Head Feature

**Files:**
- Modify: `backend/model/features.py`
- Modify: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_features.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_features.py -k "h2h" -v
```

Expected: `ImportError: cannot import name 'compute_h2h'`

- [ ] **Step 3: Implement `compute_h2h`**

Append to `backend/model/features.py`:

```python
def compute_h2h(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    For each match, compute the H2H record between the two teams from
    their last n encounters. Counts wins/draws/losses from the home team's
    perspective in the CURRENT match (not the perspective of the historic match).
    """
    # key: frozenset of (team1, team2) → list of winner strings or 'draw'
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_features.py -k "h2h" -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/features.py tests/test_features.py
git commit -m "feat: head-to-head record feature (last 10 encounters)"
```

---

### Task 5: Build Full Feature Matrix

**Files:**
- Modify: `backend/model/features.py`
- Modify: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_features.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_features.py -k "build_features" -v
```

Expected: `ImportError: cannot import name 'build_features'`

- [ ] **Step 3: Implement `build_features`**

Append to `backend/model/features.py`:

```python
FEATURE_COLS = [
    'elo_diff', 'home_elo_before', 'away_elo_before',
    'home_form', 'away_form',
    'h2h_home_wins', 'h2h_draws', 'h2h_away_wins',
    'is_neutral',
]


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Apply all feature engineering steps and return (X, y).
    X: DataFrame with FEATURE_COLS columns.
    y: Series with values 0=home win, 1=draw, 2=away win.
    """
    df = compute_elo_ratings(df)
    df = compute_recent_form(df)
    df = compute_h2h(df)

    df['elo_diff'] = df['home_elo_before'] - df['away_elo_before']
    df['is_neutral'] = df['neutral'].astype(int)

    X = df[FEATURE_COLS].copy()

    conditions = [
        df['home_score'] > df['away_score'],
        df['home_score'] == df['away_score'],
        df['home_score'] < df['away_score'],
    ]
    y = pd.Series(
        np.select(conditions, [0, 1, 2]),
        name='outcome',
        dtype=int,
    )
    return X, y
```

- [ ] **Step 4: Run all feature tests**

```bash
pytest tests/test_features.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/model/features.py tests/test_features.py
git commit -m "feat: build_features assembles full 9-column feature matrix with 3-class target"
```

---

### Task 6: Model Training

**Files:**
- Create: `backend/model/train.py`
- Create: `tests/test_train.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_train.py
import os
import pytest
from backend.model.train import train_model, save_model, load_model
from backend.model.features import load_data, build_features


@pytest.fixture(scope="module")
def trained_model():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    # Use a 5000-row subset for speed in tests
    return train_model(X.iloc[:5000], y.iloc[:5000])


def test_train_model_has_predict_proba(trained_model):
    assert hasattr(trained_model, 'predict_proba')


def test_train_model_predict_proba_shape(trained_model):
    df = load_data("data/results.csv")
    X, _ = build_features(df)
    proba = trained_model.predict_proba(X.iloc[:10])
    assert proba.shape == (10, 3)


def test_train_model_probabilities_sum_to_one(trained_model):
    df = load_data("data/results.csv")
    X, _ = build_features(df)
    proba = trained_model.predict_proba(X.iloc[:100])
    row_sums = proba.sum(axis=1)
    assert (abs(row_sums - 1.0) < 1e-6).all()


def test_save_and_load_model(tmp_path, trained_model):
    path = str(tmp_path / "model.pkl")
    save_model(trained_model, path)
    assert os.path.exists(path)
    loaded = load_model(path)
    assert hasattr(loaded, 'predict_proba')
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_train.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `train.py`**

```python
# backend/model/train.py
import joblib
import pandas as pd
from xgboost import XGBClassifier


def train_model(X: pd.DataFrame, y: pd.Series) -> XGBClassifier:
    """Train an XGBoost 3-class classifier (0=home win, 1=draw, 2=away win)."""
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)
    return model


def save_model(model: XGBClassifier, path: str) -> None:
    joblib.dump(model, path)


def load_model(path: str) -> XGBClassifier:
    return joblib.load(path)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_train.py -v
```

Expected: 4 tests PASS. (First run takes ~30s due to training on 5000 rows.)

- [ ] **Step 5: Commit**

```bash
git add backend/model/train.py tests/test_train.py
git commit -m "feat: XGBoost model training, save, and load"
```

---

### Task 7: Backtesting on 2018 & 2022 World Cups

**Files:**
- Create: `backend/model/backtest.py`
- Create: `tests/test_backtest.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_backtest.py
import pytest
from backend.model.backtest import run_backtest, BacktestResult


def test_run_backtest_returns_result():
    result = run_backtest("data/results.csv")
    assert isinstance(result, BacktestResult)


def test_backtest_accuracy_fields_exist():
    result = run_backtest("data/results.csv")
    assert hasattr(result, 'accuracy_2018')
    assert hasattr(result, 'accuracy_2022')
    assert hasattr(result, 'accuracy_combined')


def test_backtest_accuracy_is_valid_proportion():
    result = run_backtest("data/results.csv")
    assert 0.0 <= result.accuracy_2018 <= 1.0
    assert 0.0 <= result.accuracy_2022 <= 1.0
    assert 0.0 <= result.accuracy_combined <= 1.0


def test_backtest_has_predictions():
    result = run_backtest("data/results.csv")
    assert len(result.predictions_2018) > 0
    assert len(result.predictions_2022) > 0


def test_backtest_prediction_has_required_keys():
    result = run_backtest("data/results.csv")
    pred = result.predictions_2018[0]
    required_keys = {'date', 'home_team', 'away_team', 'actual', 'predicted',
                     'prob_home_win', 'prob_draw', 'prob_away_win', 'correct'}
    assert required_keys.issubset(pred.keys())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_backtest.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `backtest.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_backtest.py -v
```

Expected: 5 tests PASS. (Takes 1–2 minutes — two full model trainings.)

- [ ] **Step 5: Print backtest report**

```bash
python -c "
from backend.model.backtest import run_backtest
r = run_backtest('data/results.csv')
print(f'2018 WC Accuracy: {r.accuracy_2018:.1%}  ({len(r.predictions_2018)} matches)')
print(f'2022 WC Accuracy: {r.accuracy_2022:.1%}  ({len(r.predictions_2022)} matches)')
print(f'Combined:         {r.accuracy_combined:.1%}')
"
```

Expected output (approximate — depends on dataset):
```
2018 WC Accuracy: 51.6%  (64 matches)
2022 WC Accuracy: 50.0%  (64 matches)
Combined:         50.8%
```

> Note: ~50% accuracy is reasonable for 3-class football prediction. Human experts typically achieve 50–55%.

- [ ] **Step 6: Commit**

```bash
git add backend/model/backtest.py tests/test_backtest.py
git commit -m "feat: backtest on 2018/2022 World Cups with per-match prediction log"
```

---

### Task 8: Prediction Service

**Files:**
- Create: `backend/model/predict.py`
- Create: `tests/test_predict.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_predict.py
import pytest
from backend.model.predict import PredictorService, MatchPrediction


@pytest.fixture(scope="module")
def svc():
    return PredictorService("data/results.csv")


def test_predict_returns_match_prediction(svc):
    result = svc.predict("Brazil", "Argentina")
    assert isinstance(result, MatchPrediction)


def test_predict_probabilities_sum_to_one(svc):
    result = svc.predict("Brazil", "Argentina")
    total = result.prob_home_win + result.prob_draw + result.prob_away_win
    assert abs(total - 1.0) < 0.01


def test_predict_team_names_preserved(svc):
    result = svc.predict("France", "Germany")
    assert result.home_team == "France"
    assert result.away_team == "Germany"


def test_predict_unknown_teams_still_works(svc):
    """Unknown teams fall back to default ELO 1500; should still return valid probabilities."""
    result = svc.predict("FakeTeamA", "FakeTeamB")
    total = result.prob_home_win + result.prob_draw + result.prob_away_win
    assert abs(total - 1.0) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_predict.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `predict.py`**

```python
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
        self._df_enriched = (
            compute_h2h(compute_recent_form(compute_elo_ratings(df)))
        )

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
        h2h = self._df_enriched[mask]
        if h2h.empty:
            return 0, 0, 0
        last = h2h.iloc[-1]
        # The last row's h2h columns are relative to that row's home/away.
        # Re-count from perspective of current home_team.
        recent = h2h.tail(10)
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_predict.py -v
```

Expected: 4 tests PASS. (Takes ~30–60s to train on full dataset.)

- [ ] **Step 5: Smoke test in terminal**

```bash
python -c "
from backend.model.predict import PredictorService
svc = PredictorService('data/results.csv')
p = svc.predict('Brazil', 'Argentina')
print(f'Brazil vs Argentina:')
print(f'  Brazil win:    {p.prob_home_win:.1%}')
print(f'  Draw:          {p.prob_draw:.1%}')
print(f'  Argentina win: {p.prob_away_win:.1%}')
"
```

- [ ] **Step 6: Commit**

```bash
git add backend/model/predict.py tests/test_predict.py
git commit -m "feat: PredictorService for on-demand match outcome prediction"
```

---

## Subsystem 2: FastAPI Backend

### Task 9: Database Models & Pydantic Schemas

**Files:**
- Create: `backend/db/database.py`
- Create: `backend/db/models.py`
- Create: `backend/schemas.py`
- Create: `.env.example`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write failing tests for DB models**

```python
# tests/test_db.py
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, Match, User, UserPrediction


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_all_tables_created(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert 'matches' in tables
    assert 'users' in tables
    assert 'user_predictions' in tables


def test_match_columns(engine):
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('matches')}
    assert {'id', 'home_team', 'away_team', 'match_date', 'tournament',
            'home_score', 'away_score', 'is_locked'}.issubset(cols)


def test_user_columns(engine):
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('users')}
    assert {'id', 'username', 'total_points'}.issubset(cols)


def test_user_prediction_columns(engine):
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('user_predictions')}
    assert {'id', 'user_id', 'match_id', 'predicted_outcome', 'points_awarded'}.issubset(cols)


def test_insert_and_query(engine):
    Session = sessionmaker(bind=engine)
    db = Session()
    from datetime import datetime
    match = Match(
        home_team="Brazil", away_team="France",
        match_date=datetime(2026, 6, 1), tournament="Friendly",
    )
    db.add(match)
    db.commit()
    fetched = db.query(Match).filter_by(home_team="Brazil").first()
    assert fetched is not None
    assert fetched.away_team == "France"
    db.close()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `database.py`**

```python
# backend/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Implement `models.py`**

```python
# backend/db/models.py
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    match_date = Column(DateTime, nullable=False)
    tournament = Column(String, nullable=False, default="Friendly")
    home_score = Column(Integer, nullable=True)   # null until played
    away_score = Column(Integer, nullable=True)
    is_locked = Column(Boolean, default=False)    # True after kickoff

    predictions = relationship("UserPrediction", back_populates="match")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    total_points = Column(Integer, default=0)

    predictions = relationship("UserPrediction", back_populates="user")


class UserPrediction(Base):
    __tablename__ = "user_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    predicted_outcome = Column(String, nullable=False)  # 'home_win' | 'draw' | 'away_win'
    points_awarded = Column(Integer, nullable=True)      # null until scored
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")
```

- [ ] **Step 5: Create `schemas.py`**

```python
# backend/schemas.py
from pydantic import BaseModel


class PredictRequest(BaseModel):
    home_team: str
    away_team: str
    neutral: bool = True


class PredictResponse(BaseModel):
    home_team: str
    away_team: str
    prob_home_win: float
    prob_draw: float
    prob_away_win: float


class UserPredictRequest(BaseModel):
    username: str
    match_id: int
    predicted_outcome: str  # 'home_win' | 'draw' | 'away_win'


class UserPredictResponse(BaseModel):
    id: int
    username: str
    match_id: int
    predicted_outcome: str
    message: str


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    total_points: int
    correct_predictions: int


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


class ResultRequest(BaseModel):
    match_id: int
    home_score: int
    away_score: int
```

- [ ] **Step 6: Create `.env.example`**

```
DATABASE_URL=postgresql://user:password@localhost:5432/worldcup
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_db.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/db/database.py backend/db/models.py backend/schemas.py .env.example tests/test_db.py
git commit -m "feat: SQLAlchemy models (Match, User, UserPrediction) and Pydantic schemas"
```

---

### Task 10: FastAPI App Entry Point

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement `main.py`**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine
from backend.db.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="World Cup Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_main.py -v
```

Expected: 1 test PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: FastAPI app skeleton with CORS and /health endpoint"
```

---

### Task 11: POST /predict and POST /user/predict Routes

**Files:**
- Create: `backend/routes/predictions.py`
- Modify: `backend/main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_main.py`:

```python
def test_predict_returns_probabilities(client):
    resp = client.post("/predict", json={"home_team": "Brazil", "away_team": "Argentina", "neutral": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "prob_home_win" in data
    assert "prob_draw" in data
    assert "prob_away_win" in data
    total = data["prob_home_win"] + data["prob_draw"] + data["prob_away_win"]
    assert abs(total - 1.0) < 0.01


def test_predict_returns_correct_team_names(client):
    resp = client.post("/predict", json={"home_team": "France", "away_team": "Germany", "neutral": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["home_team"] == "France"
    assert data["away_team"] == "Germany"


def test_user_predict_requires_valid_outcome(client):
    resp = client.post("/user/predict", json={
        "username": "alice", "match_id": 999, "predicted_outcome": "invalid"
    })
    assert resp.status_code == 422


def test_user_predict_404_on_missing_match(client):
    resp = client.post("/user/predict", json={
        "username": "alice", "match_id": 99999, "predicted_outcome": "home_win"
    })
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py::test_predict_returns_probabilities -v
```

Expected: 404 Not Found (route doesn't exist yet).

- [ ] **Step 3: Implement `predictions.py`**

```python
# backend/routes/predictions.py
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import User, UserPrediction, Match
from backend.model.predict import PredictorService
from backend.schemas import (
    PredictRequest, PredictResponse, UserPredictRequest, UserPredictResponse,
)

router = APIRouter()

DATA_PATH = "data/results.csv"
VALID_OUTCOMES = {'home_win', 'draw', 'away_win'}


@lru_cache(maxsize=1)
def get_predictor() -> PredictorService:
    """Load and cache the PredictorService (training runs on first call, ~30s)."""
    return PredictorService(DATA_PATH)


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    predictor = get_predictor()
    pred = predictor.predict(request.home_team, request.away_team, neutral=request.neutral)
    return PredictResponse(
        home_team=pred.home_team,
        away_team=pred.away_team,
        prob_home_win=pred.prob_home_win,
        prob_draw=pred.prob_draw,
        prob_away_win=pred.prob_away_win,
    )


@router.post("/user/predict", response_model=UserPredictResponse)
def user_predict(request: UserPredictRequest, db: Session = Depends(get_db)):
    if request.predicted_outcome not in VALID_OUTCOMES:
        raise HTTPException(status_code=422, detail=f"predicted_outcome must be one of {VALID_OUTCOMES}")

    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.is_locked:
        raise HTTPException(status_code=409, detail="Match is locked — predictions closed at kickoff")

    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        user = User(username=request.username)
        db.add(user)
        db.flush()

    existing = db.query(UserPrediction).filter(
        UserPrediction.user_id == user.id,
        UserPrediction.match_id == request.match_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Prediction already submitted for this match")

    prediction = UserPrediction(
        user_id=user.id,
        match_id=request.match_id,
        predicted_outcome=request.predicted_outcome,
    )
    db.add(prediction)
    db.commit()

    return UserPredictResponse(
        id=prediction.id,
        username=request.username,
        match_id=request.match_id,
        predicted_outcome=request.predicted_outcome,
        message="Prediction recorded",
    )
```

- [ ] **Step 4: Register router in `main.py`**

Add after the existing `@app.get("/health")` block:

```python
from backend.routes.predictions import router as predictions_router
app.include_router(predictions_router)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_main.py -v
```

Expected: All tests PASS. (First run takes ~30s for `get_predictor()` to train the model.)

- [ ] **Step 6: Commit**

```bash
git add backend/routes/predictions.py backend/main.py tests/test_main.py
git commit -m "feat: POST /predict and POST /user/predict routes with lock validation"
```

---

### Task 12: GET /leaderboard and POST /results Routes

**Files:**
- Create: `backend/routes/users.py`
- Modify: `backend/main.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_main.py`:

```python
def test_leaderboard_returns_entries_list(client):
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_score_results_updates_user_points(client):
    from backend.db.database import SessionLocal
    from backend.db.models import Match, User, UserPrediction
    from datetime import datetime

    db = SessionLocal()
    match = Match(
        home_team="Brazil", away_team="France",
        match_date=datetime(2026, 7, 1), tournament="Test Cup",
        is_locked=False,
    )
    db.add(match)
    user = User(username="scorer_test_user")
    db.add(user)
    db.flush()
    pred = UserPrediction(
        user_id=user.id, match_id=match.id, predicted_outcome="home_win",
    )
    db.add(pred)
    db.commit()
    match_id = match.id
    db.close()

    resp = client.post("/results", json={"match_id": match_id, "home_score": 2, "away_score": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scored_predictions"] == 1
    assert data["actual_outcome"] == "home_win"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py::test_leaderboard_returns_entries_list -v
```

Expected: 404 Not Found.

- [ ] **Step 3: Implement `users.py`**

```python
# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Match, User, UserPrediction
from backend.schemas import LeaderboardEntry, LeaderboardResponse, ResultRequest

router = APIRouter()


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.total_points.desc()).limit(50).all()
    entries = []
    for rank, user in enumerate(users, start=1):
        correct = db.query(func.count(UserPrediction.id)).filter(
            UserPrediction.user_id == user.id,
            UserPrediction.points_awarded > 0,
        ).scalar() or 0
        entries.append(LeaderboardEntry(
            rank=rank,
            username=user.username,
            total_points=user.total_points,
            correct_predictions=correct,
        ))
    return LeaderboardResponse(entries=entries)


@router.post("/results")
def score_results(request: ResultRequest, db: Session = Depends(get_db)):
    """
    Record the final score for a match and award points to all users who predicted it.
    Call once after the final whistle. Correct prediction = 3 points.
    """
    match = db.query(Match).filter(Match.id == request.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.home_score = request.home_score
    match.away_score = request.away_score
    match.is_locked = True

    if request.home_score > request.away_score:
        actual = "home_win"
    elif request.home_score < request.away_score:
        actual = "away_win"
    else:
        actual = "draw"

    unscored = db.query(UserPrediction).filter(
        UserPrediction.match_id == request.match_id,
        UserPrediction.points_awarded.is_(None),
    ).all()

    scored = 0
    for pred in unscored:
        points = 3 if pred.predicted_outcome == actual else 0
        pred.points_awarded = points
        user = db.query(User).filter(User.id == pred.user_id).first()
        if user:
            user.total_points += points
        scored += 1

    db.commit()
    return {"scored_predictions": scored, "actual_outcome": actual}
```

- [ ] **Step 4: Register router in `main.py`**

Add after the predictions router include:

```python
from backend.routes.users import router as users_router
app.include_router(users_router)
```

- [ ] **Step 5: Run all backend tests**

```bash
pytest tests/ -v --ignore=tests/test_backtest.py
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/routes/users.py backend/main.py tests/test_main.py
git commit -m "feat: GET /leaderboard and POST /results for scoring user predictions"
```

---

## Subsystem 3: React Frontend

### Task 13: React App Scaffold

**Files:**
- Create: `frontend/` (Vite + React + Tailwind)
- Create: `frontend/src/api/client.js`
- Create: `frontend/src/App.jsx`

- [ ] **Step 1: Scaffold Vite app**

```bash
cd world-cup-predictor
npm create vite@latest frontend -- --template react
cd frontend && npm install
npm install react-router-dom axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 2: Configure Tailwind — replace `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 3: Replace `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: Create `frontend/src/api/client.js`**

```js
// frontend/src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

export const predictMatch = (homeTeam, awayTeam, neutral = true) =>
  api.post('/predict', { home_team: homeTeam, away_team: awayTeam, neutral });

export const submitUserPrediction = (username, matchId, predictedOutcome) =>
  api.post('/user/predict', { username, match_id: matchId, predicted_outcome: predictedOutcome });

export const getLeaderboard = () =>
  api.get('/leaderboard');

export default api;
```

- [ ] **Step 5: Replace `frontend/src/App.jsx`**

```jsx
// frontend/src/App.jsx
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import MatchPredictor from './pages/MatchPredictor';
import Leaderboard from './pages/Leaderboard';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center gap-8">
          <Link to="/" className="text-lg font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
            ⚽ World Cup Predictor
          </Link>
          <Link to="/leaderboard" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
            Leaderboard
          </Link>
        </nav>
        <main className="max-w-3xl mx-auto px-4 py-10">
          <Routes>
            <Route path="/" element={<MatchPredictor />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd frontend && npm run dev
```

Expected: Vite running at http://localhost:5173. App renders (pages will be empty stubs until Task 14).

- [ ] **Step 7: Create stub pages so routes don't 404**

```jsx
// frontend/src/pages/MatchPredictor.jsx
export default function MatchPredictor() { return <p>Match Predictor coming soon</p>; }
```

```jsx
// frontend/src/pages/Leaderboard.jsx
export default function Leaderboard() { return <p>Leaderboard coming soon</p>; }
```

- [ ] **Step 8: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: React + Vite + Tailwind + React Router scaffold with API client"
```

---

### Task 14: Match Predictor Page

**Files:**
- Create: `frontend/src/components/ProbabilityBar.jsx`
- Create: `frontend/src/components/TeamSelector.jsx`
- Modify: `frontend/src/pages/MatchPredictor.jsx`

- [ ] **Step 1: Create `ProbabilityBar.jsx`**

```jsx
// frontend/src/components/ProbabilityBar.jsx
export default function ProbabilityBar({ label, probability, colorClass }) {
  const pct = Math.round(probability * 100);
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1.5">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="font-bold text-white">{pct}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden">
        <div
          className={`h-4 rounded-full transition-all duration-700 ease-out ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `TeamSelector.jsx`**

```jsx
// frontend/src/components/TeamSelector.jsx
const TEAMS = [
  "Argentina","Australia","Belgium","Brazil","Cameroon","Canada","Costa Rica",
  "Croatia","Denmark","Ecuador","England","France","Germany","Ghana","Italy",
  "Japan","Mexico","Morocco","Netherlands","Poland","Portugal","Qatar",
  "Saudi Arabia","Senegal","Serbia","South Korea","Spain","Switzerland",
  "Tunisia","Uruguay","USA","Wales",
].sort();

export default function TeamSelector({ label, value, onChange }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-gray-400 font-semibold uppercase tracking-wide">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
      >
        <option value="">Select team…</option>
        {TEAMS.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
    </div>
  );
}
```

- [ ] **Step 3: Replace `frontend/src/pages/MatchPredictor.jsx`**

```jsx
// frontend/src/pages/MatchPredictor.jsx
import { useState } from 'react';
import ProbabilityBar from '../components/ProbabilityBar';
import TeamSelector from '../components/TeamSelector';
import { predictMatch, submitUserPrediction } from '../api/client';

const OUTCOME_BUTTONS = (home, away) => [
  { value: 'home_win', label: `${home} Win`, color: 'bg-emerald-600 border-emerald-500' },
  { value: 'draw',     label: 'Draw',        color: 'bg-yellow-600 border-yellow-500' },
  { value: 'away_win', label: `${away} Win`, color: 'bg-blue-600 border-blue-500' },
];

export default function MatchPredictor() {
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam]  = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [username, setUsername] = useState('');
  const [userPick, setUserPick] = useState('');
  const [submitState, setSubmitState] = useState('idle'); // 'idle' | 'loading' | 'done' | 'error'
  const [submitError, setSubmitError] = useState('');

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) return setError('Select both teams');
    if (homeTeam === awayTeam) return setError('Teams must be different');
    setError('');
    setLoading(true);
    setPrediction(null);
    setUserPick('');
    setSubmitState('idle');
    try {
      const { data } = await predictMatch(homeTeam, awayTeam);
      setPrediction(data);
    } catch {
      setError('Prediction failed — is the backend running at localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  const handleUserSubmit = async () => {
    if (!username.trim() || !userPick) return;
    setSubmitState('loading');
    setSubmitError('');
    try {
      await submitUserPrediction(username.trim(), 1, userPick); // match_id=1 is a placeholder
      setSubmitState('done');
    } catch (e) {
      setSubmitError(e.response?.data?.detail || 'Failed to submit prediction');
      setSubmitState('error');
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-1 text-emerald-400">Match Predictor</h1>
      <p className="text-gray-500 mb-8 text-sm">AI-powered Win / Draw / Loss probabilities</p>

      {/* Team selector card */}
      <div className="bg-gray-900 rounded-2xl p-6 mb-5 border border-gray-800">
        <div className="grid grid-cols-2 gap-4 mb-5">
          <TeamSelector label="Home Team" value={homeTeam} onChange={setHomeTeam} />
          <TeamSelector label="Away Team" value={awayTeam} onChange={setAwayTeam} />
        </div>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <button
          onClick={handlePredict}
          disabled={loading || !homeTeam || !awayTeam}
          className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 disabled:text-gray-600 text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {loading ? 'Predicting…' : 'Get AI Prediction'}
        </button>
      </div>

      {/* AI prediction output */}
      {prediction && (
        <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 mb-5">
          <h2 className="text-lg font-semibold mb-5 text-gray-200">
            {prediction.home_team}
            <span className="text-gray-500 mx-2">vs</span>
            {prediction.away_team}
          </h2>
          <ProbabilityBar
            label={`${prediction.home_team} Win`}
            probability={prediction.prob_home_win}
            colorClass="bg-emerald-500"
          />
          <ProbabilityBar
            label="Draw"
            probability={prediction.prob_draw}
            colorClass="bg-yellow-500"
          />
          <ProbabilityBar
            label={`${prediction.away_team} Win`}
            probability={prediction.prob_away_win}
            colorClass="bg-blue-500"
          />

          {/* User prediction form */}
          <div className="mt-6 pt-5 border-t border-gray-800">
            <h3 className="font-semibold mb-3 text-gray-300 text-sm uppercase tracking-wide">
              Your Prediction
            </h3>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white mb-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <div className="grid grid-cols-3 gap-2 mb-4">
              {OUTCOME_BUTTONS(prediction.home_team, prediction.away_team).map(({ value, label, color }) => (
                <button
                  key={value}
                  onClick={() => setUserPick(value)}
                  className={`py-2.5 rounded-xl text-sm font-medium transition-all border ${
                    userPick === value
                      ? `${color} text-white`
                      : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {submitState === 'done' ? (
              <p className="text-emerald-400 text-center font-semibold">
                ✓ Prediction locked in!
              </p>
            ) : (
              <>
                {submitError && <p className="text-red-400 text-sm mb-2">{submitError}</p>}
                <button
                  onClick={handleUserSubmit}
                  disabled={!username.trim() || !userPick || submitState === 'loading'}
                  className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white font-semibold py-2.5 rounded-xl transition-colors text-sm"
                >
                  {submitState === 'loading' ? 'Submitting…' : 'Lock In My Pick'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Test in browser**

Start both servers in separate terminals:
```bash
# Terminal 1 — backend
cd world-cup-predictor && uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd world-cup-predictor/frontend && npm run dev
```

Open http://localhost:5173. Select Brazil vs Argentina, click "Get AI Prediction". Verify:
- Three probability bars render with correct percentages
- Percentages sum to 100%
- Picking an outcome highlights the button
- "Lock In My Pick" button is disabled until both username and outcome are chosen

- [ ] **Step 5: Commit**

```bash
cd world-cup-predictor
git add frontend/src/
git commit -m "feat: Match Predictor page with probability bars and user pick form"
```

---

### Task 15: Leaderboard Page

**Files:**
- Modify: `frontend/src/pages/Leaderboard.jsx`

- [ ] **Step 1: Replace `frontend/src/pages/Leaderboard.jsx`**

```jsx
// frontend/src/pages/Leaderboard.jsx
import { useEffect, useState } from 'react';
import { getLeaderboard } from '../api/client';

const MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLeaderboard()
      .then(({ data }) => setEntries(data.entries))
      .catch(() => setError('Could not load leaderboard — is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-1 text-emerald-400">Leaderboard</h1>
      <p className="text-gray-500 mb-8 text-sm">Ranked by total prediction points</p>

      {loading && <p className="text-gray-500">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <div className="bg-gray-900 rounded-2xl p-10 border border-gray-800 text-center">
          <p className="text-gray-500">No predictions yet — be the first to predict a match!</p>
        </div>
      )}

      {entries.length > 0 && (
        <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wide">
                <th className="px-6 py-3 text-left">Rank</th>
                <th className="px-6 py-3 text-left">Player</th>
                <th className="px-6 py-3 text-right">Points</th>
                <th className="px-6 py-3 text-right">Correct</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.rank}
                  className="border-b border-gray-800 last:border-0 hover:bg-gray-800/40 transition-colors"
                >
                  <td className="px-6 py-4 text-gray-400 font-medium">
                    {MEDALS[entry.rank] ?? `#${entry.rank}`}
                  </td>
                  <td className="px-6 py-4 font-semibold text-white">{entry.username}</td>
                  <td className="px-6 py-4 text-right text-emerald-400 font-bold">
                    {entry.total_points} pts
                  </td>
                  <td className="px-6 py-4 text-right text-gray-400">
                    {entry.correct_predictions}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify in browser**

Navigate to http://localhost:5173/leaderboard. Should show the empty-state message. After submitting a prediction and scoring it via `POST /results`, re-check to confirm user appears in table.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Leaderboard.jsx
git commit -m "feat: Leaderboard page with rankings table and empty state"
```

---

### Task 16: Final Integration Check

- [ ] **Step 1: Run full test suite**

```bash
cd world-cup-predictor && pytest tests/ -v --tb=short
```

Expected: All tests PASS.

- [ ] **Step 2: Print backtest accuracy**

```bash
python -c "
from backend.model.backtest import run_backtest
r = run_backtest('data/results.csv')
print(f'2018 WC Accuracy: {r.accuracy_2018:.1%}  ({len(r.predictions_2018)} matches)')
print(f'2022 WC Accuracy: {r.accuracy_2022:.1%}  ({len(r.predictions_2022)} matches)')
print(f'Combined:         {r.accuracy_combined:.1%}')
"
```

- [ ] **Step 3: End-to-end smoke test**

With both servers running:
1. Open http://localhost:5173
2. Select France vs Germany → click "Get AI Prediction" → verify probability bars appear
3. Enter a username, pick an outcome, click "Lock In My Pick" → verify "Prediction locked in!"
4. Open http://localhost:5173/leaderboard → verify it loads (empty state is fine)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final integration — all tests passing, full stack verified"
```

---

## Notes for Deployment (Render / Railway)

- Set `DATABASE_URL` environment variable to the PostgreSQL connection string.
- Change `allow_origins` in `main.py` to your frontend's production URL.
- Set `VITE_API_URL` in Vite build environment to your backend URL.
- Pre-train the model and save to `backend/model/trained_model.pkl` using `save_model()` so startup doesn't require 30s training on cold start.
