#!/usr/bin/env python3
"""
scripts/seed_r16.py

Advance the tournament DB to the Round of 16 (state as of 2026-07-06):
  1. Fix the three R32 penalty ties whose scorelines were faked as decisive
     (ids 3, 4, 14) → true 1–1 + penalty shootout; flag extra-time / upset matches.
  2. Seed the 8 R16 fixtures into Match ids 17–24 (4 final, 4 upcoming) with kickoff
     times, statuses, scores, model Win/Draw/Loss probabilities and upset flags.
  3. Append every finished knockout result to data/results.csv (penalty ties as 1–1,
     deduped) so ELO / form update on the next model retrain.
  4. Rebuild all user scores from scratch (so the previously-mis-scored penalty ties
     are corrected) and clear the model cache.

Idempotent — safe to re-run. Usage from repo root:
  python scripts/seed_r16.py [--dry-run]
"""

import os
import sys
import argparse
from datetime import datetime, timezone

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repo_root)

from backend.db.database import SessionLocal
from backend.db.models import Match, User, UserPrediction
from backend.services import results_csv
from backend.services.scoring import score_match

UTC = timezone.utc


# ── R32 penalty / flag corrections (bracket already has the right winners) ────────
# id: (home_score, away_score, penalty_home, penalty_away, went_to_extra_time, is_upset)
R32_FIXES = {
    3:  (1, 1, 3, 4, False, False),   # Germany 1-1 Paraguay   (Paraguay 4-3 pens)
    4:  (1, 1, 2, 3, False, False),   # Netherlands 1-1 Morocco (Morocco 3-2 pens)
    14: (1, 1, 2, 4, False, True),    # Australia 1-1 Egypt     (Egypt 4-2 pens) — upset
    9:  (None, None, None, None, True, False),   # Belgium 3-2 Senegal (AET)
    15: (None, None, None, None, True, True),    # Argentina 3-2 Cape Verde (AET) — upset
}

# ── R16 fixtures, DB ids 17–24 (order per frontend MATCH_ID_MAP r16_1→17 … r16_8→24) ──
# id: dict(home, away, kickoff(UTC), status, home_score, away_score, is_upset,
#          probs=(home, draw, away) | None)
R16 = {
    17: dict(home="France",      away="Paraguay", kickoff=datetime(2026, 7, 4, 22, 0, tzinfo=UTC),
             status="final", home_score=1, away_score=0, is_upset=False, probs=None),
    18: dict(home="Morocco",     away="Canada",   kickoff=datetime(2026, 7, 4, 18, 0, tzinfo=UTC),
             status="final", home_score=3, away_score=0, is_upset=False, probs=None),
    19: dict(home="Brazil",      away="Norway",   kickoff=datetime(2026, 7, 5, 20, 0, tzinfo=UTC),
             status="final", home_score=0, away_score=2, is_upset=True,  probs=(0.54, 0.25, 0.21)),
    20: dict(home="Mexico",      away="England",  kickoff=datetime(2026, 7, 6, 0, 0, tzinfo=UTC),
             status="final", home_score=2, away_score=3, is_upset=False, probs=(0.30, 0.30, 0.40)),
    21: dict(home="Portugal",    away="Spain",    kickoff=datetime(2026, 7, 6, 19, 0, tzinfo=UTC),
             status="upcoming", home_score=None, away_score=None, is_upset=False, probs=(0.24, 0.26, 0.50)),
    22: dict(home="USA",         away="Belgium",  kickoff=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
             status="upcoming", home_score=None, away_score=None, is_upset=False, probs=(0.35, 0.28, 0.37)),
    23: dict(home="Argentina",   away="Egypt",    kickoff=datetime(2026, 7, 7, 16, 0, tzinfo=UTC),
             status="upcoming", home_score=None, away_score=None, is_upset=False, probs=(0.70, 0.19, 0.10)),
    24: dict(home="Switzerland", away="Colombia", kickoff=datetime(2026, 7, 7, 20, 0, tzinfo=UTC),
             status="upcoming", home_score=None, away_score=None, is_upset=False, probs=(0.27, 0.30, 0.43)),
}


# Placeholder kickoff dates for rounds without real fixtures yet (kept in the future
# so the bracket stays pickable — a past date would trip the kickoff lock).
FUTURE_ROUND_DATES = {
    25: datetime(2026, 7, 10, 20, 0, tzinfo=UTC), 26: datetime(2026, 7, 10, 20, 0, tzinfo=UTC),
    27: datetime(2026, 7, 11, 20, 0, tzinfo=UTC), 28: datetime(2026, 7, 11, 20, 0, tzinfo=UTC),
    29: datetime(2026, 7, 14, 20, 0, tzinfo=UTC), 30: datetime(2026, 7, 15, 20, 0, tzinfo=UTC),
    31: datetime(2026, 7, 19, 19, 0, tzinfo=UTC),
}


def normalize_future_rounds(db, dry):
    """Keep QF/SF/Final placeholders in the future so they remain pickable."""
    for mid, dt in FUTURE_ROUND_DATES.items():
        m = db.query(Match).filter(Match.id == mid).first()
        if m and m.status != "final":
            if not dry:
                m.match_date = dt


