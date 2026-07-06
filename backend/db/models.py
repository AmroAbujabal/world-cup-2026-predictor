# backend/db/models.py
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
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
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_locked = Column(Boolean, default=False)
    status = Column(String, default="upcoming")   # upcoming | live | final
    external_id = Column(Integer, nullable=True)  # football-data.org match ID

    # Knockout / display metadata (nullable — added via _migrate_db for existing DBs)
    went_to_penalties = Column(Boolean, nullable=True)
    penalty_home = Column(Integer, nullable=True)
    penalty_away = Column(Integer, nullable=True)
    went_to_extra_time = Column(Boolean, nullable=True)
    is_upset = Column(Boolean, nullable=True)

    # Stored model Win/Draw/Loss probabilities (for the current home/away orientation)
    prob_home = Column(Float, nullable=True)
    prob_draw = Column(Float, nullable=True)
    prob_away = Column(Float, nullable=True)

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
    predicted_outcome = Column(String, nullable=False)
    points_awarded = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")
