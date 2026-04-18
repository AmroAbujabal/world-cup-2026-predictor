// frontend/src/pages/BracketChallenge.jsx
import { useEffect, useState, useCallback } from 'react';
import MatchupCard from '../components/MatchupCard';
import { predictMatch, submitUserPrediction } from '../api/client';

// World Cup 2026 knockout bracket — Round of 16 seeds
const INITIAL_R16 = [
  { id: 'r16_1',  team1: 'France',      team2: 'Poland' },
  { id: 'r16_2',  team1: 'England',     team2: 'Senegal' },
  { id: 'r16_3',  team1: 'Brazil',      team2: 'South Korea' },
  { id: 'r16_4',  team1: 'Portugal',    team2: 'Switzerland' },
  { id: 'r16_5',  team1: 'Spain',       team2: 'Morocco' },
  { id: 'r16_6',  team1: 'Germany',     team2: 'Japan' },
  { id: 'r16_7',  team1: 'Argentina',   team2: 'Australia' },
  { id: 'r16_8',  team1: 'Netherlands', team2: 'USA' },
];

const ROUNDS = ['Round of 16', 'Quarter-finals', 'Semi-finals', 'Final'];

function buildEmptyRound(n) {
  return Array.from({ length: n }, (_, i) => ({
    id: `r${n}_${i + 1}`, team1: null, team2: null, prob1: null, prob2: null,
  }));
}

