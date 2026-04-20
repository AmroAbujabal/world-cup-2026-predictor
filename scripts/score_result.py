#!/usr/bin/env python3
"""
Enter a match result and trigger leaderboard scoring.

Usage:
  python scripts/score_result.py <match_id> <home_score> <away_score>

Match IDs:
  R32:   1-16   (in order of BRACKET_R32 in predictions.py)
  R16:   17-24
  QF:    25-28
  SF:    29-30
  Final: 31

Example — Spain beat Egypt 2-0 (match 8):
  python scripts/score_result.py 8 2 0
"""
import os
import sys
import requests

API = os.getenv("API_URL", "https://world-cup-2026-predictor-production.up.railway.app")

if len(sys.argv) != 4:
    print(__doc__)
    sys.exit(1)

match_id, home_score, away_score = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])

r = requests.post(f"{API}/results", json={
    "match_id": match_id,
    "home_score": home_score,
    "away_score": away_score,
})
print(r.status_code, r.json())
