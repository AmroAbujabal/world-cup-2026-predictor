// frontend/src/components/ModelReportCard.jsx
const OUTCOME_LABEL = {
  home_win: "home win",
  draw: "draw",
  away_win: "away win",
};

// The model's scorecard: stored pre-kickoff probabilities vs what actually happened.
export default function ModelReportCard({ perf }) {
  if (!perf?.matches_scored) return null;
  const acc = Math.round(perf.accuracy * 100);
  return (
    <div className="max-w-5xl mx-auto mb-8 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-widest text-gold-600 mb-1">
        AI report card
      </p>
      <h2 className="text-lg font-bold text-slate-900 mb-4">
        How the model did against the real results
      </h2>

      <div className="flex flex-wrap gap-6 items-start">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-5xl text-pitch-700 leading-none nums">
            {acc}%
          </span>
          <span className="text-sm text-slate-500 nums">
            {perf.correct}/{perf.matches_scored} calls
          </span>
        </div>
        <div className="flex flex-wrap gap-2 flex-1 min-w-56">
          {perf.by_stage.map((s) => (
            <div
              key={s.stage}
              className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-center min-w-[74px]"
            >
              <div className="font-bold text-slate-900 nums text-sm">
                {s.correct}/{s.total}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">{s.stage}</div>
            </div>
          ))}
        </div>
      </div>

      {perf.misses.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 mb-2">
            Where it got it wrong
          </p>
          <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
            {perf.misses.map((m) => (
              <li
                key={m.match_id}
                className="flex items-baseline justify-between gap-3"
              >
                <span className="text-slate-700 truncate">
                  <span className="text-slate-400 text-xs mr-1.5">
                    {m.stage}
                  </span>
                  {m.home_team} {m.score} {m.away_team}
                  {m.went_to_penalties && (
                    <span className="text-slate-400 text-xs"> (pens)</span>
                  )}
                </span>
                <span className="text-xs text-slate-400 shrink-0 nums">
                  called {OUTCOME_LABEL[m.predicted_outcome]}{" "}
                  {Math.round(m.confidence * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-slate-400 mt-4">
        Probabilities are the ones stored before the result was recorded — no
        hindsight. Penalty ties count as draws. Random guessing scores{" "}
        {Math.round(perf.random_baseline * 100)}%; Brier score{" "}
        {perf.brier_score} (0 = perfect, 2 = maximally wrong).
      </p>
    </div>
  );
}
