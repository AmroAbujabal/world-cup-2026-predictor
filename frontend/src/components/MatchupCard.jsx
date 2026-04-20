// frontend/src/components/MatchupCard.jsx

export default function MatchupCard({ matchup, onPick, userPick, loadingProbs }) {
  const { id, team1, team2, prob1, prob2 } = matchup;

  if (!team1 && !team2) return (
    <div className="w-44 bg-white border border-slate-200 rounded-xl p-3 opacity-40 text-center text-xs text-slate-400">
      TBD
    </div>
  );

  return (
    <div className="w-44 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {[{ team: team1, prob: prob1, outcome: 'home_win' }, { team: team2, prob: prob2, outcome: 'away_win' }].map(({ team, prob, outcome }, i) => {
        if (!team) return (
          <div key={i} className={`px-3 py-2.5 text-xs text-slate-400 ${i === 0 ? 'border-b border-slate-200' : ''}`}>TBD</div>
        );
        const picked = userPick === team;
        const otherPicked = userPick && userPick !== team;
        return (
          <button
            key={i}
            onClick={() => team2 && onPick(id, team, outcome)}
            disabled={!team2}
            className={`w-full px-3 py-2.5 text-left transition-all cursor-pointer ${i === 0 ? 'border-b border-slate-200' : ''}
              ${picked ? 'bg-green-600 text-white' : otherPicked ? 'bg-slate-50 text-slate-400' : 'hover:bg-green-50 text-slate-700'}
            `}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium truncate">{team}</span>
              {prob != null && !loadingProbs && (
                <span className={`text-xs font-bold shrink-0 ${picked ? 'text-green-100' : 'text-slate-400'}`}>
                  {Math.round(prob * 100)}%
                </span>
              )}
              {loadingProbs && <span className="text-xs text-slate-300">…</span>}
            </div>
          </button>
        );
      })}
    </div>
  );
}
