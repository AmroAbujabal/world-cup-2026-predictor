# World Cup 2026 Predictor — Claude Context

## Stack

- **Backend:** FastAPI + SQLAlchemy (SQLite) + XGBoost, Python 3.12
- **Frontend:** React 18 + Vite + Tailwind CSS v3 + React Router v6 + axios
- **Deploy:** Render (backend), Neon (Postgres), Vercel (frontend)

## Running locally

```bash
# Backend — from repo root
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev -- --port 5200
# (5173 may be occupied by another project)
```

## Deployment (free stack — migrated off Railway when its trial expired, Jul 2026)

- **Frontend:** Vercel — **https://worldcup.amrabujabal.com** (also still on
  https://frontend-nine-alpha-56.vercel.app). `cd frontend && vercel --prod`.
  `VITE_API_URL` (prod env) points at the Render backend; Vite bakes it at build → redeploy after changing.
  Adding a domain is only half the job: the origin must go into `ALLOWED_ORIGINS` in main.py too, or
  the page renders and every fetch is blocked (the bracket then silently shows its seed fixtures).
- **Backend:** Render free web service — https://wc2026-predictor-api-5qvg.onrender.com
  (Blueprint `render.yaml`; auto-deploys on push to main). Free tier sleeps after ~15 min idle (cold start
  ~40–60s + model retrain), so `.github/workflows/keepalive.yml` pings `/health` every 10 min to hold it
  awake — that costs ~730 of the 750 free instance-hours/month, so no second free service fits.
  Env: `DATABASE_URL` (Neon), `FOOTBALL_DATA_API_KEY`, `ADMIN_TOKEN`.
- **Database:** Neon free Postgres (persistent). App normalizes `postgres://`→`postgresql://` and strips
  whitespace from `DATABASE_URL` (a trailing space breaks psycopg2 sslmode).
- **Auto-updates:** `.github/workflows/sync.yml` → `POST /admin/sync` (X-Admin-Token = GitHub secret
  `ADMIN_TOKEN`; also secret `BACKEND_URL`). It ran on a 10-min cron through the tournament; the
  schedule is now off and it is `workflow_dispatch`-only. `sync_service.run_sync()` pulls the whole
  bracket from football-data.org and upserts everything — there is no manual score entry.
- Old Railway URL (dead): world-cup-2026-predictor-production.up.railway.app

## Tournament state — FINISHED (19 Jul 2026)

- All 31 knockout slots are `final`. **Spain beat Argentina 1–0 in the final.**
  Semi-finals: Spain 2–0 France, Argentina 2–1 England.
- Penalty ties (stored at their level score, so they score as draws): id 1 Germany–Paraguay
  1–1 (3–4p), id 4 Netherlands–Morocco 1–1 (2–3p), id 14 Australia–Egypt 1–1 (2–4p),
  id 24 Switzerland–Colombia 0–0 (4–3p).
- Model went 26/31 — exposed via `GET /model-performance`, computed from the `prob_home/draw/away`
  columns. The sync prices a fixture when its teams are known and no longer overwrites those
  probabilities once the result lands (it only fills them if the match was never seen unfinished),
  so stored odds never trail a result.
- The GitHub Actions sync cron is **disabled** (schedule removed, `workflow_dispatch` kept).
  Re-run it by hand if football-data.org ever amends a result.
- The third-place playoff (France 4–6 England, 18 Jul, fd id 537389) is DB slot **32**, added by
  `_ensure_third_place()` in main.py and filled by the sync's `THIRD_PLACE` stage. It sits outside
  the 31-match bracket: nobody predicted it, so `/model-performance` still filters `id <= 31` and
  the leaderboard denominators stay at 31. The model had France at 59% and got it wrong.

## Architecture notes

- Model trains once on first API request (~30s), cached via `lru_cache(maxsize=1)` in `backend/routes/predictions.py`
- All WC matches use `neutral=True`
- Submitted bracket username stored in `localStorage` key `wc2026_bracket_submission`
- CORS uses regex pattern match for all `*.vercel.app` preview URLs plus the custom domain
  (DynamicCORSMiddleware in main.py); `tests/test_cors.py` pins what's in and what stays out
- 31 WC knockout matches seeded in DB on first startup (`_seed_matches()` in main.py), IDs 1–31,
  plus slot 32 (third-place playoff) topped up idempotently by `_ensure_third_place()` — that one
  runs on every boot because `_seed_matches()` only fires on an empty table.
  - R32 slots 1–16 are updated with real fixtures by `scripts/seed_wc2026.py`
- `sync_matches()` decides "already recorded" on `status == "final"`, NOT `is_locked` — a live 0–0
  that ends 0–0 on penalties is still an unrecorded result, and a provider flipping
  FINISHED→IN_PLAY→FINISHED must not re-skip it (this stranded match 24 on `live` for weeks).
  Regression covered by `tests/test_sync.py`.
- `/user/predict` is an upsert — re-submitting updates the prediction rather than erroring
- Poller runs every 5 min during the tournament window (Jun 28–Jul 19 2026) if FOOTBALL_DATA_API_KEY
  is set — that window has passed, so it is now inert
