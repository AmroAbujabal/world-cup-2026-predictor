# Handoff — World Cup 2026 Predictor: queued follow-ups cleared

## Goal

Work the four follow-ups left when the tournament was closed out: third-place playoff as a
32nd bracket slot, lifespan migration, test rollback hygiene, and the portfolio update. Plus
one raised mid-session: the bracket page's round alignment was visibly broken.

## Current State

Everything below is **shipped and verified in production**.

- **Slot 32 is live.** `GET /matches` returns 32, slot 32 = `3rd Place`, France 4–6 England,
  `is_upset` true, model probs 0.558/0.187/0.255 (it favoured France and got it wrong).
- **Scorecard deliberately unchanged: 26/31, 83.9%, Brier 0.3665.** `/model-performance` still
  filters `id <= 31`. The playoff sits outside the bracket challenge because nobody predicted it,
  so the leaderboard denominators stay at 31 too. This was an explicit call — including it would
  read 26/32 (81.3%) since it's a miss.
- **Bracket layout fixed** (see Changes Made #4) — rounds now line up with their feeders.
- **Lifespan migration done**; the `on_event` deprecation warnings are gone from the test run.
- **pytest no longer writes into `dev.db`.** A full suite run leaves it at 32 matches / 10 users /
  310 predictions.
- Tests **51 passed** (was 50). Frontend lint + build clean.
- Portfolio updated and pushed (`9bf96d0`), deploys GitHub → Vercel.

Commits: `1007ca5` (the three backend/test items), `095c058` (bracket layout), portfolio `9bf96d0`.

## Active Files

- `backend/main.py` — `_ensure_third_place()`, `lifespan` context manager
- `backend/services/sync_service.py` — `STAGE_SLOTS["THIRD_PLACE"]`
- `backend/routes/predictions.py` — `_stage_label()` bound, `STAGE_ID_RANGES["3rd Place"]`
- `backend/routes/users.py` — comment making the `id <= 31` scoping intentional
- `frontend/src/pages/BracketChallenge.jsx` — third-place Banner, bracket layout
- `tests/test_sync.py` (new third-place test), `tests/test_scoring.py`, `tests/test_main.py`
- `~/portfolio/src/data/content.ts`, `~/portfolio/public/projects/world-cup-predictor.png`

## Changes Made

1. **Third-place playoff = slot 32.** `_ensure_third_place()` tops the row up on every boot —
   `_seed_matches()` only fires on an empty table and every deployed DB already had 1–31. Sync
   picks it up via `STAGE_SLOTS["THIRD_PLACE"]`. `_stage_label()` previously returned "Final" for
   anything past 30; it now distinguishes 31 from 32. Rendered as its own `Banner` (reusing the
   existing component) rather than forced into the 5-round pick tree.
2. **Lifespan migration.** Only the poller lived in `@app.on_event("startup")` — `_migrate_db()`
   and `_seed_matches()` run at import — so it moved to an `asynccontextmanager`, no behaviour change.
3. **Test rollback hygiene.** `test_scoring.py` took the rollback fixture from `test_sync.py`.
   `test_main.py`'s `/results` test **must** really commit (the endpoint runs in the app's own
   session and only sees committed rows), so it deletes its rows in a `finally` instead. Purged the
   pre-existing junk (ids 32–37, 14 test users) so the real slot 32 could take id 32.
4. **Bracket layout fix.** Spacing came from `CELL = 82` with `gap = 2^round * CELL - 76`, i.e. it
   assumed a ~76px card. Finished cards are 140–176px (score header, two team rows, probability bar,
   penalty footnote, UPSET badge), so every round drifted further off — the Final's 618px offset
   landed nowhere near the R32 column's real centre (~1170px), and later rounds bunched at the top
   leaving most of the bracket empty. Replaced with height-agnostic CSS: `items-stretch` on the row
   so all columns share R32's height, each card in a `flex-1` wrapper centring it in its share.
   Verified live — QF 1830 = midpoint of R16's 1671/1989; SF 2148 = midpoint of QF's 1830/2466;
   Final 2784 = midpoint of SF's 2148/3421; Champion matches the Final. Net −13 lines.

## Failed Attempts / Gotchas

- **Do not `run_sync()` against a mirrored `dev.db`.** Its `external_id`s were never aligned with its
  team names (the mirror script copied teams from `/matches`, which doesn't expose `external_id`), so
  a full sync re-homes every fixture onto its true `external_id` row and scrambles the local bracket
  — id 1 became "South Africa–Canada 0–1 with penalties". **Prod is unaffected**: it wrote teams and
  `external_id` together, and a prod sync was a clean no-op for 1–31. Restore from a copy instead.
  Now recorded in CLAUDE.md under Known leftovers.
- Playwright MCP screenshots still don't land on disk here. Worked around with a small node script
  using `~/portfolio/node_modules/playwright` — note it resolves modules from the _script's_
  directory, so it has to live inside a repo that has playwright installed.
- Next.js caches optimised images by src path, so replacing `world-cup-predictor.png` in place kept
  serving the old one locally until `rm -rf .next/cache/images`. Vercel builds fresh, so prod was fine.
- The local `.env` `ADMIN_TOKEN` still 403s against Render (unchanged) — heal prod with
  `gh workflow run sync-results`, which carries the right secret. Used it here for slot 32.

## Next steps

Nothing outstanding — all four queued items and the layout fix are shipped and verified.

Optional, if the bracket page gets more attention: it still has no connector lines between rounds.
The geometry is now correct so drawing them is tractable, but it's cosmetic and nobody asked.
