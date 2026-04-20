# World Cup 2026 Predictor — Claude Context

## Stack

- **Backend:** FastAPI + SQLAlchemy (SQLite) + XGBoost, Python 3.12
- **Frontend:** React 18 + Vite + Tailwind CSS v3 + React Router v6 + axios
- **Deploy:** Railway (backend), Vercel (frontend)

## Running locally

```bash
# Backend — from repo root
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev -- --port 5200
# (5173 may be occupied by another project)
```

## Deployment

```bash
# Backend
railway up --service world-cup-2026-predictor

# Frontend
cd frontend && vercel --prod
```

- Railway URL: https://world-cup-2026-predictor-production.up.railway.app
- Vercel alias: https://frontend-nine-alpha-56.vercel.app
- VITE_API_URL is set in Vercel project env (production + preview)

## Architecture notes

- Model trains once on first API request (~30s), cached via `lru_cache(maxsize=1)` in `backend/routes/predictions.py`
- All WC matches use `neutral=True`
- Group picks are persisted to `localStorage` key `wc2026_group_picks`
- Submitted bracket username stored in `localStorage` key `wc2026_bracket_submission`
- GroupStage (`/`) → navigate('/bracket', { state: { r32 } }) — BracketChallenge also reads localStorage as fallback
- CORS uses regex pattern match for all `*.vercel.app` preview URLs (DynamicCORSMiddleware in main.py)
- 31 WC knockout matches are seeded into DB on first startup (`_seed_matches()` in main.py), IDs 1–31
- `/user/predict` is an upsert — re-submitting updates the prediction rather than erroring
- To score match results after games are played: `python scripts/score_result.py <match_id> <home> <away>`

## Routes

- `/` — GroupStage (landing page / compete flow)
- `/groups` — GroupStage alias
- `/bracket` — BracketChallenge (knockout bracket)
- `/analysis` — Analysis (ML research writeup)
- `/leaderboard` — Leaderboard

## Key files

- `backend/model/predict.py` — PredictorService, feature engineering, XGBoost training
- `backend/routes/predictions.py` — /predict, /group-standings, /bracket-predictions, /user/predict
- `backend/routes/users.py` — /leaderboard, /results
- `frontend/src/data/wc2026.js` — 48 teams, 12 groups, buildR32()
- `frontend/src/pages/GroupStage.jsx` — landing page, group stage picker
- `frontend/src/pages/BracketChallenge.jsx` — knockout bracket challenge
- `scripts/score_result.py` — enter real match results to trigger leaderboard scoring
- `data/results.csv` — 49,287 international matches (1872–2024)
