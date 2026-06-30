"""Seed dummy users with random predictions for leaderboard display."""
import random
import sqlite3
import sys
import os

# Direct DB write to bypass lock checks and hit all matches including finals
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dev.db')

OUTCOMES = ['home_win', 'draw', 'away_win']

USERS = [
    'alice',
    'bob',
    'carlos',
    'diana',
    'ethan',
    'fatima',
    'george',
    'hana',
    'ivan',
    'julia',
]

# Actual results for scoring (match_id → actual outcome)
KNOWN_RESULTS = {
    1: 'away_win',   # South Africa 0–1 Canada
    2: 'home_win',   # Brazil 2–1 Japan
    3: 'away_win',   # Germany 5–6 Paraguay
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch all matches
    cur.execute("SELECT id FROM matches ORDER BY id")
    match_ids = [r[0] for r in cur.fetchall()]
    print(f"Found {len(match_ids)} matches: {match_ids}")

    # Ensure all dummy users exist
    for username in USERS:
        cur.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()

    # Fetch user IDs
    cur.execute("SELECT id, username FROM users WHERE username IN ({})".format(
        ','.join('?' * len(USERS))), USERS)
    user_map = {row[1]: row[0] for row in cur.fetchall()}
    print(f"Users: {user_map}")

    # Insert random predictions for every user × every match
    random.seed(42)
    inserted = 0
    for username, user_id in user_map.items():
        for match_id in match_ids:
            outcome = random.choice(OUTCOMES)
            # Delete existing prediction for this user+match first (upsert)
            cur.execute("DELETE FROM user_predictions WHERE user_id = ? AND match_id = ?", (user_id, match_id))
            cur.execute("""
                INSERT INTO user_predictions (user_id, match_id, predicted_outcome, points_awarded)
                VALUES (?, ?, ?, NULL)
            """, (user_id, match_id, outcome))
            inserted += 1
    conn.commit()
    print(f"Inserted {inserted} predictions")

    # Score predictions for final matches and update user totals
    for match_id, actual in KNOWN_RESULTS.items():
        cur.execute("SELECT id, user_id, predicted_outcome FROM user_predictions WHERE match_id = ?", (match_id,))
        preds = cur.fetchall()
        for pred_id, user_id, predicted in preds:
            points = 3 if predicted == actual else 0
            cur.execute("UPDATE user_predictions SET points_awarded = ? WHERE id = ?", (points, pred_id))
        print(f"Scored match {match_id} ({actual}): {len(preds)} predictions")

    # Update user total_points
    for username, user_id in user_map.items():
        cur.execute("SELECT COALESCE(SUM(points_awarded), 0) FROM user_predictions WHERE user_id = ?", (user_id,))
        total = cur.fetchone()[0]
        cur.execute("UPDATE users SET total_points = ? WHERE id = ?", (total, user_id))
    conn.commit()

    # Print leaderboard preview
    cur.execute("""
        SELECT u.username,
               COALESCE(u.total_points, 0) as total,
               COALESCE(SUM(CASE WHEN p.points_awarded > 0 THEN 1 ELSE 0 END), 0) as correct
        FROM users u
        LEFT JOIN user_predictions p ON p.user_id = u.id
        WHERE u.username IN ({})
        GROUP BY u.id
        ORDER BY total DESC, correct DESC
    """.format(','.join('?' * len(USERS))), USERS)
    print("\nLeaderboard preview:")
    print(f"{'Rank':<5} {'Username':<12} {'Points':>6} {'Correct':>8}")
    for i, (name, pts, correct) in enumerate(cur.fetchall(), 1):
        print(f"{i:<5} {name:<12} {pts:>6} {correct:>8}")

    conn.close()

if __name__ == '__main__':
    main()
