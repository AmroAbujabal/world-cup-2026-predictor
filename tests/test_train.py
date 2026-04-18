import pytest
from backend.model.train import train_model, save_model, load_model
from backend.model.features import load_data, build_features


@pytest.fixture(scope="module")
def trained_model():
    df = load_data("data/results.csv")
    X, y = build_features(df)
    # Use a 5000-row subset for test speed
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
    import os
    path = str(tmp_path / "model.pkl")
    save_model(trained_model, path)
    assert os.path.exists(path)
    loaded = load_model(path)
    assert hasattr(loaded, 'predict_proba')