def _model_probs(home, away):
    """Model 3-way probs, or None if the model can't be built (offline / no data)."""
    try:
        from backend.routes.predictions import get_predictor
        p = get_predictor().predict(home, away, neutral=True)
        return (p.prob_home_win, p.prob_draw, p.prob_away_win)
    except Exception as exc:
        print(f"     ⚠️  model unavailable ({exc}); using seeded probs")
        return None


def fix_r32(db, dry):
    for mid, (hs, as_, ph, pa, aet, upset) in R32_FIXES.items():
        m = db.query(Match).filter(Match.id == mid).first()
        if not m:
            continue
        if hs is not None:
            m.home_score, m.away_score = hs, as_
            m.went_to_penalties = True
            m.penalty_home, m.penalty_away = ph, pa
        if aet:
            m.went_to_extra_time = True
        m.is_upset = upset
        m.is_locked = True
        m.status = "final"
        tag = f" (pens {ph}-{pa})" if hs is not None else ""
        print(f"  {'[dry] ' if dry else ''}R32 id {mid}: {m.home_team} {m.home_score}-{m.away_score} {m.away_team}"
              f"{tag}{' [upset]' if upset else ''}")


def seed_r16(db, dry):
    for mid, r in R16.items():
        m = db.query(Match).filter(Match.id == mid).first()
        if not m:
            print(f"  ⚠️  Match id {mid} missing — run the app once to seed placeholders")
            continue
        m.home_team, m.away_team = r["home"], r["away"]
        m.match_date = r["kickoff"]
        m.status = r["status"]
        m.is_upset = r["is_upset"]
        probs = r["probs"] or _model_probs(r["home"], r["away"])
        if probs:
            m.prob_home, m.prob_draw, m.prob_away = [round(float(x), 3) for x in probs]
        if r["status"] == "final":
            m.home_score, m.away_score = r["home_score"], r["away_score"]
            m.is_locked = True
        print(f"  {'[dry] ' if dry else ''}R16 id {mid}: {r['home']} vs {r['away']}  [{r['status']}]"
              f"{'  ' + str(r['home_score']) + '-' + str(r['away_score']) if r['status']=='final' else ''}"
              f"{' [upset]' if r['is_upset'] else ''}")


def append_csv(db, dry):
    """Append every finished knockout match to results.csv (penalty ties as level 1–1)."""
    written = 0
    db.flush()  # ensure just-seeded R16 scores are visible to this query
    finals = db.query(Match).filter(
        Match.id <= 24, Match.home_score.isnot(None), Match.away_score.isnot(None)
    ).order_by(Match.id).all()
    for m in finals:
        date_str = m.match_date.date().isoformat()
        if dry:
            if not results_csv.row_exists(date_str, results_csv.to_csv_name(m.home_team),
                                          results_csv.to_csv_name(m.away_team)):
                print(f"  [dry] +csv {date_str} {m.home_team} {m.home_score}-{m.away_score} {m.away_team}")
                written += 1
            continue
        if results_csv.append_result(date_str, m.home_team, m.away_team, m.home_score, m.away_score):
            written += 1
    print(f"  {written} knockout row(s) {'would be ' if dry else ''}appended to results.csv")


def rescore(db, dry):
    """Wipe and rebuild all points so corrected penalty ties re-score cleanly (no drift)."""
    if dry:
        n = db.query(UserPrediction).filter(UserPrediction.points_awarded.isnot(None)).count()
        print(f"  [dry] would re-score {n} predictions and rebuild user totals")
        return
    db.query(UserPrediction).update({UserPrediction.points_awarded: None})
    db.query(User).update({User.total_points: 0})
    db.flush()
    finals = db.query(Match).filter(
        Match.home_score.isnot(None), Match.away_score.isnot(None)
    ).all()
    total = 0
    for m in finals:
        _, scored = score_match(
            db, m, m.home_score, m.away_score,
            penalty_home=m.penalty_home, penalty_away=m.penalty_away,
        )
        total += scored
    print(f"  re-scored {total} predictions across {len(finals)} final matches")


def main():
    ap = argparse.ArgumentParser(description="Seed WC 2026 Round of 16")
    ap.add_argument("--dry-run", action="store_true")
    dry = ap.parse_args().dry_run
    if dry:
        print("🔍  DRY RUN — no changes written\n")

    db = SessionLocal()
    try:
        print("1️⃣  Fixing R32 penalty ties / flags...")
        fix_r32(db, dry)
        print("\n2️⃣  Seeding R16 fixtures (ids 17–24)...")
        seed_r16(db, dry)
        normalize_future_rounds(db, dry)
        print("\n3️⃣  Appending knockout results to results.csv...")
        append_csv(db, dry)
        print("\n4️⃣  Rebuilding user scores...")
        rescore(db, dry)
        if not dry:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if not dry:
        try:
            from backend.routes.predictions import get_predictor
            get_predictor.cache_clear()
            print("\n  ✅  Model cache cleared — retrains on next /predict")
        except Exception as exc:
            print(f"\n  ⚠️  Could not clear model cache: {exc}")
    print("\n✅  Done.")


if __name__ == "__main__":
    main()
