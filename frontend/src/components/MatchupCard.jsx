// frontend/src/components/MatchupCard.jsx

function StatusBadge({ status, homeScore, awayScore }) {
  if (status === 'final' && homeScore != null) {
    return (
      <div className="px-3 py-1 bg-slate-100 border-b border-slate-200 flex items-center justify-between text-xs font-bold">
        <span className="text-slate-500">FT</span>
        <span className="text-slate-700">{homeScore} – {awayScore}</span>
      </div>
    );
  }
  if (status === 'live') {
    return (
      <div className="px-3 py-1 bg-green-500 flex items-center gap-1.5 text-xs font-bold text-white">
        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse inline-block" />
        LIVE
      </div>
    );
  }
  return null;
}

export default function MatchupCard({ matchup, onPick, userPick, loadingProbs }) {
  const { id, team1, team2, prob1, prob2, status, homeScore, awayScore } = matchup;
  const isFinal = status === 'final';

  if (!team1 && !team2) return (
    <div className="w-44 bg-white border border-slate-200 rounded-xl p-3 opacity-40 text-center text-xs text-slate-400">
      TBD
    </div>
  );

  return (
    <div className="w-44 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <StatusBadge status={status} homeScore={homeScore} awayScore={awayScore} />

      {[
        { team: team1, prob: prob1, outcome: 'home_win', score: homeScore },
        { team: team2, prob: prob2, outcome: 'away_win', score: awayScore },
      ].map(({ team, prob, outcome, score }, i) => {
        if (!team) return (
          <div key={i} className={`px-3 py-2.5 text-xs text-slate-400 ${i === 0 ? 'border-b border-slate-200' : ''}`}>TBD</div>
        );
        const picked = userPick === team;
        const otherPicked = userPick && userPick !== team;
        const winner = isFinal && ((i === 0 && homeScore > awayScore) || (i === 1 && awayScore > homeScore));
        return (
          <button
            key={i}
            onClick={() => !isFinal && team2 && onPick(id, team, outcome)}
            disabled={isFinal || !team2}
            className={`w-full px-3 py-2.5 text-left transition-all ${isFinal ? 'cursor-default' : 'cursor-pointer'}
              ${i === 0 ? 'border-b border-slate-200' : ''}
              ${winner ? 'bg-amber-50' : picked ? 'bg-green-600 text-white' : otherPicked ? 'bg-slate-50 text-slate-400' : isFinal ? '' : 'hover:bg-green-50 text-slate-700'}
            `}
          >
            <div className="flex items-center justify-between gap-2">
              <span className={`text-sm font-medium truncate ${winner ? 'text-amber-700 font-bold' : ''}`}>
                {team}
              </span>
              <span className={`text-xs font-bold shrink-0 ${
                isFinal ? (winner ? 'text-amber-600' : 'text-slate-300') :
                picked ? 'text-green-100' : 'text-slate-400'
              }`}>
                {isFinal
                  ? (winner ? '✓' : '')
                  : prob != null && !loadingProbs
                    ? `${Math.round(prob * 100)}%`
                    : loadingProbs ? '…' : ''}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
