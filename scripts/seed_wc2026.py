#!/usr/bin/env python3
"""
scripts/seed_wc2026.py

One-time setup for the live tournament phase:
  1. Fetch all WC 2026 group stage results from football-data.org
  2. Fill real scores into the NA rows already in data/results.csv
  3. Save the updated CSV (model retrains on next /predict call with updated ELO/form)
  4. Fetch actual R32 fixtures and update Match records 1–16 in the DB
  5. Score South Africa vs Canada (and any other finished R32 matches)

Usage (from repo root):
  export FOOTBALL_DATA_API_KEY=3ed4966ca2e143c198b8d663b23b6a88
  python scripts/seed_wc2026.py [--dry-run]

  --dry-run   Print what would change, don't write anything.
"""

import os
import sys
import argparse
from datetime import datetime, timezone, date

import httpx
import pandas as pd

# ── Setup sys.path so we can import backend ───────────────────────────────────
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from backend.db.database import SessionLocal
from backend.db.models import Match, User, UserPrediction
from sqlalchemy import text

FDORG_BASE = "https://api.football-data.org/v4"
CSV_PATH = os.path.join(repo_root, "data", "results.csv")

# football-data.org name → our canonical name (matches results.csv & wc2026.js)
NAME_MAP = {
    "Côte d'Ivoire": "Ivory Coast",
    "United States": "USA",
    "Republic of Korea": "South Korea",
    "IR Iran": "Iran",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Bosnia": "Bosnia and Herzegovina",
    "Congo DR": "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "Czechia": "Czech Republic",
    "Curaçao": "Curacao",
    "Cape Verde Islands": "Cape Verde",
    "Cabo Verde": "Cape Verde",
}


def normalize(name: str) -> str:
    return NAME_MAP.get(name, name)


def fetch_wc_matches(stage: str | None = None) -> list[dict]:
    key = os.getenv("FOOTBALL_DATA_API_KEY", "")
    if not key:
        sys.exit("❌  FOOTBALL_DATA_API_KEY not set")
    params: dict = {"season": "2026"}
    if stage:
        params["stage"] = stage
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{FDORG_BASE}/competitions/WC/matches",
            params=params,
            headers={"X-Auth-Token": key},
        )
        r.raise_for_status()
        return r.json()["matches"]


# ── Step 1: Update group stage scores in results.csv ─────────────────────────

def update_csv(matches: list[dict], dry_run: bool) -> int:
    """
    Match football-data.org FINISHED group stage results to the NA rows in results.csv.
    Tries direct match, normalized names, swapped home/away, and ±1 day date variants.
    Returns count of rows updated.
    """
    from datetime import timedelta

    df = pd.read_csv(CSV_PATH)

    # Build lookup: (date_str, home_norm, away_norm) → (home_score, away_score, real_home, real_away)
    # Also store swapped version so we can detect home/away transposition.
    results_lookup: dict = {}
    for m in matches:
        if m.get("stage") != "GROUP_STAGE":
            continue
        if m.get("status") not in ("FINISHED", "AWARDED"):
            continue
        score = m.get("score", {}).get("fullTime", {})
        hs, as_ = score.get("home"), score.get("away")
        if hs is None or as_ is None:
            continue
        utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        home = normalize(m["homeTeam"]["name"])
        away = normalize(m["awayTeam"]["name"])
        # Add the UTC date and adjacent dates to handle timezone edge cases
        for delta in (0, -1, 1):
            d = (utc_dt + timedelta(days=delta)).strftime("%Y-%m-%d")
            results_lookup[(d, home, away)] = (hs, as_)
            # Also add swapped — CSV and football-data.org may disagree on home/away
            results_lookup[(d, away, home)] = (as_, hs)

    print(f"  football-data.org returned {len(results_lookup) // 6} finished group stage matches")

    updated = 0
    for idx, row in df.iterrows():
        if row["tournament"] != "FIFA World Cup":
            continue
        if str(row["date"]) < "2026-01-01":
            continue
        if pd.notna(row["home_score"]):
            continue  # already has a score

        csv_home = str(row["home_team"])
        csv_away = str(row["away_team"])
        csv_date = str(row["date"])[:10]

        # Try: (date, csv_home, csv_away) then with normalized names
        key = (csv_date, csv_home, csv_away)
        if key not in results_lookup:
            key = (csv_date, normalize(csv_home), normalize(csv_away))
        if key not in results_lookup:
            continue

        hs, as_ = results_lookup[key]
        if dry_run:
            print(f"  [dry] {csv_date}  {csv_home} {hs}–{as_} {csv_away}")
        else:
            df.at[idx, "home_score"] = hs
            df.at[idx, "away_score"] = as_
        updated += 1

    if not dry_run and updated > 0:
        df.to_csv(CSV_PATH, index=False)

    return updated


