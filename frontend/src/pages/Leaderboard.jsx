// frontend/src/pages/Leaderboard.jsx
import { useEffect, useState } from "react";
import { getLeaderboard } from "../api/client";

const MEDALS = { 1: "🥇", 2: "🥈", 3: "🥉" };
// Model's historical World Cup accuracy (2018: 40.6%, 2022: 39.1%) — the line to beat.
const AI_ACCURACY = 0.4;

const pct = (correct, total) =>
  total > 0 ? Math.round((correct / total) * 100) : null;

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const hasScores = entries.some(
    (e) => e.total_points > 0 || e.total_predictions > 0,
  );

  useEffect(() => {
    getLeaderboard()
      .then(({ data }) => setEntries(data.entries))
      .catch(() =>
        setError("Could not load leaderboard — is the backend running?"),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto reveal">
      <p className="text-xs font-bold uppercase tracking-widest text-pitch-700 mb-1">
        Round of 16 · Live
      </p>
      <h1 className="font-display text-4xl font-bold mb-1 text-slate-900 tracking-tight">
        Leaderboard
      </h1>
      <p className="text-slate-500 mb-6 text-sm">
        Ranked by total points.{" "}
        <span className="text-pitch-700 font-medium">Accuracy</span> is correct
        outcomes out of matches scored — beat the AI's{" "}
        {Math.round(AI_ACCURACY * 100)}%.
      </p>

      {loading && <p className="text-slate-400">Loading…</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {!loading && !error && entries.length === 0 && (
        <div className="bg-white rounded-2xl p-10 border border-slate-200 text-center shadow-sm">
          <p className="text-slate-400">
            No predictions yet — be the first to submit a bracket!
          </p>
        </div>
      )}

      {entries.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 text-[11px] uppercase tracking-widest bg-slate-50">
                  <th className="px-5 py-3 text-left font-bold">Rank</th>
                  <th className="px-5 py-3 text-left font-bold">Player</th>
                  <th className="px-5 py-3 text-right font-bold">Points</th>
                  <th className="px-5 py-3 text-right font-bold">Correct</th>
                  <th className="px-5 py-3 text-right font-bold">Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const acc = pct(
                    entry.correct_predictions,
                    entry.total_predictions,
                  );
                  const beatsAI = acc != null && acc / 100 >= AI_ACCURACY;
                  return (
                    <tr
                      key={entry.rank}
                      className="border-b border-slate-100 hover:bg-pitch-50/50 transition-colors"
                    >
                      <td className="px-5 py-4 text-slate-500 font-display text-base">
                        {MEDALS[entry.rank] ?? `#${entry.rank}`}
                      </td>
                      <td className="px-5 py-4 font-semibold text-slate-900 font-display text-base">
                        {entry.username}
                      </td>
                      <td className="px-5 py-4 text-right">
                        {hasScores ? (
                          <span className="text-pitch-700 font-bold nums">
                            {entry.total_points} pts
                          </span>
                        ) : (
                          <span className="text-xs font-semibold text-pitch-700 bg-pitch-100 px-2 py-0.5 rounded-full">
                            Submitted
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-right text-slate-500 nums">
                        {entry.total_predictions > 0
                          ? `${entry.correct_predictions}/${entry.total_predictions}`
                          : "—"}
                      </td>
                      <td className="px-5 py-4 text-right nums">
                        {acc == null ? (
                          <span className="text-slate-300">—</span>
                        ) : (
                          <span
                            className={`font-bold ${beatsAI ? "text-pitch-700" : "text-slate-500"}`}
                          >
                            {acc}%
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {/* AI baseline — the model users are competing against */}
                <tr className="bg-pitch-50/70 border-t-2 border-pitch-200">
                  <td className="px-5 py-4 text-pitch-600 font-display text-base">
                    AI
                  </td>
                  <td className="px-5 py-4 font-semibold text-pitch-800 font-display text-base flex items-center gap-2">
                    XGBoost model
                    <span className="text-[9px] font-bold uppercase tracking-widest bg-pitch-100 text-pitch-700 px-1.5 py-0.5 rounded-full">
                      baseline
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right text-pitch-400 text-xs">
                    —
                  </td>
                  <td className="px-5 py-4 text-right text-pitch-400 text-xs">
                    historical
                  </td>
                  <td className="px-5 py-4 text-right nums font-bold text-pitch-700">
                    {Math.round(AI_ACCURACY * 100)}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
