# FIFA World Cup 2026 Predictor

A full-stack machine learning app that predicts match outcomes for the 2026 FIFA World Cup. Pick your group stage results, select your Round of 32 bracket, and compare your predictions against an XGBoost model trained on 49,287 international matches.

**Live app:** https://frontend-nine-alpha-56.vercel.app

---

## Features

- **Group Stage Picker** — 48 teams across 12 groups. Click to rank the top 2 per group, or hit "AI picks" to auto-fill with ML predictions. Pick 8 of 12 third-place teams to advance.
- **Knockout Bracket** — Round of 32 → Round of 16 → Quarter-finals → Semi-finals → Final. Pre-seeded from your group picks with AI win probabilities on every matchup.
- **AI Predictions** — XGBoost 3-class classifier (home win / draw / away win) with ELO ratings, recent form, and head-to-head features. Beats random baseline by ~7%.
- **Analysis Page** — Research article covering the data, model architecture, backtest results, and the AI's full predicted bracket.
- **Leaderboard** — Submit your bracket and track predictions against other users.

---

## Tech Stack

| Layer | Tech |
|---|---|
| ML Model | XGBoost, pandas, scikit-learn |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | React 18, Vite, Tailwind CSS v3, React Router |
| Deployment | Railway (backend), Vercel (frontend) |

---

## Model Details

- **Training data:** 49,287 international matches (1872–2024)
- **Algorithm:** XGBoost 3-class classifier
- **Features:** ELO rating differential (tournament-weighted), home ELO, away ELO, home recent form (last 5), away recent form (last 5), home H2H win rate, away H2H win rate, match count, neutral ground flag
- **2018 World Cup accuracy:** 40.6% (vs 33.3% random baseline)
- **2022 World Cup accuracy:** 39.1%

---

## Local Development

### Prerequisites

- Python 3.12
- Node.js 18+

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server (trains model on first request ~30s)
uvicorn backend.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

App at `http://localhost:5173`

### Environment Variables

**Frontend** — create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8000
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/predict` | Predict a single match outcome |
| `POST` | `/group-standings` | Simulate round-robin standings for 4 teams |
| `GET` | `/bracket-predictions` | Full AI-predicted knockout bracket |
| `POST` | `/user/predict` | Submit a user bracket prediction |
| `GET` | `/leaderboard` | Ranked leaderboard by prediction points |
| `POST` | `/results` | Score predictions after a real match result |
| `GET` | `/health` | Health check |

---

## Project Structure

```
world-cup-predictor/
├── backend/
│   ├── main.py              # FastAPI app + CORS
│   ├── model/
│   │   └── predict.py       # PredictorService (XGBoost)
│   ├── routes/
│   │   ├── predictions.py   # /predict, /group-standings, /bracket-predictions
│   │   └── users.py         # /leaderboard, /results
│   ├── db/
│   │   ├── database.py      # SQLAlchemy engine
│   │   └── models.py        # User, Match, UserPrediction
│   └── schemas.py           # Pydantic request/response models
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── GroupStage.jsx       # Home — group stage picker
│       │   ├── BracketChallenge.jsx # Knockout bracket
│       │   ├── Analysis.jsx         # Research article + AI bracket
│       │   └── Leaderboard.jsx      # User rankings
│       ├── components/
│       │   └── MatchupCard.jsx      # Individual bracket card
│       ├── data/
│       │   └── wc2026.js            # 48 teams, 12 groups, buildR32()
│       └── api/
│           └── client.js            # Axios API client
├── data/
│   └── results.csv          # 49,287 international match results
├── Procfile                 # Railway deploy command
└── .python-version          # Pins Python 3.12 for Railway
```

---

## Deployment

### Backend — Railway

```bash
# Install CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up --service world-cup-2026-predictor
```

The `Procfile` and `.python-version` (3.12) are already configured.

### Frontend — Vercel

```bash
# Install CLI
npm install -g vercel

cd frontend
vercel --prod
```

Set `VITE_API_URL` to your Railway backend URL in Vercel project settings.

---

## Notes

- The ML model trains on first API request (~30s). Subsequent requests are instant thanks to `lru_cache`.
- All World Cup matches are treated as neutral ground (`neutral=True`).
- Group stage picks are persisted to `localStorage` so your bracket survives page refreshes.
