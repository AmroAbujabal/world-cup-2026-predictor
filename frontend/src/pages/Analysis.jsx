// frontend/src/pages/Analysis.jsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function ProbBar({ p1, pd, p2 }) {
  return (
    <div className="flex flex-col gap-1 w-56 shrink-0">
      <div className="flex w-full h-2.5 rounded-full overflow-hidden gap-px">
        <div className="bg-green-500 transition-all" style={{ width: `${p1}%` }} />
        <div className="bg-slate-300 transition-all" style={{ width: `${pd}%` }} />
        <div className="bg-sky-500 transition-all" style={{ width: `${p2}%` }} />
      </div>
      <div className="flex w-full justify-between text-xs text-slate-500 font-medium">
        <span>{p1}%</span>
        <span className="text-slate-400">{pd}% draw</span>
        <span>{p2}%</span>
      </div>
    </div>
  );
}

function MatchupRow({ matchup }) {
  const p1 = Math.round(matchup.prob1 * 100);
  const pd = Math.round(matchup.prob_draw * 100);
  const p2 = Math.round(matchup.prob2 * 100);
  const w1 = matchup.predicted_winner === matchup.team1;

  return (
    <div className="bg-white border border-slate-200 rounded-xl px-5 py-4 flex items-center justify-between gap-4 shadow-sm">
      <div className={`w-36 text-right text-sm font-semibold ${w1 ? 'text-green-700' : 'text-slate-400'}`}>
        {matchup.team1}
        {w1 && <span className="ml-1.5 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-normal">wins</span>}
      </div>
      <ProbBar p1={p1} pd={pd} p2={p2} />
      <div className={`w-36 text-sm font-semibold ${!w1 ? 'text-green-700' : 'text-slate-400'}`}>
        {!w1 && <span className="mr-1.5 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-normal">wins</span>}
        {matchup.team2}
      </div>
    </div>
  );
}

function Section({ number, title, children }) {
  return (
    <section className="mb-14">
      <div className="flex items-baseline gap-3 mb-5">
        <span className="text-green-600 font-bold text-lg">{number}.</span>
        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm">
      <div className="text-3xl font-bold text-green-600 mb-1">{value}</div>
      <div className="text-sm font-semibold text-slate-900">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  );
}

function FeatureCard({ name, desc }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
      <div className="text-sm font-semibold text-green-600 mb-1.5">{name}</div>
      <div className="text-sm text-slate-600 leading-relaxed">{desc}</div>
    </div>
  );
}

