# FIFA World Cup 2026 Predictor

A full-stack machine learning app tracking the live 2026 FIFA World Cup. The Round of 32 is underway — watch the AI's bracket predictions update in real time as results come in, and track your own picks on the leaderboard.

**Live app:** https://frontend-nine-alpha-56.vercel.app

---

## Tournament State (as of Jun 29 2026)

- Group stage complete (all 72 matches seeded)
- R32 in progress: South Africa 0–1 Canada (FT), Brazil 2–1 Japan (FT), Germany vs Paraguay (LIVE)
- 13 R32 matches still upcoming

---

## Features

- **Live Bracket** — Official FIFA WC 2026 R32 → R16 → QF → SF → Final bracket. Live scores and status (LIVE / FT) auto-update every 60s from the backend.
- **AI Predictions** — XGBoost classifier with ELO ratings, recent form, and H2H features predicts every remaining match. Knockout probabilities are renormalized (no draw) for bracket simulation.
- **Analysis Page** — Research write-up covering data pipeline, model architecture, feature engineering, and backtest results vs 2018/2022 World Cups.
- **Leaderboard** — Submit your bracket and track prediction points as real results come in.
- **Admin Endpoints** — Mark matches live/final, update scores, retrain the model — all protected by an admin token.
- **Auto-Polling** — Backend polls football-data.org every 5 minutes during the tournament window (Jun 28–Jul 19) to automatically update scores and score predictions.

---

## Tech Stack

| Layer | Tech |
|---|---|
| ML Model | XGBoost, pandas, scikit-learn |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | React 18, Vite, Tailwind CSS v3, React Router |
| Live Data | football-data.org API |
| Deployment | Railway (backend), Vercel (frontend) |

---

## Model Details

- **Training data:** 49,287 international matches (1872–2024) + 72 WC 2026 group stage results
- **Algorithm:** XGBoost 3-class classifier (home_win / draw / away_win)
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

# Copy and fill env vars
cp .env.example .env

# Start the API server (trains model on first request ~30s)
uvicorn backend.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 5200
```

App at `http://localhost:5200`

### Environment Variables

**Backend** — create `.env` in repo root:
```
FOOTBALL_DATA_API_KEY=<your-football-data.org-key>   # enables auto-polling
ADMIN_TOKEN=<secret>                                   # protects /admin/* endpoints
DATABASE_URL=sqlite:///./dev.db                        # default
```

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
| `GET` | `/matches` | All knockout fixtures with live status + scores |
| `POST` | `/user/predict` | Submit or update a user bracket prediction |
| `GET` | `/leaderboard` | Ranked leaderboard by prediction points |
| `GET` | `/health` | Health check |

### Admin Endpoints (require `X-Admin-Token` header)

| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/update-result` | Body: `{match_id, home_score, away_score}` — scores predictions, marks match final |
| `POST` | `/admin/set-live` | Body: `{match_id}` — marks a match as live |
| `POST` | `/admin/retrain` | Clears model cache so it retrains on next `/predict` call |

---

## Re-seeding after new R32 results

When more R32 results are published by football-data.org:

```bash
# Fetch and seed latest results
FOOTBALL_DATA_API_KEY=... python scripts/seed_wc2026.py

# Clear model cache so it retrains with the new data
curl -X POST https://<railway-url>/admin/retrain -H "X-Admin-Token: <token>"
```

---

## Project Structure

```
world-cup-predictor/
├── backend/
│   ├── main.py              # FastAPI app, startup tasks, CORS
│   ├── model/
│   │   └── predict.py       # PredictorService (XGBoost)
│   ├── routes/
│   │   ├── predictions.py   # /predict, /matches, /bracket-predictions, /user/predict
│   │   ├── users.py         # /leaderboard
│   │   └── admin.py         # /admin/* (protected)
│   ├── services/
│   │   ├── football_data.py # football-data.org API client + name normalization
│   │   └── poller.py        # asyncio background poller (every 5 min)
│   ├── db/
│   │   ├── database.py      # SQLAlchemy engine
│   │   └── models.py        # User, Match, UserPrediction
│   └── schemas.py           # Pydantic request/response models
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── BracketChallenge.jsx # Live knockout bracket (landing page)
│       │   ├── Analysis.jsx         # Research article + AI bracket
│       │   └── Leaderboard.jsx      # User rankings
│       ├── components/
│       │   └── MatchupCard.jsx      # Bracket card with live status badge
│       └── api/
│           └── client.js            # Axios API client
├── scripts/
│   ├── seed_wc2026.py       # Fetch & seed WC 2026 group results + R32 fixtures
│   └── score_result.py      # Legacy manual result entry
├── data/
│   └── results.csv          # 49,287 historical + 72 WC 2026 group stage matches
├── Procfile                 # Railway deploy command
└── .python-version          # Pins Python 3.12 for Railway
```

---

## Deployment

### Backend — Railway

```bash
npm install -g @railway/cli
railway login
railway up --service world-cup-2026-predictor
```

Set `FOOTBALL_DATA_API_KEY`, `ADMIN_TOKEN`, and `DATABASE_URL` in Railway environment variables.

### Frontend — Vercel

```bash
cd frontend
vercel --prod
```

Set `VITE_API_URL` to your Railway backend URL in Vercel project settings.

---

## Notes

- The ML model trains on first API request (~30s). Subsequent predictions are <100ms thanks to `lru_cache`.
- All World Cup matches use `neutral=True`.
- The poller runs every 5 minutes between Jun 28–Jul 19 2026 if `FOOTBALL_DATA_API_KEY` is set.
- `/user/predict` is an upsert — re-submitting updates the prediction rather than erroring.
- Match IDs 1–16 are R32, 17–24 R16, 25–28 QF, 29–30 SF, 31 Final.
