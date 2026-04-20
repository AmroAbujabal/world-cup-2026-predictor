// frontend/src/pages/GroupStage.jsx
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { GROUPS, GROUP_LABELS, buildR32 } from '../data/wc2026';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Icons ────────────────────────────────────────────────────────────────────
const CheckIcon = () => (
  <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);
const BoltIcon = () => (
  <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
    <path d="M7 1L2 7h4l-1 4 5-6H6l1-4z"/>
  </svg>
);
const ArrowRightIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
    <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// ── GroupCard ────────────────────────────────────────────────────────────────
function GroupCard({ groupLetter, teams, selections, aiRanking, loading, onToggle, onUseAI }) {
  const isDone = selections.length === 2;

  return (
    <div className={`bg-white rounded-xl p-4 transition-all duration-200 border ${
      isDone ? 'border-green-400 shadow-[0_4px_20px_rgba(22,163,74,0.15)]' : 'border-slate-200 hover:border-green-300'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-baseline gap-1.5">
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-[0.15em]">Group</span>
          <span className="text-2xl font-black text-slate-900 leading-none">{groupLetter}</span>
        </div>
        {isDone ? (
          <span className="flex items-center gap-1 text-[10px] font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
            <CheckIcon /> Done
          </span>
        ) : (
          <span className="text-[10px] font-semibold text-slate-400">{selections.length}/2</span>
        )}
      </div>

      {/* Teams */}
      <div className="flex flex-col gap-1.5 mb-3">
        {teams.map((team) => {
          const rankIdx = selections.indexOf(team);
          const rank = rankIdx + 1;
          const aiPos = aiRanking ? aiRanking.indexOf(team) : -1;
          const isEliminated = isDone && rank === 0;
          const isAISuggested = !isDone && rank === 0 && aiPos >= 0 && aiPos < 2;

          return (
            <button
              key={team}
              onClick={() => !isEliminated && onToggle(groupLetter, team)}
              className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all duration-150 focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:outline-none ${
                rank === 1
                  ? 'bg-green-600 text-white cursor-pointer'
                  : rank === 2
                  ? 'bg-green-50 border border-green-300 text-green-700 cursor-pointer'
                  : isEliminated
                  ? 'opacity-30 cursor-default text-slate-400'
                  : 'bg-slate-50 hover:bg-green-50 text-slate-700 cursor-pointer hover:border hover:border-green-200'
              }`}
            >
              {/* Position circle */}
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${
                rank === 1 ? 'bg-white text-green-700' :
                rank === 2 ? 'bg-green-200 text-green-700' :
                'bg-slate-200 text-slate-400'
              }`}>
                {rank > 0 ? rank : loading ? '·' : aiPos >= 0 ? aiPos + 1 : '·'}
              </span>

              <span className="text-xs font-semibold truncate flex-1">{team}</span>

              {isAISuggested && (
                <span className="text-[9px] font-bold text-amber-500 uppercase tracking-wide shrink-0">AI</span>
              )}
            </button>
          );
        })}
      </div>

      {/* AI button */}
      <button
        onClick={() => onUseAI(groupLetter)}
        disabled={loading || !aiRanking}
        className="w-full flex items-center justify-center gap-1.5 text-[10px] font-bold text-amber-600 uppercase tracking-wider border border-amber-300 hover:bg-amber-50 rounded-lg py-1.5 transition-colors disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:outline-none"
      >
        <BoltIcon />
        {loading ? 'Loading…' : 'AI picks'}
      </button>
    </div>
  );
}

// ── ThirdPlaceCard ───────────────────────────────────────────────────────────
function ThirdPlaceCard({ group, team, selected, disabled, onToggle }) {
  return (
    <button
      onClick={() => !disabled && onToggle(team)}
      className={`px-3 py-3 rounded-xl border text-left transition-all duration-150 focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:outline-none ${
        selected
          ? 'bg-green-600 border-green-500 text-white cursor-pointer shadow-[0_4px_12px_rgba(22,163,74,0.25)]'
          : disabled
          ? 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed opacity-40'
          : 'bg-white border-slate-200 text-slate-700 hover:border-green-300 hover:bg-green-50 cursor-pointer'
      }`}
    >
      <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Group {group}</div>
      <div className="text-xs font-semibold truncate">{team}</div>
    </button>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
const STORAGE_KEY = 'wc2026_group_picks';

function loadSaved() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

export default function GroupStage() {
  const saved = loadSaved();
  const [selections, setSelections] = useState(
    saved?.selections ?? Object.fromEntries(GROUP_LABELS.map(g => [g, []]))
  );
  const [aiRankings, setAiRankings] = useState({});
  const [loadingAI, setLoadingAI] = useState(
    Object.fromEntries(GROUP_LABELS.map(g => [g, false]))
  );
  const [thirdSelected, setThirdSelected] = useState(saved?.thirdSelected ?? []);
  const [warming, setWarming] = useState(false);
  const navigate = useNavigate();

  const fetchGroupAI = useCallback(async (group) => {
    setLoadingAI(p => ({ ...p, [group]: true }));
    try {
      const { data } = await axios.post(`${API}/group-standings`, { teams: GROUPS[group] });
      setAiRankings(p => ({ ...p, [group]: data.standings.map(s => s.team) }));
    } catch {
      // silently fail
    } finally {
      setLoadingAI(p => ({ ...p, [group]: false }));
    }
  }, []);

  // Warm up the model with Group A first, then stagger the rest
  useEffect(() => {
    setWarming(true);
    fetchGroupAI(GROUP_LABELS[0]).then(() => {
      setWarming(false);
      GROUP_LABELS.slice(1).forEach((g, i) => {
        setTimeout(() => fetchGroupAI(g), (i + 1) * 200);
      });
    });
  }, [fetchGroupAI]);

  // Persist picks to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ selections, thirdSelected }));
  }, [selections, thirdSelected]);

  const toggleTeam = (group, team) => {
    setSelections(prev => {
      const cur = prev[group];
      if (cur.includes(team)) return { ...prev, [group]: cur.filter(t => t !== team) };
      if (cur.length < 2) return { ...prev, [group]: [...cur, team] };
      return prev;
    });
  };

  const useAIPicks = (group) => {
    if (!aiRankings[group]) return;
    setSelections(prev => ({ ...prev, [group]: aiRankings[group].slice(0, 2) }));
  };

  const useAllAI = () => {
    const next = {};
    GROUP_LABELS.forEach(g => {
      next[g] = aiRankings[g] ? aiRankings[g].slice(0, 2) : selections[g];
    });
    setSelections(prev => ({ ...prev, ...next }));
  };

  const getThirdPlace = (group) => {
    const sel = selections[group];
    if (sel.length < 2) return null;
    const ranking = aiRankings[group] || GROUPS[group];
    return ranking.find(t => !sel.includes(t)) || null;
  };

  const completedCount = GROUP_LABELS.filter(g => selections[g].length === 2).length;
  const allGroupsDone = completedCount === 12;

  const thirdPlaceTeams = allGroupsDone
    ? GROUP_LABELS.map(g => ({ group: g, team: getThirdPlace(g) })).filter(x => x.team)
    : [];

  const toggleThirdPlace = (team) => {
    setThirdSelected(prev =>
      prev.includes(team)
        ? prev.filter(t => t !== team)
        : prev.length < 8 ? [...prev, team] : prev
    );
  };

  const canBuild = allGroupsDone && thirdSelected.length === 8;

  const handleBuild = () => {
    const groupResults = Object.fromEntries(
      GROUP_LABELS.map(g => [g, { winner: selections[g][0], runnerUp: selections[g][1] }])
    );
    navigate('/bracket', { state: { r32: buildR32(groupResults, thirdSelected) } });
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <p className="text-xs font-bold uppercase tracking-widest text-green-600 mb-1">
          FIFA World Cup 2026 · 48 Teams · 12 Groups
        </p>
        <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Group Stage Predictor</h1>
        <p className="text-slate-500 text-sm max-w-xl">
          Pick the top 2 finishers from each group. AI probabilities are generated by an XGBoost model trained on 49k international matches.
        </p>
      </div>

      {/* Model warm-up notice */}
      {warming && (
        <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5 mb-4">
          <svg className="w-3.5 h-3.5 animate-spin shrink-0" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2" strokeDasharray="28" strokeDashoffset="10"/>
          </svg>
          Warming up AI model — first load takes ~30s, then it's instant
        </div>
      )}

      {/* Progress bar + controls */}
      <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 rounded-xl px-5 py-3 mb-6 shadow-sm">
        <div className="flex-1 min-w-36 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all duration-500"
            style={{ width: `${(completedCount / 12) * 100}%` }}
          />
        </div>
        <span className="text-sm text-slate-500 whitespace-nowrap font-medium">{completedCount}/12 groups</span>
        <button
          onClick={useAllAI}
          className="flex items-center gap-1.5 text-xs font-bold text-amber-600 border border-amber-300 hover:bg-amber-50 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
        >
          <BoltIcon /> Auto-fill all with AI
        </button>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-10">
        {GROUP_LABELS.map(g => (
          <GroupCard
            key={g}
            groupLetter={g}
            teams={GROUPS[g]}
            selections={selections[g]}
            aiRanking={aiRankings[g]}
            loading={loadingAI[g]}
            onToggle={toggleTeam}
            onUseAI={useAIPicks}
          />
        ))}
      </div>

      {/* 3rd Place Selection */}
      {allGroupsDone && (
        <div className="mb-8">
          <div className="flex items-end justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-0.5">Best Third-Place Teams</h2>
              <p className="text-slate-500 text-sm">
                Pick <span className="text-slate-900 font-semibold">8 of 12</span> third-place teams to advance to the Round of 32
              </p>
            </div>
            <span className={`text-sm font-bold px-3 py-1 rounded-lg ${
              thirdSelected.length === 8 ? 'text-green-700 bg-green-100' : 'text-slate-500 bg-slate-100'
            }`}>
              {thirdSelected.length}/8
            </span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
            {thirdPlaceTeams.map(({ group, team }) => (
              <ThirdPlaceCard
                key={group}
                group={group}
                team={team}
                selected={thirdSelected.includes(team)}
                disabled={!thirdSelected.includes(team) && thirdSelected.length >= 8}
                onToggle={toggleThirdPlace}
              />
            ))}
          </div>
        </div>
      )}

      {/* Build Bracket CTA */}
      {allGroupsDone && (
        <div className={`flex items-center gap-5 rounded-2xl px-6 py-5 border transition-all duration-300 ${
          canBuild
            ? 'bg-green-50 border-green-400 shadow-sm'
            : 'bg-white border-slate-200'
        }`}>
          <div className="flex-1">
            <div className={`font-bold mb-0.5 ${canBuild ? 'text-slate-900' : 'text-slate-400'}`}>
              {canBuild ? 'Your 32 teams are set — build your bracket' : `Select ${8 - thirdSelected.length} more third-place team${8 - thirdSelected.length !== 1 ? 's' : ''}`}
            </div>
            <div className="text-slate-500 text-sm">
              {canBuild ? 'Round of 32 will be auto-populated from your group picks' : 'Complete all groups and 3rd-place selection to continue'}
            </div>
          </div>
          <button
            onClick={handleBuild}
            disabled={!canBuild}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-500 disabled:bg-slate-200 disabled:text-slate-400 text-white font-bold px-6 py-3 rounded-xl transition-all duration-150 text-sm whitespace-nowrap cursor-pointer disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-green-400 focus-visible:outline-none"
          >
            Build Bracket <ArrowRightIcon />
          </button>
        </div>
      )}
    </div>
  );
}