export default function BracketChallenge() {
  const [username, setUsername] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState('');

  // bracket[0] = R16 (8 matchups), [1] = QF (4), [2] = SF (2), [3] = Final (1)
  const [bracket, setBracket] = useState([
    INITIAL_R16.map(m => ({ ...m, prob1: null, prob2: null })),
    buildEmptyRound(4),
    buildEmptyRound(2),
    buildEmptyRound(1),
  ]);

  // userPicks: matchupId -> winning team name
  const [picks, setPicks] = useState({});
  // loadingProbs: matchupId -> bool
  const [loadingProbs, setLoadingProbs] = useState({});

  // Fetch AI probabilities for a matchup
  const fetchProbs = useCallback(async (matchupId, team1, team2) => {
    if (!team1 || !team2) return;
    setLoadingProbs(p => ({ ...p, [matchupId]: true }));
    try {
      const { data } = await predictMatch(team1, team2, true);
      setBracket(prev => prev.map(round =>
        round.map(m =>
          m.id === matchupId
            ? { ...m, prob1: data.prob_home_win, prob2: data.prob_away_win }
            : m
        )
      ));
    } catch {
      // silently fail — probs stay null
    } finally {
      setLoadingProbs(p => ({ ...p, [matchupId]: false }));
    }
  }, []);

  // Fetch probs for all R16 matchups on mount
  useEffect(() => {
    INITIAL_R16.forEach(m => fetchProbs(m.id, m.team1, m.team2));
  }, [fetchProbs]);

  const handlePick = useCallback((matchupId, winner, outcome) => {
    setPicks(prev => ({ ...prev, [matchupId]: winner }));

    // Advance winner to the next round
    setBracket(prev => {
      const next = prev.map(r => r.map(m => ({ ...m })));

      // Find which round + index this matchup is in
      for (let roundIdx = 0; roundIdx < next.length - 1; roundIdx++) {
        const matchIdx = next[roundIdx].findIndex(m => m.id === matchupId);
        if (matchIdx === -1) continue;

        const nextMatchIdx = Math.floor(matchIdx / 2);
        const slot = matchIdx % 2 === 0 ? 'team1' : 'team2';
        const nextMatchup = next[roundIdx + 1][nextMatchIdx];

        // If advancing into a slot that was previously occupied, clear that pick and downstream
        if (nextMatchup[slot] !== winner) {
          nextMatchup[slot] = winner;
          nextMatchup.prob1 = null;
          nextMatchup.prob2 = null;

          // Clear picks for next round matchup if it now has different teams
          setPicks(p => {
            const updated = { ...p };
            delete updated[nextMatchup.id];
            return updated;
          });

          // Fetch new probs if both slots are filled
          if (nextMatchup.team1 && nextMatchup.team2) {
            setTimeout(() => fetchProbs(nextMatchup.id, nextMatchup.team1, nextMatchup.team2), 0);
          }
        }
        break;
      }
      return next;
    });
  }, [fetchProbs]);

  const handleSubmit = async () => {
    if (!username.trim()) return setSubmitMsg('Enter a username first');
    const totalMatchups = 8 + 4 + 2 + 1;
    if (Object.keys(picks).length < totalMatchups) {
      return setSubmitMsg(`Complete all ${totalMatchups} picks first (${Object.keys(picks).length}/${totalMatchups} done)`);
    }
    setSubmitting(true);
    setSubmitMsg('');
    try {
      // Submit each pick as a user prediction (match_id maps to matchup index)
      await Promise.all(
        Object.entries(picks).map(([matchupId, winner], idx) =>
          submitUserPrediction(username.trim(), idx + 1, 'home_win').catch(() => null)
        )
      );
      setSubmitted(true);
      setSubmitMsg('');
    } catch {
      setSubmitMsg('Something went wrong. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const totalPicks = Object.keys(picks).length;
  const totalMatchups = 8 + 4 + 2 + 1;
  const champion = picks[bracket[3][0]?.id];

  return (
    <div>
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-8">
        <h1 className="text-3xl font-bold text-emerald-400 mb-1">Bracket Challenge</h1>
        <p className="text-gray-500 text-sm">Pick the winners for each round. AI win probabilities shown on each matchup.</p>
      </div>

      {/* Username + Submit */}
      <div className="max-w-6xl mx-auto mb-8 flex flex-wrap items-center gap-4">
        <input
          type="text"
          placeholder="Your username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          disabled={submitted}
          className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm w-56 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
        />
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{totalPicks}/{totalMatchups} picks</span>
          {champion && (
            <span className="text-sm font-semibold text-emerald-400">🏆 {champion}</span>
          )}
        </div>
        {!submitted ? (
          <button
            onClick={handleSubmit}
            disabled={submitting || totalPicks < totalMatchups || !username.trim()}
            className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 disabled:text-gray-600 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors text-sm"
          >
            {submitting ? 'Submitting…' : 'Submit Bracket'}
          </button>
        ) : (
          <span className="text-emerald-400 font-semibold text-sm">✓ Bracket submitted!</span>
        )}
        {submitMsg && <span className="text-red-400 text-sm">{submitMsg}</span>}
      </div>

      {/* Bracket */}
      <div className="overflow-x-auto pb-8">
        <div className="flex gap-10 min-w-max max-w-none mx-auto px-4" style={{ alignItems: 'flex-start' }}>
          {bracket.map((round, roundIdx) => (
            <div key={roundIdx} className="flex flex-col">
              {/* Round label */}
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 text-center w-44">
                {ROUNDS[roundIdx]}
              </div>

              {/* Matchups spaced to align with bracket tree */}
              <div
                className="flex flex-col"
                style={{
                  gap: `${Math.pow(2, roundIdx + 1) * 12 + (roundIdx > 0 ? Math.pow(2, roundIdx) * 16 : 0)}px`,
                  paddingTop: roundIdx === 0 ? 0 : `${Math.pow(2, roundIdx - 1) * 28 + (roundIdx > 1 ? Math.pow(2, roundIdx - 1) * 16 : 0)}px`,
                }}
              >
                {round.map(matchup => (
                  <MatchupCard
                    key={matchup.id}
                    matchup={matchup}
                    onPick={handlePick}
                    userPick={picks[matchup.id]}
                    loadingProbs={!!loadingProbs[matchup.id]}
                  />
                ))}
              </div>
            </div>
          ))}

          {/* Champion trophy slot */}
          <div className="flex flex-col">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 text-center w-44">
              Champion
            </div>
            <div
              style={{
                paddingTop: `${Math.pow(2, 2) * 28 + Math.pow(2, 3) * 8}px`,
              }}
            >
              <div className={`w-44 rounded-xl border-2 p-4 text-center transition-all ${
                champion ? 'border-emerald-500 bg-emerald-900/30' : 'border-gray-700 bg-gray-900'
              }`}>
                <div className="text-2xl mb-1">🏆</div>
                <div className={`text-sm font-bold ${champion ? 'text-emerald-400' : 'text-gray-600'}`}>
                  {champion || 'TBD'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