- Match.external_id links DB records to football-data.org match IDs for the poller

## Env vars

```
FOOTBALL_DATA_API_KEY=<football-data.org key>  # enables auto-polling
ADMIN_TOKEN=<secret>                             # protects /admin/* endpoints
DATABASE_URL=sqlite:///./dev.db                  # default
```

## Data model additions (Match)

- Penalty/upset: `went_to_penalties`, `penalty_home`, `penalty_away`, `went_to_extra_time`, `is_upset`
- Stored model probabilities: `prob_home`, `prob_draw`, `prob_away`
- All nullable; added idempotently in `_migrate_db()` (main.py) — no Alembic.
- **Penalty policy:** penalty ties are stored as their level 1–1 score, so predictions score as a
  DRAW; `penalty_home/away` only advance the bracket + drive the "(x–y pens)" display.

## Scoring

- Single source of truth: `backend/services/scoring.py::score_match(db, match, home, away, ...)`.
  Called by `/admin/update-result`, `/results`, the poller, and the seed scripts (no duplication).
- `backend/services/results_csv.py::append_result(...)` appends finished results to results.csv
  (canonical names via CSV_NAME_MAP, deduped by date+teams) for the ELO/form retrain.

## Admin endpoints (require X-Admin-Token header)

- `POST /admin/update-result` — body: `{match_id, home_score, away_score, penalty_home?, penalty_away?, went_to_extra_time?}`
  — atomic: score save → append to results.csv → score predictions → leaderboard → clear model cache
- `POST /admin/set-live` — body: `{match_id}` — marks a match as live
- `POST /admin/retrain` — clears model cache so it retrains on next /predict call

## Public API endpoints (predictions/users routers)

- `GET /matches` — all knockout fixtures (incl. probs, penalties, is_upset)
- `GET /matches/round?round=R16` — fixtures for one stage (R32|R16|QF|SF|Final)
- `GET /user/{username}/predictions` — a user's picks vs actual result + points (feeds "My Predictions")
- `GET /leaderboard` — entries include `total_predictions` (for Correct/Total + AI-accuracy compare)
- `GET /model-performance` — model vs actual: accuracy, Brier score, per-stage tally, every miss,
  and the champion. Computed from stored pre-kickoff probs; feeds the bracket report card,
  the Leaderboard AI row and the Analysis results section.

## Routes (frontend)

- `/` — Analysis (ML research write-up, landing page); `/analysis` redirects to `/`.
- `/bracket` — BracketChallenge (finished knockout bracket + AI report card); `/groups` redirects to it
- `/my-predictions` — MyPredictions (per-user picks vs results)
- `/leaderboard` — Leaderboard
- GroupStage.jsx and `data/wc2026.js` were deleted (unrouted + lint-failing after the tournament ended);
  BracketChallenge now seeds its first paint from its own INITIAL_R32 and lets the DB overlay the rest.
- UI: broadcast-scorecard theme — Barlow Condensed (display) + Instrument Sans (body) via @fontsource;
  green (home) / slate (draw) / sky (away) 3-way probability bars; cards lock at kickoff/live.

## Key files

- `backend/model/predict.py` — PredictorService, feature engineering, XGBoost training
- `backend/routes/predictions.py` — /predict, /matches, /group-standings, /bracket-predictions, /user/predict
- `backend/routes/users.py` — /leaderboard, /results, /model-performance, /user/*/predictions
- `backend/routes/admin.py` — /admin/update-result, /admin/set-live, /admin/retrain
- `backend/services/football_data.py` — football-data.org API client (sync + async, name normalization)
- `backend/services/poller.py` — asyncio polling task (every 5 min during tournament)
- `backend/services/sync_service.py` — the self-driving bracket sync (all updates route through it)
- `frontend/src/pages/BracketChallenge.jsx` — finished knockout bracket + ModelReportCard
- `frontend/src/pages/Analysis.jsx` — research write-up incl. the 2026 results section
- `scripts/seed_wc2026.py` — re-runnable seed script (group stage CSV + R32 DB fixtures)
- `scripts/score_result.py` — legacy manual result entry script
- `data/results.csv` — 49,287 historical matches + 72 WC 2026 group stage results

## If a result is amended

```bash
curl -X POST https://wc2026-predictor-api-5qvg.onrender.com/admin/sync -H "X-Admin-Token: <token>"
```

One sync re-reads the whole bracket from football-data.org and fixes teams, scores, statuses,
user points and probabilities. Local seed scripts (`scripts/seed_wc2026.py`, `scripts/seed_r16.py`)
are still there but the sync supersedes them.

## Known leftovers

- Full `pytest` run takes ~5 min — the model-pipeline tests train real XGBoost models.
- `dev.db` is a local mirror and its `external_id`s were never aligned with its team names (the
  mirror script copied teams from `/matches`, which doesn't expose `external_id`). Running a full
  `run_sync()` against it therefore re-homes teams onto their true `external_id` rows and scrambles
  the local bracket. Prod is unaffected — it wrote teams and `external_id` together. Don't
  `run_sync()` against a mirrored dev.db; re-copy it instead.
