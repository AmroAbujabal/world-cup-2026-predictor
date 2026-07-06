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
    total_predictions: int = 0


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]


class ResultRequest(BaseModel):
    match_id: int
    home_score: int
    away_score: int
    penalty_home: int | None = None
    penalty_away: int | None = None
    went_to_extra_time: bool | None = None


class MatchResponse(BaseModel):
    id: int
    home_team: str
    away_team: str
    match_date: str
    stage: str
    status: str
    home_score: int | None = None
    away_score: int | None = None
    went_to_penalties: bool | None = None
    penalty_home: int | None = None
    penalty_away: int | None = None
    went_to_extra_time: bool | None = None
    is_upset: bool | None = None
    prob_home: float | None = None
    prob_draw: float | None = None
    prob_away: float | None = None
