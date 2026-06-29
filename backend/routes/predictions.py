# backend/routes/predictions.py
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import User, UserPrediction, Match
from backend.model.predict import PredictorService
from backend.schemas import PredictRequest, PredictResponse, UserPredictRequest, UserPredictResponse, MatchResponse

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


# Official WC 2026 bracket — ordered so sequential R16 pairings are correct
# R16 pairs: (0,1) (2,3) (4,5) (6,7) (8,9) (10,11) (12,13) (14,15)
# Source: confirmed R16 schedule (Jul 4–7 2026)
#   0v1 → Germany vs France        (Jul 4, Philadelphia)
#   2v3 → Canada vs Netherlands    (Jul 4, Houston)
#   4v5 → Brazil vs Norway         (Jul 5, East Rutherford)
#   6v7 → Mexico vs England        (Jul 5, Mexico City)
#   8v9 → Portugal vs Spain        (Jul 6, Arlington)
#  10v11→ USA vs Senegal           (Jul 6, Seattle)
#  12v13→ Argentina vs Egypt       (Jul 7, Atlanta)
#  14v15→ Switzerland vs Colombia  (Jul 7, Vancouver)
BRACKET_R32 = [
    ("Germany",               "Paraguay"),           # 0  → R16 vs France winner     (DB id 3)
    ("France",                "Sweden"),             # 1  → R16 vs Germany winner    (DB id 6)
    ("South Africa",          "Canada"),             # 2  → R16 vs Netherlands win.  (DB id 1)
    ("Netherlands",           "Morocco"),            # 3  → R16 vs Canada            (DB id 4)
    ("Brazil",                "Japan"),              # 4  → R16 vs Norway winner     (DB id 2)
    ("Ivory Coast",           "Norway"),             # 5  → R16 vs Brazil            (DB id 5)
    ("Mexico",                "Ecuador"),            # 6  → R16 vs England winner    (DB id 7)
    ("England",               "DR Congo"),           # 7  → R16 vs Mexico winner     (DB id 8)
    ("Portugal",              "Croatia"),            # 8  → R16 vs Spain winner      (DB id 12)
    ("Spain",                 "Austria"),            # 9  → R16 vs Portugal winner   (DB id 11)
    ("Belgium",               "Senegal"),            # 10 → R16 vs USA winner        (DB id 9)
    ("USA",                   "Bosnia and Herzegovina"), # 11 → R16 vs Belgium/Sen.  (DB id 10)
    ("Argentina",             "Cape Verde"),         # 12 → R16 vs Egypt winner      (DB id 15)
    ("Australia",             "Egypt"),              # 13 → R16 vs Argentina         (DB id 14)
    ("Switzerland",           "Algeria"),            # 14 → R16 vs Colombia winner   (DB id 13)
    ("Colombia",              "Ghana"),              # 15 → R16 vs Switzerland       (DB id 16)
]

# Known R32 results — bracket index → actual winner
R32_RESULTS = {
    2: "Canada",   # South Africa 0-1 Canada  (bracket idx 2)
    4: "Brazil",   # Brazil 2-1 Japan          (bracket idx 4)
}


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

    def predict_winner(team1, team2, known_winner=None):
        if known_winner:
            # Use real result — redistribute draw prob for display consistency
            p = predictor.predict(team1, team2, neutral=True)
            base = p.prob_home_win + p.prob_away_win
            prob1 = round(p.prob_home_win / base, 3) if base > 0 else 0.5
            prob2 = round(p.prob_away_win / base, 3) if base > 0 else 0.5
            return {
                "team1": team1, "team2": team2,
                "prob1": prob1, "prob2": prob2,
                "predicted_winner": known_winner,
                "actual_winner": known_winner,
            }
        p = predictor.predict(team1, team2, neutral=True)
        base = p.prob_home_win + p.prob_away_win
        prob1 = round(p.prob_home_win / base, 3) if base > 0 else 0.5
        prob2 = round(p.prob_away_win / base, 3) if base > 0 else 0.5
        winner = team1 if prob1 >= prob2 else team2
        return {
            "team1": team1, "team2": team2,
            "prob1": prob1, "prob2": prob2,
            "predicted_winner": winner,
        }

    rounds = []
    round_names = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals", "Final"]

    pairs = list(BRACKET_R32)
    for round_idx, round_name in enumerate(round_names):
        matchups = []
        for match_idx, (a, b) in enumerate(pairs):
            known = R32_RESULTS.get(match_idx) if round_idx == 0 else None
            matchups.append(predict_winner(a, b, known_winner=known))
        rounds.append({"round": round_name, "matchups": matchups})
        winners = [m["predicted_winner"] for m in matchups]
        if len(winners) > 1:
            pairs = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    champion = rounds[-1]["matchups"][0]["predicted_winner"] if rounds else None
    return {"rounds": rounds, "champion": champion}


def _stage_label(match_id: int) -> str:
    if match_id <= 16: return "R32"
    if match_id <= 24: return "R16"
    if match_id <= 28: return "QF"
    if match_id <= 30: return "SF"
    return "Final"


@router.get("/matches", response_model=list[MatchResponse])
def get_matches(db: Session = Depends(get_db)):
    """Return all knockout fixtures with current status and scores."""
    matches = db.query(Match).order_by(Match.id).all()
    return [
        MatchResponse(
            id=m.id,
            home_team=m.home_team,
            away_team=m.away_team,
            match_date=m.match_date.isoformat(),
            stage=_stage_label(m.id),
            status=m.status or "upcoming",
            home_score=m.home_score,
            away_score=m.away_score,
        )
        for m in matches
    ]


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
