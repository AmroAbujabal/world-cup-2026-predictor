// frontend/src/pages/MyPredictions.jsx
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getUserPredictions } from "../api/client";
import Badge from "../components/Badge";

const SUBMISSION_KEY = "wc2026_bracket_submission";

function savedUsername() {
  try {
    return JSON.parse(localStorage.getItem(SUBMISSION_KEY))?.username || "";
  } catch {
    return "";
  }
}

const outcomeLabel = (outcome, home, away) =>
  outcome === "home_win"
    ? home
    : outcome === "away_win"
      ? away
      : outcome === "draw"
        ? "Draw"
        : "—";

function scoreline(p) {
  if (p.home_score == null) return null;
  const pens =
    p.went_to_penalties && p.penalty_home != null
      ? ` (${p.penalty_home}–${p.penalty_away} pens)`
      : "";
  return `${p.home_score}–${p.away_score}${pens}`;
}

export default function MyPredictions() {
  const [username, setUsername] = useState(savedUsername);
  const [input, setInput] = useState(savedUsername);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchFor = useCallback((name) => {
    if (!name) return;
    setLoading(true);
    setError("");
    getUserPredictions(name)
      .then(({ data }) => setData(data))
      .catch((e) => {
        setData(null);
        setError(
          e?.response?.status === 404
            ? `No predictions found for “${name}”.`
            : "Could not load predictions.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Load on mount / when the looked-up username changes (external data sync).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchFor(username);
  }, [username, fetchFor]);

  const load = (e) => {
    e.preventDefault();
    setUsername(input.trim());
  };

  const preds = data?.predictions || [];
  const scored = preds.filter((p) => p.points_awarded != null);
  const correct = scored.filter((p) => p.points_awarded > 0).length;

  return (
    <div className="max-w-2xl mx-auto reveal">
      <p className="text-xs font-bold uppercase tracking-widest text-green-600 mb-1">
        Round of 16 · Live
      </p>
      <h1 className="font-display text-4xl font-bold mb-1 text-slate-900 tracking-tight">
        My Predictions
      </h1>
      <p className="text-slate-500 mb-6 text-sm">
        Every pick you made, against the real result.
      </p>

      <form onSubmit={load} className="flex items-center gap-2 mb-6">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Your username"
          className="bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-green-500 placeholder:text-slate-400"
        />
        <button
          type="submit"
          className="bg-green-600 hover:bg-green-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors"
        >
          Load
        </button>
      </form>

      {loading && <p className="text-slate-400">Loading…</p>}
      {error && (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center shadow-sm">
          <p className="text-slate-500 text-sm mb-3">{error}</p>
          <Link
            to="/"
            className="text-sm font-bold text-green-700 border border-green-300 hover:bg-green-50 px-4 py-2 rounded-lg transition-colors"
          >
            Make your picks →
          </Link>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Summary */}
          <div className="flex flex-wrap gap-3 mb-6">
            {[
              {
                label: "Total points",
                value: data.total_points,
                tone: "text-green-600",
              },
              {
                label: "Correct",
                value: `${correct}/${scored.length}`,
                tone: "text-slate-900",
              },
              {
                label: "Accuracy",
                value: scored.length
                  ? `${Math.round((correct / scored.length) * 100)}%`
                  : "—",
                tone: "text-sky-600",
              },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-white border border-slate-200 rounded-xl px-5 py-3 text-center shadow-sm min-w-[110px]"
              >
                <div
                  className={`font-display text-2xl font-bold nums ${s.tone}`}
                >
                  {s.value}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 uppercase tracking-widest">
                  {s.label}
                </div>
              </div>
            ))}
          </div>

          {/* Prediction rows */}
          <div className="space-y-2">
            {preds.map((p) => {
              const picked = outcomeLabel(
                p.predicted_outcome,
                p.home_team,
                p.away_team,
              );
              const actual = outcomeLabel(
                p.actual_outcome,
                p.home_team,
                p.away_team,
              );
              const pending = p.actual_outcome == null;
              const correctPick = p.points_awarded > 0;
              return (
                <div
                  key={p.match_id}
                  className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm flex items-center gap-3"
                >
                  <Badge tone="slate">{p.stage}</Badge>
                  <div className="flex-1 min-w-0">
                    <div className="font-display text-[15px] text-slate-900 truncate">
                      {p.home_team} <span className="text-slate-300">v</span>{" "}
                      {p.away_team}
                      {scoreline(p) && (
                        <span className="text-slate-400 text-xs ml-2 nums">
                          {scoreline(p)}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      You picked{" "}
                      <span className="font-semibold text-slate-700">
                        {picked}
                      </span>
                      {!pending && (
                        <>
                          {" "}
                          · result{" "}
                          <span className="font-semibold text-slate-700">
                            {actual}
                          </span>
                        </>
                      )}
                      {p.went_to_penalties && (
                        <span className="text-slate-400"> · pens = draw</span>
                      )}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    {pending ? (
                      <Badge tone="slate">Pending</Badge>
                    ) : correctPick ? (
                      <span className="font-display text-lg font-bold text-green-600 nums">
                        +{p.points_awarded}
                      </span>
                    ) : (
                      <Badge tone="red">Missed</Badge>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {preds.length === 0 && (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center shadow-sm">
              <p className="text-slate-400 text-sm">
                No predictions recorded for this user yet.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
