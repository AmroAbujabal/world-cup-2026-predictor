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


# Predicted R32 based on the official 2026 WC draw (December 2024)
# Pairings follow FIFA format: 1A vs 2B, 1B vs 2A, 1C vs 2D, ... 1K vs 2L, 1L vs 2K
# Final 4 matches use 8 best 3rd-place qualifiers (most likely candidates shown)
BRACKET_R32 = [
    # Group A winner vs Group B runner-up
    ("Mexico",      "Canada"),
    # Group B winner vs Group A runner-up
    ("Switzerland", "South Korea"),
    # Group C winner vs Group D runner-up
    ("Brazil",      "Turkey"),
    # Group D winner vs Group C runner-up
    ("United States", "Morocco"),
    # Group E winner vs Group F runner-up
    ("Germany",     "Japan"),
    # Group F winner vs Group E runner-up
    ("Netherlands", "Ecuador"),
    # Group G winner vs Group H runner-up
    ("Belgium",     "Uruguay"),
    # Group H winner vs Group G runner-up
    ("Spain",       "Egypt"),
    # Group I winner vs Group J runner-up
    ("France",      "Austria"),
    # Group J winner vs Group I runner-up
    ("Argentina",   "Senegal"),
    # Group K winner vs Group L runner-up
    ("Portugal",    "Croatia"),
    # Group L winner vs Group K runner-up
    ("England",     "Colombia"),
    # Best 3rd-place matches
    ("South Africa",           "Bosnia and Herzegovina"),
    ("Scotland",               "Paraguay"),
    ("Ivory Coast",            "Sweden"),
    ("Iran",                   "Norway"),
]


@router.post("/group-standings")
def group_standings(request: dict):
    """Predict group standings by simulating all 6 round-robin matches."""
    teams = request.get("teams", [])
    if len(teams) != 4:
        raise HTTPException(status_code=422, detail="Must provide exactly 4 teams")
    predictor = get_predictor()
    from itertools import combinations
    points = {t: 0 for t in teams}
    prob_score = {t: 0.0 for t in teams}
    for home, away in combinations(teams, 2):
        p = predictor.predict(home, away, neutral=True)
        if p.prob_home_win >= p.prob_draw and p.prob_home_win >= p.prob_away_win:
            points[home] += 3
        elif p.prob_away_win >= p.prob_home_win and p.prob_away_win >= p.prob_draw:
            points[away] += 3
        else:
            points[home] += 1
            points[away] += 1
        prob_score[home] += p.prob_home_win
        prob_score[away] += p.prob_away_win
    standings = sorted(teams, key=lambda t: (points[t], prob_score[t]), reverse=True)
    return {"standings": [{"team": t, "pts": points[t]} for t in standings]}


@router.get("/bracket-predictions")
def bracket_predictions():
    """Run the AI model through all knockout rounds and return the full predicted bracket."""
    predictor = get_predictor()

    def predict_winner(team1, team2):
        p = predictor.predict(team1, team2, neutral=True)
        winner = team1 if p.prob_home_win >= p.prob_away_win else team2
        return {
            "team1": team1, "team2": team2,
            "prob1": round(p.prob_home_win, 3),
            "prob_draw": round(p.prob_draw, 3),
            "prob2": round(p.prob_away_win, 3),
            "predicted_winner": winner,
        }

    rounds = []
    round_names = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Final"]

    pairs = BRACKET_R32
    for round_name in round_names:
        matchups = [predict_winner(a, b) for a, b in pairs]
        rounds.append({"round": round_name, "matchups": matchups})
        winners = [m["predicted_winner"] for m in matchups]
        if len(winners) > 1:
            pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    champion = rounds[-1]["matchups"][0]["predicted_winner"] if rounds else None
    return {"rounds": rounds, "champion": champion}


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
        # Allow updating a prediction as long as the match isn't locked
        existing.predicted_outcome = request.predicted_outcome
        db.commit()
        return UserPredictResponse(
            id=existing.id,
            username=request.username,
            match_id=request.match_id,
            predicted_outcome=request.predicted_outcome,
            message="Prediction updated",
        )

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
