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
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_locked = Column(Boolean, default=False)

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
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")
