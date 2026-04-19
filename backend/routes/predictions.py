# backend/routes/predictions.py
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import User, UserPrediction, Match
from backend.model.predict import PredictorService
from backend.schemas import PredictRequest, PredictResponse, UserPredictRequest, UserPredictResponse

router = APIRouter()

DATA_PATH = "data/results.csv"
VALID_OUTCOMES = {'home_win', 'draw', 'away_win'}


@lru_cache(maxsize=1)
def get_predictor() -> PredictorService:
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
