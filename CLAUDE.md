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
# Backend — set FOOTBALL_DATA_API_KEY and ADMIN_TOKEN in Railway env vars first
railway up --service world-cup-2026-predictor

# Frontend
cd frontend && vercel --prod
```

- Railway URL: https://world-cup-2026-predictor-production.up.railway.app
- Vercel alias: https://frontend-nine-alpha-56.vercel.app
- VITE_API_URL is set in Vercel project env (production + preview)

## Tournament state (as of Jun 29 2026)

- Group stage complete (all 72 matches seeded into results.csv)
- R32 in progress: Match 1 (South Africa 0–1 Canada) and Match 2 (Brazil 2–1 Japan) are FINAL
- Match 3 (Germany vs Paraguay) is LIVE
- Matches 4–16 are upcoming

## Architecture notes

- Model trains once on first API request (~30s), cached via `lru_cache(maxsize=1)` in `backend/routes/predictions.py`
- All WC matches use `neutral=True`
- Group picks are persisted to `localStorage` key `wc2026_group_picks`
- Submitted bracket username stored in `localStorage` key `wc2026_bracket_submission`
- GroupStage (`/`) → navigate('/bracket', { state: { r32 } }) — BracketChallenge also reads localStorage as fallback
- CORS uses regex pattern match for all `*.vercel.app` preview URLs (DynamicCORSMiddleware in main.py)
- 31 WC knockout matches seeded in DB on first startup (`_seed_matches()` in main.py), IDs 1–31
  - R32 slots 1–16 are updated with real fixtures by `scripts/seed_wc2026.py`
- `/user/predict` is an upsert — re-submitting updates the prediction rather than erroring
- Poller runs every 5 min during tournament window (Jun 28–Jul 19) if FOOTBALL_DATA_API_KEY is set
- Match.external_id links DB records to football-data.org match IDs for the poller

## Env vars

```
FOOTBALL_DATA_API_KEY=<football-data.org key>  # enables auto-polling
ADMIN_TOKEN=<secret>                             # protects /admin/* endpoints
DATABASE_URL=sqlite:///./dev.db                  # default
```

## Admin endpoints (require X-Admin-Token header)

- `POST /admin/update-result` — body: `{match_id, home_score, away_score}` — scores predictions, marks match final
- `POST /admin/set-live` — body: `{match_id}` — marks a match as live
- `POST /admin/retrain` — clears model cache so it retrains on next /predict call

## Routes

- `/` — GroupStage (landing page / compete flow)
- `/groups` — GroupStage alias
- `/bracket` — BracketChallenge (knockout bracket with live scores)
- `/analysis` — Analysis (ML research writeup)
- `/leaderboard` — Leaderboard

## Key files

- `backend/model/predict.py` — PredictorService, feature engineering, XGBoost training
- `backend/routes/predictions.py` — /predict, /matches, /group-standings, /bracket-predictions, /user/predict
- `backend/routes/users.py` — /leaderboard, /results
- `backend/routes/admin.py` — /admin/update-result, /admin/set-live, /admin/retrain
- `backend/services/football_data.py` — football-data.org API client (sync + async, name normalization)
- `backend/services/poller.py` — asyncio polling task (every 5 min during tournament)
- `frontend/src/data/wc2026.js` — 48 teams, 12 groups, buildR32()
- `frontend/src/pages/GroupStage.jsx` — landing page, group stage picker
- `frontend/src/pages/BracketChallenge.jsx` — knockout bracket with live status + scores
- `scripts/seed_wc2026.py` — re-runnable seed script (group stage CSV + R32 DB fixtures)
- `scripts/score_result.py` — legacy manual result entry script
- `data/results.csv` — 49,287 historical matches + 72 WC 2026 group stage results

## Re-seeding after more R32 results come in

```bash
# After more R32 results are published by football-data.org:
FOOTBALL_DATA_API_KEY=... python scripts/seed_wc2026.py

# Then clear the model cache:
curl -X POST https://<railway-url>/admin/retrain -H "X-Admin-Token: <token>"
```
