// frontend/src/components/MatchupCard.jsx

export default function MatchupCard({ matchup, onPick, userPick, loadingProbs }) {
  const { id, team1, team2, prob1, prob2 } = matchup;

  if (!team1 && !team2) return (
    <div className="w-44 bg-gray-900 border border-gray-800 rounded-xl p-3 opacity-40 text-center text-xs text-gray-600">
      TBD
    </div>
  );

  return (
    <div className="w-44 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-lg">
      {[{ team: team1, prob: prob1, outcome: 'home_win' }, { team: team2, prob: prob2, outcome: 'away_win' }].map(({ team, prob, outcome }, i) => {
        if (!team) return (
          <div key={i} className={`px-3 py-2.5 text-xs text-gray-600 ${i === 0 ? 'border-b border-gray-800' : ''}`}>TBD</div>
        );
        const picked = userPick === team;
        const otherPicked = userPick && userPick !== team;
        return (
          <button
            key={i}
            onClick={() => team2 && onPick(id, team, outcome)}
            disabled={!team2}
            className={`w-full px-3 py-2.5 text-left transition-all ${i === 0 ? 'border-b border-gray-800' : ''}
              ${picked ? 'bg-emerald-600 text-white' : otherPicked ? 'bg-gray-900 text-gray-600' : 'hover:bg-gray-800 text-gray-200'}
            `}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium truncate">{team}</span>
              {prob != null && !loadingProbs && (
                <span className={`text-xs font-bold shrink-0 ${picked ? 'text-emerald-200' : 'text-gray-500'}`}>
                  {Math.round(prob * 100)}%
                </span>
              )}
              {loadingProbs && <span className="text-xs text-gray-700">…</span>}
            </div>
          </button>
        );
      })}
    </div>
  );
}
