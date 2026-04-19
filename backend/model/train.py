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
        n_jobs=1,  # single-threaded to cap memory usage on constrained servers
    )
    model.fit(X, y)
    return model


def save_model(model: XGBClassifier, path: str) -> None:
    joblib.dump(model, path)


def load_model(path: str) -> XGBClassifier:
    return joblib.load(path)
