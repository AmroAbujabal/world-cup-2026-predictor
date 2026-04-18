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
    from datetime import datetime
    Session = sessionmaker(bind=engine)
    db = Session()
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
