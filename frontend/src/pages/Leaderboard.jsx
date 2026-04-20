// frontend/src/pages/Leaderboard.jsx
import { useEffect, useState } from 'react';
import { getLeaderboard } from '../api/client';

const MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' };

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const hasScores = entries.some(e => e.total_points > 0);

  useEffect(() => {
    getLeaderboard()
      .then(({ data }) => setEntries(data.entries))
      .catch(() => setError('Could not load leaderboard — is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-1 text-slate-900">Leaderboard</h1>
      <p className="text-slate-500 mb-6 text-sm">Ranked by total prediction points</p>

      {!loading && !error && !hasScores && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-5 py-4 mb-6">
          <span className="text-amber-500 text-lg leading-none mt-0.5">⏳</span>
          <div>
            <p className="text-sm font-semibold text-amber-800">Tournament hasn't started yet</p>
            <p className="text-xs text-amber-700 mt-0.5">Brackets are locked in. Scoring begins when matches are played — June 2026.</p>
          </div>
        </div>
      )}

      {loading && <p className="text-slate-400">Loading…</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <div className="bg-white rounded-2xl p-10 border border-slate-200 text-center shadow-sm">
          <p className="text-slate-400">No predictions yet — be the first to submit a bracket!</p>
        </div>
      )}

      {entries.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 text-xs uppercase tracking-wide bg-slate-50">
                <th className="px-6 py-3 text-left">Rank</th>
                <th className="px-6 py-3 text-left">Player</th>
                <th className="px-6 py-3 text-right">{hasScores ? 'Points' : 'Status'}</th>
                {hasScores && <th className="px-6 py-3 text-right">Correct</th>}
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.rank} className="border-b border-slate-100 last:border-0 hover:bg-green-50/50 transition-colors">
                  <td className="px-6 py-4 text-slate-500 font-medium">{MEDALS[entry.rank] ?? `#${entry.rank}`}</td>
                  <td className="px-6 py-4 font-semibold text-slate-900">{entry.username}</td>
                  <td className="px-6 py-4 text-right">
                    {hasScores
                      ? <span className="text-green-600 font-bold">{entry.total_points} pts</span>
                      : <span className="text-xs font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">Submitted</span>
                    }
                  </td>
                  {hasScores && <td className="px-6 py-4 text-right text-slate-400">{entry.correct_predictions}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