# ── Step 2: Reset R32 fixtures in the DB ─────────────────────────────────────

def seed_r32(matches: list[dict], dry_run: bool) -> int:
    """
    Update Match records 1–16 with actual R32 fixtures in order.
    Also scores any already-FINISHED R32 matches (incl. South Africa vs Canada).
    Returns count of matches updated.
    """
    r32_matches = [m for m in matches if m.get("stage") == "LAST_32"]
    # Sort by utcDate so we process in chronological order
    r32_matches.sort(key=lambda m: m["utcDate"])

    if not r32_matches:
        print("  ⚠️  No LAST_32 matches returned — check if stage filter is correct")
        return 0

    db = SessionLocal()
    updated = 0
    try:
        for slot_id, m in enumerate(r32_matches[:16], start=1):
            home = normalize(m["homeTeam"]["name"])
            away = normalize(m["awayTeam"]["name"])
            utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            ext_id = m["id"]
            fd_status = m.get("status", "SCHEDULED")
            score = m.get("score", {}).get("fullTime", {})
            hs = score.get("home")
            as_ = score.get("away")

            if fd_status in ("FINISHED", "AWARDED"):
                status = "final"
            elif fd_status in ("IN_PLAY", "PAUSED", "HALFTIME"):
                status = "live"
            else:
                status = "upcoming"

            if dry_run:
                print(f"  [dry] Match {slot_id}: {home} vs {away}  {utc_dt.date()}  → {status}", end="")
                if hs is not None:
                    print(f"  {hs}–{as_}", end="")
                print()
                continue

            db_match = db.query(Match).filter(Match.id == slot_id).first()
            if not db_match:
                print(f"  ⚠️  Match ID {slot_id} not found in DB — skipping")
                continue

            db_match.home_team = home
            db_match.away_team = away
            db_match.match_date = utc_dt
            db_match.external_id = ext_id
            db_match.status = status

            if status == "final" and hs is not None:
                db_match.home_score = hs
                db_match.away_score = as_
                db_match.is_locked = True
                _score_predictions(db, db_match, hs, as_)
                print(f"  ✅  Match {slot_id}: {home} {hs}–{as_} {away} (final, scored)")
            else:
                print(f"  📋  Match {slot_id}: {home} vs {away}  [{status}]")

            updated += 1

        if not dry_run:
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return updated


def _score_predictions(db, match, home_score: int, away_score: int):
    from backend.services.scoring import score_match
    actual, scored = score_match(db, match, home_score, away_score)
    if scored:
        print(f"     → scored {scored} predictions (actual: {actual})")


# ── Step 3: Clear model cache ─────────────────────────────────────────────────

def clear_model_cache():
    try:
        from backend.routes.predictions import get_predictor
        get_predictor.cache_clear()
        print("  ✅  Model cache cleared — will retrain on next /predict call")
    except Exception as e:
        print(f"  ⚠️  Could not clear model cache: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed WC 2026 live data")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()
    dry = args.dry_run

    if dry:
        print("🔍  DRY RUN — no changes will be written\n")

    print("1️⃣  Fetching all WC 2026 matches from football-data.org...")
    try:
        all_matches = fetch_wc_matches()
        print(f"   Got {len(all_matches)} total matches\n")
    except httpx.HTTPStatusError as e:
        sys.exit(f"❌  API error {e.response.status_code}: {e.response.text}")

    print("2️⃣  Updating group stage scores in data/results.csv...")
    n_csv = update_csv(all_matches, dry)
    print(f"   Updated {n_csv} rows in results.csv\n")

    print("3️⃣  Seeding actual R32 fixtures into the DB (Match IDs 1–16)...")
    n_r32 = seed_r32(all_matches, dry)
    print(f"   Updated {n_r32} R32 match records\n")

    if not dry:
        print("4️⃣  Clearing model cache (ELO/form will update on next predict request)...")
        clear_model_cache()

    print("\n✅  Done!")
    if not dry:
        print("\nNext steps:")
        print("  • Restart the backend to reload results.csv into the model")
        print("  • Or hit POST /admin/retrain to clear the cache without restarting")
        print("  • Run with --dry-run first if you want to preview changes")


if __name__ == "__main__":
    main()
