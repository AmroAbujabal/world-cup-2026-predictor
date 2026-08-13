# Handoff — World Cup 2026 Predictor: tournament finished, app closed out

## Goal

The 2026 World Cup ended on 19 July 2026 (Spain 1–0 Argentina). Bring the app to its finished
state: heal the bracket data, present the tournament as complete rather than live, score the
model against the real results, and clean out what the end of the tournament made dead.

## Current State

- **Bracket data is correct.** All 31 knockout slots are `final`. The one stale row (id 24,
  Switzerland–Colombia, stuck on `live 0–0` since early July) was a sync bug, now fixed —
  it records as 0–0 with a 4–3 shootout to Switzerland.
- **Model scorecard is live**: `GET /model-performance` → 26/31 correct (83.9%), Brier 0.3665,
  by round R32 14/16 · R16 6/8 · QF 4/4 · SF 2/2 · Final 0/1. It called the final for Argentina
  at 43%. Computed from the probabilities stored before the result was recorded.
- **Frontend shows the finished tournament**: champion hero + banner, AI report card with every
  miss, entries-closed panel, real champion in the champion slot, final standings on the
  leaderboard with the model scored on the players' 3-points scale.
- **Tests: 50 passed** (was 45 passed / 5 failed). Lint and build clean.
- Sync cron is off (`workflow_dispatch` only); the in-process poller is inert past its window.

## Active Files

- Backend: `backend/services/sync_service.py` (the fix), `backend/routes/users.py`
  (`/model-performance`), `backend/model/backtest.py` (unpack fix)
- Tests: `tests/test_sync.py` (new), `tests/test_features.py`, `tests/test_train.py`
- Frontend: `src/pages/{BracketChallenge,Leaderboard,Analysis,MyPredictions}.jsx`,
  `src/components/{MatchupCard,Banner}.jsx`, `src/api/client.js`, `src/App.jsx`
- Ops/docs: `.github/workflows/sync.yml`, `CLAUDE.md`, `README.md`

## Changes Made

1. **Sync fix (root cause of the stuck match).** `sync_matches()` decided "already recorded" from
   `is_locked`; a match that was live at 0–0 and finished 0–0 on penalties matched that test and was
   skipped on every sync forever. Now it compares `status == "final"`, and an `IN_PLAY` payload can
   no longer downgrade a recorded result (the provider flipped FINISHED→IN_PLAY→FINISHED on 2 Aug).
   `tests/test_sync.py` covers both; both tests fail on the old code.
2. **`GET /model-performance`** — accuracy, Brier, per-stage tally, every miss, champion. Consumed by
   the bracket report card, the leaderboard AI row and the analysis page; no hardcoded accuracy left.
3. **Bracket page**: champion hero/banner/slot, entries-closed panel, report card replacing the stale
   "Predicted Round of 16" simulation, W/D/L bar kept on finished cards.
4. **Leaderboard**: final standings, pool winner in the subhead, AI row on the same points scale
   (78 pts, 26/31) with a footnote on why the comparison isn't strictly like-for-like.
5. **Analysis**: new §6 "2026 World Cup: How It Actually Did" (stats, per-round, every miss, sample-size
   caveat), sections renumbered, live/future-tense copy moved to past tense.
6. **Cleanup**: cron schedule removed; `GroupStage.jsx` + `data/wc2026.js` deleted (unrouted,
   lint-failing) and BracketChallenge's dead localStorage/router-state path with them; fixed the
   `build_features` 3-tuple unpack in `backtest.py` (real source bug — the backtest module had been
   broken since the signature changed) and in two test files; CLAUDE.md + README rewritten to the
   finished state.

## Failed Attempts / Gotchas

- `POST /admin/sync` with the local `.env` `ADMIN_TOKEN` returns 403 — the Render env has a
  different token. The live DB heals via the GitHub Actions workflow instead (`gh workflow run
sync-results`), which carries the right secret.
- Playwright MCP screenshots did not land on disk in this environment; the accessibility snapshots
  under `~/.playwright-mcp/*.yml` were used for verification instead, which was sufficient.
- Snapshots taken immediately after `browser_navigate` catch the pages mid-fetch ("Loading…") —
  wait for a known string before reading them.
- To preview the finished UI locally, `scripts`-free mirror script copied prod `/matches` into
  `dev.db` (scratchpad, not committed); `dev.db` is gitignored so this is safe but it leaves local
  data that no longer matches prod.

## Next steps

- After the Render deploy lands, run `gh workflow run sync-results` and confirm match 24 flips to
  `final` in prod (`GET /matches`) and `/model-performance` reports 31 matches.
- Redeploy the frontend (`cd frontend && vercel --prod`) — Vite bakes `VITE_API_URL` at build time.
- Optional tidy-ups: migrate `@app.on_event("startup")` to a lifespan handler; add the third-place
  playoff as a 32nd slot if the bracket should be strictly complete; make the older tests roll back
  like `tests/test_sync.py` so `dev.db` stops collecting fixture rows.
- Portfolio (`~/portfolio`, `src/data/content.ts`) still owes an update with this project's finished
  screenshots and the 26/31 result.
