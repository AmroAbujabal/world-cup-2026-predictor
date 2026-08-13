// frontend/src/pages/Leaderboard.jsx
import { useEffect, useState } from "react";
import { getLeaderboard, getModelPerformance } from "../api/client";

const MEDALS = { 1: "🥇", 2: "🥈", 3: "🥉" };
// Fallback only — the real line to beat comes from /model-performance (2026 results).
const FALLBACK_AI_ACCURACY = 0.4;

const pct = (correct, total) =>
  total > 0 ? Math.round((correct / total) * 100) : null;

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [perf, setPerf] = useState(null);
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
    getModelPerformance()
      .then(({ data }) => setPerf(data))
      .catch(() => {});
  }, []);

  const aiAccuracy = perf?.accuracy ?? FALLBACK_AI_ACCURACY;
  const complete = !!perf?.champion;
  const winner = entries[0];

  return (
    <div className="max-w-3xl mx-auto reveal">
      <p className="text-xs font-bold uppercase tracking-widest text-pitch-700 mb-1">
        {complete ? "World Cup 2026 · Final standings" : "Live"}
      </p>
      <h1 className="font-display text-4xl font-bold mb-1 text-slate-900 tracking-tight">
        Leaderboard
      </h1>
      <p className="text-slate-500 mb-6 text-sm">
        {complete && winner ? (
          <>
            <span className="font-semibold text-slate-900">
              {winner.username}
            </span>{" "}
            wins the pool with {winner.total_points} points.{" "}
          </>
        ) : (
          <>Ranked by total points. </>
        )}
        <span className="text-pitch-700 font-medium">Accuracy</span> is correct
        outcomes out of matches scored — the model finished on{" "}
        {Math.round(aiAccuracy * 100)}%.
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
                  const beatsAI = acc != null && acc / 100 >= aiAccuracy;
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
                      {perf ? "2026 result" : "baseline"}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right text-pitch-700 font-bold text-sm nums">
                    {/* same 3-points-per-correct-outcome scale as the players */}
                    {perf ? `${perf.correct * 3} pts` : "—"}
                  </td>
                  <td className="px-5 py-4 text-right text-pitch-600 text-xs nums">
                    {perf
                      ? `${perf.correct}/${perf.matches_scored}`
                      : "historical"}
                  </td>
                  <td className="px-5 py-4 text-right nums font-bold text-pitch-700">
                    {Math.round(aiAccuracy * 100)}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {perf && (
        <p className="text-xs text-slate-400 mt-4 leading-relaxed">
          Players locked one bracket before the knockouts, so their later-round
          picks could land on teams that never made it. The model re-priced each
          fixture once it was set, using only the odds it held before kickoff.
          Same 3-points-per-correct-outcome scale either way.
        </p>
      )}
    </div>
  );
}
