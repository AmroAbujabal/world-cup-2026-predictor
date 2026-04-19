// frontend/src/pages/Leaderboard.jsx
import { useEffect, useState } from 'react';
import { getLeaderboard } from '../api/client';

const MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLeaderboard()
      .then(({ data }) => setEntries(data.entries))
      .catch(() => setError('Could not load leaderboard — is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-1 text-emerald-400">Leaderboard</h1>
      <p className="text-gray-500 mb-8 text-sm">Ranked by total prediction points</p>

      {loading && <p className="text-gray-500">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <div className="bg-gray-900 rounded-2xl p-10 border border-gray-800 text-center">
          <p className="text-gray-500">No predictions yet — be the first to submit a bracket!</p>
        </div>
      )}

      {entries.length > 0 && (
        <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wide">
                <th className="px-6 py-3 text-left">Rank</th>
                <th className="px-6 py-3 text-left">Player</th>
                <th className="px-6 py-3 text-right">Points</th>
                <th className="px-6 py-3 text-right">Correct</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.rank} className="border-b border-gray-800 last:border-0 hover:bg-gray-800/40 transition-colors">
                  <td className="px-6 py-4 text-gray-400 font-medium">{MEDALS[entry.rank] ?? `#${entry.rank}`}</td>
                  <td className="px-6 py-4 font-semibold text-white">{entry.username}</td>
                  <td className="px-6 py-4 text-right text-emerald-400 font-bold">{entry.total_points} pts</td>
                  <td className="px-6 py-4 text-right text-gray-400">{entry.correct_predictions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