export default function Analysis() {
  const [bracket, setBracket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/bracket-predictions`)
      .then(r => { setBracket(r.data); setLoading(false); })
      .catch(() => { setError('Failed to load predictions — is the backend running?'); setLoading(false); });
  }, []);

  return (
    <div className="max-w-3xl mx-auto">

      {/* Header */}
      <div className="mb-12">
        <p className="text-xs font-bold uppercase tracking-widest text-green-600 mb-3">Research Report · April 2026</p>
        <h1 className="text-4xl font-extrabold text-slate-900 leading-snug mb-4 mt-1">
          Predicting the 2026 FIFA World Cup with Machine Learning
        </h1>
        <p className="text-sm text-slate-500 mb-4">
          By <span className="text-slate-700 font-medium">Amr Abujabal</span>
        </p>
        <p className="text-slate-600 text-base leading-relaxed">
          An XGBoost model trained on 49,287 international matches (1872–2024) to predict match outcomes and simulate the full knockout bracket using ELO ratings, recent form, and head-to-head records.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white font-bold px-6 py-2.5 rounded-xl transition-colors text-sm"
          >
            Compete against the model
            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <div className="flex gap-2 flex-wrap">
            {['XGBoost', 'FastAPI', 'React', 'ELO Ratings', '49k matches'].map(tag => (
              <span key={tag} className="text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 px-3 py-1 rounded-full">{tag}</span>
            ))}
          </div>
        </div>
      </div>

      <hr className="border-slate-200 mb-12" />

      {/* Abstract */}
      <Section number="Abstract" title="">
        <p className="text-slate-600 leading-relaxed text-base">
          This project builds an end-to-end machine learning pipeline to predict international football outcomes — home win, draw, or away win — and simulate the 2026 FIFA World Cup knockout bracket. Features are derived from ELO ratings, recent form, and head-to-head records. Backtesting against the 2018 and 2022 World Cups yields ~40% accuracy, meaningfully above the 33.3% random baseline for a 3-class problem.
        </p>
      </Section>

      {/* Data */}
      <Section number="1" title="Data">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          The dataset is sourced from Kaggle's international football results archive, covering every recorded international match from 1872 to 2024 across 194 nations. Each row contains the home team, away team, final score, tournament name, and whether the match was played on neutral ground.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total Matches" value="49,287" sub="1872 – 2024" />
          <StatCard label="Unique Teams" value="194+" sub="nations" />
          <StatCard label="Tournaments" value="150+" sub="types" />
          <StatCard label="World Cups" value="23" sub="in dataset" />
        </div>
      </Section>

      {/* Features */}
      <Section number="2" title="Feature Engineering">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          Nine features are computed per match using only data available before kick-off to avoid leakage. Features fall into three groups: skill (ELO), form, and history (H2H).
        </p>
        <div className="grid sm:grid-cols-3 gap-3">
          {[
            { name: 'ELO Difference', desc: 'Skill gap between the two teams using tournament-weighted K-factors — FIFA World Cup = 60, Friendly = 20.' },
            { name: 'Home ELO', desc: "Home team's ELO rating computed chronologically, starting at 1500, updated after every match." },
            { name: 'Away ELO', desc: "Away team's ELO rating computed on the same chronological pass." },
            { name: 'Home Form', desc: 'Average points per game over the home team\'s last 5 matches (3 = win, 1 = draw, 0 = loss).' },
            { name: 'Away Form', desc: 'Average points per game over the away team\'s last 5 matches.' },
            { name: 'H2H Home Wins', desc: 'Home team wins in the last 10 direct encounters between these two sides.' },
            { name: 'H2H Draws', desc: 'Draws in the last 10 direct encounters between these two sides.' },
            { name: 'H2H Away Wins', desc: 'Away team wins in the last 10 direct encounters between these two sides.' },
            { name: 'Is Neutral', desc: 'Binary flag: 1 if played on neutral ground. All World Cup bracket matches are set to 1.' },
          ].map(f => <FeatureCard key={f.name} {...f} />)}
        </div>
      </Section>

      {/* Model */}
      <Section number="3" title="Model">
        <p className="text-slate-600 text-base leading-relaxed mb-5">
          XGBoost was chosen for its strength on tabular data and native multi-class probability support. The model outputs softmax probabilities across three classes: home win, draw, and away win.
        </p>
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 font-mono text-sm text-slate-300 leading-loose">
          <span className="text-emerald-400">XGBClassifier</span>(<br />
          &nbsp;&nbsp;n_estimators=<span className="text-yellow-300">300</span>,<br />
          &nbsp;&nbsp;max_depth=<span className="text-yellow-300">5</span>,<br />
          &nbsp;&nbsp;learning_rate=<span className="text-yellow-300">0.05</span>,<br />
          &nbsp;&nbsp;subsample=<span className="text-yellow-300">0.8</span>,<br />
          &nbsp;&nbsp;colsample_bytree=<span className="text-yellow-300">0.8</span>,<br />
          &nbsp;&nbsp;eval_metric=<span className="text-blue-400">'mlogloss'</span>,<br />
          &nbsp;&nbsp;objective=<span className="text-blue-400">'multi:softprob'</span><br />
          )
        </div>
      </Section>

      {/* Backtest */}
      <Section number="4" title="Backtest Results">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          The model is backtested by training on all data before each World Cup year and evaluating on that tournament's 64 matches. The 3-class random baseline is 33.3%.
        </p>
        <div className="grid grid-cols-3 gap-4 mb-5">
          <StatCard label="2018 WC Accuracy" value="40.6%" sub="64 matches" />
          <StatCard label="2022 WC Accuracy" value="39.1%" sub="64 matches" />
          <StatCard label="Combined" value="39.8%" sub="+6.5pp above baseline" />
        </div>
        <p className="text-slate-500 text-sm leading-relaxed">
          Draws are the hardest class to predict and pull accuracy down — a model that ignores draws entirely would score higher on raw accuracy. The ELO + form features capture long-run quality well; short-run upset potential remains the main gap.
        </p>
      </Section>

      {/* Bracket Predictions */}
      <Section number="5" title="2026 World Cup Bracket Predictions">
        <p className="text-slate-600 text-base leading-relaxed mb-8">
          The model simulates all 5 knockout rounds (Round of 32 through the Final) by predicting every matchup and advancing the team with the higher win probability. All matches are treated as neutral-ground (is_neutral = 1).
        </p>

        {loading && (
          <div className="text-slate-400 text-sm text-center py-16 border border-slate-200 rounded-xl bg-white">
            Running bracket simulation…
          </div>
        )}
        {error && (
          <div className="text-red-600 text-sm text-center py-16 border border-red-200 rounded-xl bg-red-50">
            {error}
          </div>
        )}

        {bracket && bracket.rounds.map(round => (
          <div key={round.round} className="mb-8">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-px flex-1 bg-slate-200" />
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">{round.round}</span>
              <div className="h-px flex-1 bg-slate-200" />
            </div>
            <div className="flex flex-col gap-2.5">
              {round.matchups.map((m, i) => <MatchupRow key={i} matchup={m} />)}
            </div>
          </div>
        ))}

        {bracket && (
          <div className="mt-10 border-2 border-amber-400 bg-amber-50 rounded-2xl p-10 text-center shadow-[0_4px_24px_rgba(251,191,36,0.2)]">
            <div className="text-5xl mb-4">🏆</div>
            <div className="text-xs font-bold uppercase tracking-widest text-amber-600 mb-2">Model's Predicted Champion</div>
            <div className="text-4xl font-extrabold text-slate-900">{bracket.champion}</div>
          </div>
        )}
      </Section>

      {/* Challenge CTA */}
      <div className="my-14 rounded-2xl border border-green-300 bg-gradient-to-br from-green-50 to-amber-50 px-8 py-10">
        <div className="text-center mb-8">
          <p className="text-xs font-bold uppercase tracking-widest text-green-600 mb-3">Your Turn</p>
          <h2 className="text-3xl font-extrabold text-slate-900 mb-3">
            Think you can beat the model?
          </h2>
          <p className="text-slate-600 text-base max-w-lg mx-auto leading-relaxed">
            The model has made its picks. Now build your own bracket — choose your group stage winners, pick your third-place qualifiers, and call every knockout match. See who gets it right when the tournament kicks off.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-base"
          >
            Build my bracket
            <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <Link
            to="/leaderboard"
            className="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
          >
            View leaderboard →
          </Link>
        </div>
        <div className="mt-8 grid grid-cols-3 gap-4 text-center border-t border-green-200 pt-8">
          {[
            { n: '48', label: 'Teams', sub: '12 groups' },
            { n: '31', label: 'Matches to pick', sub: 'R32 → Final' },
            { n: '40.6%', label: 'Model accuracy', sub: '2018 World Cup' },
          ].map(s => (
            <div key={s.label}>
              <div className="text-2xl font-extrabold text-green-600">{s.n}</div>
              <div className="text-sm font-semibold text-slate-900 mt-0.5">{s.label}</div>
              <div className="text-xs text-slate-400">{s.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Stack */}
      <Section number="6" title="Tech Stack">
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            { layer: 'Data & ML', items: 'Python · pandas · XGBoost · scikit-learn · joblib' },
            { layer: 'Backend API', items: 'FastAPI · SQLAlchemy · SQLite (dev) · Pydantic v2' },
            { layer: 'Frontend', items: 'React 18 · Vite · Tailwind CSS v3 · React Router · axios' },
            { layer: 'Dataset', items: 'Kaggle — International Football Results 1872–2024 (49,287 matches)' },
          ].map(s => (
            <div key={s.layer} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-sm font-bold text-slate-900 mb-1">{s.layer}</div>
              <div className="text-sm text-slate-500">{s.items}</div>
            </div>
          ))}
        </div>
      </Section>

    </div>
  );
}
