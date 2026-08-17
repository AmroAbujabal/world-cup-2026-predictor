# Handoff — World Cup 2026 Predictor: resume polish (domain, README, keep-alive)

## Goal

Three recruiter-facing asks, none of them about the model:

1. A custom domain — `worldcup.amrabujabal.com` reads better on a resume than the Vercel default.
2. A README with screenshots, model accuracy and the stack — recruiters open the repo first.
3. Stop the Render free tier's cold start making the live demo look broken.

## Current State

All three **shipped and verified in production**.

- **`https://worldcup.amrabujabal.com` is live** and serving real data. The apex is on Vercel-managed
  DNS, so `vercel domains add` created the record and issued the cert with no Namecheap-style step.
  The old `frontend-nine-alpha-56.vercel.app` still resolves.
- **README leads with three production screenshots** (`docs/screenshots/`): the finished bracket, the
  AI report card at 84% / 26-of-31, and the analysis page. All three load from GitHub raw (200).
  Stack table, model details and backtest numbers were already there and are unchanged.
- **The backend no longer sleeps.** `.github/workflows/keepalive.yml` pings `/health` every 10 min.
  Registered as `active` in `gh workflow list`; a manual dispatch ran green in 8s.
- **CORS fixed** — see Failed Attempts, this was the real trap in the domain work.
- **`python3 -m pytest tests/ -q` → 60 passed** (was 51; +9 from the new CORS tests). Slow at 20m42s
  only because other sessions were running their own suites on the same machine.
- Portfolio + CV updated to the new domain and deployed; `curl https://amrabujabal.com` now returns
  `worldcup.amrabujabal.com` and no longer mentions the old host.

Commits: `367208b` (CORS + keep-alive), `0d9d127` (README + screenshots + CLAUDE.md).
Portfolio `e207d53`. Both repos clean and in sync with `origin/main`.

Note: pushing the screenshots needed `git -c http.postBuffer=524288000 push` — the default buffer
gave `RPC failed; HTTP 400` on the ~1.1MB of PNGs.

## Active Files

- `backend/main.py` — `ALLOWED_ORIGINS`
- `tests/test_cors.py` — **new**, pins the allowlist
- `.github/workflows/keepalive.yml` — **new**
- `README.md` — Screenshots section, live link, Deployment notes
- `docs/screenshots/{bracket,report-card,analysis}.png` — **new**
- `CLAUDE.md` — deployment URLs, keep-alive, the CORS rule
- `~/portfolio/src/data/content.ts` (`demoUrl`), `~/portfolio/cv/AmrAbujabal_CV.tex`

## Changes Made

1. **Custom domain.** `vercel domains add worldcup.amrabujabal.com` from `frontend/` — one command,
   because `amrabujabal.com` sits on Vercel nameservers. Live within seconds.
2. **CORS allowlist.** Added the origin to `ALLOWED_ORIGINS` (see Failed Attempts for why this was
   not optional) and added `tests/test_cors.py` covering both directions: every deployed origin is
   allowed, and suffix (`...amrabujabal.com.evil.test`), sibling-subdomain (`evil-worldcup...`),
   plaintext-http and apex origins stay rejected. The allowlist is a trust boundary, so it gets a
   test rather than a comment.
3. **Keep-alive.** 10-minute cron on `/health`, `--max-time 90 --retry 2` so a wake-up that does
   happen is waited out rather than failing the run. Chosen over Render Starter ($7/mo) — the user
   took the free option knowing the two ceilings, both recorded in the workflow header and the
   README: GitHub disables scheduled workflows after 60 days of repo inactivity, and holding the
   service awake costs ~730 of Render's 750 free instance-hours/month, so there is room for exactly
   one always-on free service on this account.
4. **README.** Screenshots section directly under the live link, before the write-up. Deployment
   section now documents the keep-alive and states the CORS rule for any future domain.
5. **Portfolio + CV.** `demoUrl` was still the raw Vercel hostname. The CV bullet now names the live
   bracket the same way the ResNet entry names its write-up (`cv/build.sh` rebuilt the PDF into
   `public/` and `~/Downloads/Resume/`).

## Failed Attempts / Gotchas

- **Adding the domain silently broke the app, and it looked fine.** `ALLOWED_ORIGINS` is an explicit
  regex allowlist, so on the new origin the page rendered perfectly and every fetch was blocked —
  `BracketChallenge` falls back to its own `INITIAL_R32` seed, so the bracket showed a full, plausible
  "UPCOMING / TBD" tree instead of an error. Caught only because the first screenshot pass looked
  wrong. **Any new origin must go into `ALLOWED_ORIGINS` in the same change as the domain.**
- Because of that, the screenshots had to be taken **after** the backend redeployed (~4 min on
  Render). The capture script now waits on `getByText("Spain")` and `"AI report card"`, so it fails
  loudly rather than shipping a fallback screenshot again.
- **Sticky nav paints across tall element screenshots.** The first `bracket.png` had the header
  stamped through its middle and the left edge clipped. Fixed by `addStyleTag({content: "header, nav
{ display: none !important }"})` plus a full-page shot clipped to the grid's document-absolute rect
  with 24px padding — element screenshots can't add bleed.
- Playwright still isn't installed in this repo; the capture script lives in the scratchpad but must
  be run with cwd `~/portfolio` and an absolute import path, since it resolves modules from there.
- `git push` of the PNGs failed with `RPC failed; HTTP 400` until `http.postBuffer` was raised.

## Next steps

**Nothing outstanding on the three asks.**

Two things to watch, neither urgent:

- **The keep-alive is the fragile part of this setup.** If the demo ever feels slow again, check the
  Actions tab first — GitHub disables scheduled workflows after 60 days of repo inactivity, and this
  repo is finished, so that clock is running. Re-enabling is one click. Render Starter ($7/mo) is the
  permanent fix if it becomes annoying.
- Standing rule from the previous session still applies: **never reintroduce a card-height constant
  in the bracket page.** Round spacing and connectors are measured and height-agnostic on purpose.
