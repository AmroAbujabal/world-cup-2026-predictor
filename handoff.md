# Handoff — World Cup 2026 Predictor: Round of 16 update

## Goal

Advance the app from "R32 complete" to "R16 underway" against the **real FIFA/CBS bracket**: seed R16
fixtures + results, correct the faked R32 penalty scorelines, score user predictions, generate/store R16
model probabilities, add the backend endpoints and frontend UI for it, and elevate the UI (no "AI slop").

## Current State

- **Backend done & verified.** New nullable `Match` columns (penalties, extra-time, upset, prob_home/draw/away)
  added via `_migrate_db()`. Scoring centralized in `services/scoring.py`; `results_csv.py` appends to the
  training CSV. `/admin/update-result` is now atomic (save → csv append → score → leaderboard → cache clear).
  New `GET /matches/round?round=R16` and `GET /user/{username}/predictions`. Leaderboard exposes
  `total_predictions`. Poller has a final-match clobber guard. Name-alias fix (USA/Curacao) in `predict.py`.
  Relevant tests green: **16 passed** (test_db, test_main, test_predict).
- **Data seeded** via `scripts/seed_r16.py` (idempotent): R32 penalty ties fixed to 1–1 + shootout (ids 3,4,14);
  R16 ids 17–24 seeded (17–20 final incl. Norway 2–0 Brazil upset, England 3–2 Mexico; 21–24 upcoming with AI
  probs); 20 knockout rows appended to results.csv; all user scores rebuilt from scratch.
- **Frontend done & builds clean.** Broadcast-scorecard theme (Barlow Condensed + Instrument Sans self-hosted).
  MatchupCard: upcoming/kickoff/LOCKED states, 3-way W/D/L bar, penalty scoreline "(x–y pens)", upset badge.
  BracketChallenge auto-advances real winners across all rounds. Leaderboard: Correct/Total + AI baseline row.
  New MyPredictions page + route + nav. Reusable Badge/Banner components. Canada elimination banner.

## Active Files

- Backend: `backend/db/models.py`, `backend/main.py`, `backend/schemas.py`, `backend/routes/{admin,users,predictions}.py`,
  `backend/services/{scoring,results_csv,poller}.py`, `backend/model/predict.py`
- Scripts: `scripts/seed_r16.py` (new), `scripts/seed_wc2026.py` (scorer centralized)
- Frontend: `src/components/{MatchupCard,Badge,Banner}.jsx`, `src/pages/{BracketChallenge,Leaderboard,MyPredictions}.jsx`,
  `src/App.jsx`, `src/api/client.js`, `src/main.jsx`, `src/index.css`, `tailwind.config.js`

## Changes Made

See CLAUDE.md (updated) for the full API/column/route reference. Highlights: migration + 8 new columns;
scoring service; atomic admin flow; 2 new endpoints; penalty-as-draw policy; R16 seed script; full frontend R16 UI.

**UI redesign v2 ("NBA-champions-predictor" energy, WC themed):** Russo One (display) + Chakra Petch (body)
via @fontsource; WC palette (pitch green / gold / electric blue) as Tailwind tokens + `pitch-bg`/`pitch-deep`
glow backgrounds; bold pitch nav, "ROAD TO THE FINAL" hero, block-style MatchupCards (Russo One scorelines,
3-way W/D/L bars, UPSET pills, live shimmer). Direction from the ui-ux-pro-max skill. Verified via
headless-Chrome screenshots; builds + lints clean.

**Fixes this session:** (a) `database.py` anchors the default SQLite path to the repo root — leaderboard
"not working" was launching uvicorn from `~` (must run from repo root; `backend` isn't importable elsewhere).
(b) `applyLiveData` won't let winner-propagation reorder DB-authoritative R16 teams (`dbFilled` guard).
(c) UPSET badge un-clipped (outer non-overflow wrapper). (d) QF/SF/Final placeholder dates were in the past
→ locked the bracket; bumped to Jul 10–19 in DB + `seed_r16.py::normalize_future_rounds`. (e) Removed
pytest junk users/matches (`scorer_test_*`, `pk_*`, `Test Cup`) from dev.db.

## Failed Attempts / Gotchas

- A background `pytest | tail` reported exit 0 (tail's code) while pytest actually had **pre-existing** failures
  in `test_features/test_backtest/test_train` — those tests do `X, y = build_features()` but it returns a 3-tuple.
  **Not caused by this work**; left as-is (out of scope). One pre-existing lint error in the orphaned `GroupStage.jsx`.
- A `git stash` during a diagnostic pytest got killed by a 2-min timeout before `stash pop` ran, briefly reverting
  the tree — restored with `git stash pop`. (Don't wrap long pytest in a chained stash.)
- Seed `append_csv` initially missed the R16 finals because the session doesn't autoflush before the query — fixed
  with an explicit `db.flush()`.

## Next steps

- Manual end-to-end check with backend + frontend running (see Verification in the plan file).
- Commit the work (feature branch; user prefers pushing to main, no PR).
- Update the portfolio (`~/portfolio`, `src/data/content.ts`) with this AI work.
- When R16 ids 21–24 finish, re-run `scripts/seed_r16.py` (add their scores to the R16 table first) or post via
  `/admin/update-result`. Consider migrating the poller off deprecated `@app.on_event("startup")` to lifespan.
- Optionally fix the pre-existing `build_features` unpack in the model-pipeline tests.
