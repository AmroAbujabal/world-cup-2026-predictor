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
    predicted_outcome: str


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
