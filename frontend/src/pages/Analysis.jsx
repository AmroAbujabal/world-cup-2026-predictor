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

function ChallengeCard({ title, problem, solution }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="text-sm font-bold text-slate-900 mb-3">{title}</div>
      <div className="mb-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-red-500 mr-2">Problem</span>
        <span className="text-sm text-slate-600">{problem}</span>
      </div>
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-green-600 mr-2">Solution</span>
        <span className="text-sm text-slate-600">{solution}</span>
      </div>
    </div>
  );
}

function ArchBox({ label, items, color }) {
  const colors = {
    green: 'border-green-300 bg-green-50',
    blue: 'border-sky-300 bg-sky-50',
    amber: 'border-amber-300 bg-amber-50',
    slate: 'border-slate-300 bg-slate-50',
  };
  const textColors = {
    green: 'text-green-700',
    blue: 'text-sky-700',
    amber: 'text-amber-700',
    slate: 'text-slate-700',
  };
  return (
    <div className={`border rounded-xl p-4 ${colors[color]}`}>
      <div className={`text-xs font-bold uppercase tracking-wider mb-2 ${textColors[color]}`}>{label}</div>
      {items.map(item => (
        <div key={item} className="text-sm text-slate-700 py-0.5">{item}</div>
      ))}
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
        <p className="text-xs font-bold uppercase tracking-widest text-green-600 mb-3">Engineering Write-up · April 2026</p>
        <h1 className="text-4xl font-extrabold text-slate-900 leading-snug mb-4 mt-1">
          Predicting the 2026 FIFA World Cup with Machine Learning
        </h1>
        <p className="text-sm text-slate-500 mb-4">
          By <span className="text-slate-700 font-medium">Amr Abujabal</span>
          <span className="mx-2 text-slate-300">·</span>
          <a
            href="https://github.com/AmroAbujabal/world-cup-2026-predictor"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-900 transition-colors"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
            </svg>
            View on GitHub
          </a>
        </p>
        <p className="text-slate-600 text-base leading-relaxed">
          A full-stack ML application: an XGBoost classifier trained on 49,287 international matches predicts World Cup outcomes, served via a FastAPI backend, with an interactive React frontend that lets users build brackets and compete on a live leaderboard.
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
            {['XGBoost', 'FastAPI', 'React 18', 'PostgreSQL', 'Railway', 'Vercel'].map(tag => (
              <span key={tag} className="text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 px-3 py-1 rounded-full">{tag}</span>
            ))}
          </div>
        </div>
      </div>

      <hr className="border-slate-200 mb-12" />

      {/* Abstract */}
      <Section number="Abstract" title="">
        <p className="text-slate-600 leading-relaxed text-base">
          This project is an end-to-end machine learning system for predicting international football match outcomes — home win, draw, or away win — and simulating the 2026 FIFA World Cup knockout bracket. The ML pipeline covers data ingestion, chronological feature engineering (ELO ratings, recent form, head-to-head records), XGBoost training with leakage-free backtesting, and a live prediction API. On top of this sits a full-stack web application: a FastAPI backend with a PostgreSQL database and a React frontend with an interactive bracket challenge and real-time leaderboard.
        </p>
        <p className="text-slate-600 leading-relaxed text-base mt-4">
          Backtesting against the 2018 and 2022 World Cups yields ~40% accuracy — meaningfully above the 33.3% random baseline for a 3-class problem and comparable to published academic models on the same task.
        </p>
      </Section>

      {/* System Architecture */}
      <Section number="1" title="System Architecture">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          The system is split into three layers: a Python ML pipeline, a FastAPI REST API, and a React single-page application. Each is independently deployable, with the backend hosted on Railway and the frontend on Vercel.
        </p>
        <div className="grid sm:grid-cols-3 gap-3 mb-6">
          <ArchBox color="green" label="ML Pipeline" items={['pandas · feature eng.', 'XGBoost classifier', 'ELO · form · H2H', 'joblib model cache']} />
          <ArchBox color="blue" label="FastAPI Backend" items={['REST prediction API', 'SQLAlchemy ORM', 'PostgreSQL (Railway)', 'Pydantic v2 schemas']} />
          <ArchBox color="amber" label="React Frontend" items={['Vite + Tailwind CSS', 'React Router v6', 'axios API client', 'localStorage state']} />
        </div>
        <p className="text-slate-600 text-sm leading-relaxed">
          The model is loaded once on the first API request using <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono text-xs">lru_cache(maxsize=1)</code> — this singleton pattern avoids re-training on every request while keeping the deployment stateless. Training takes ~30 seconds on cold start; subsequent predictions are &lt;100ms.
        </p>
      </Section>

      {/* Data */}
      <Section number="2" title="Data">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          The dataset is sourced from Kaggle's international football results archive, covering every recorded international match from 1872 to 2024 across 194 nations. Each row contains the home team, away team, final score, tournament name, and a neutral-ground flag. The full dataset is loaded with memory-efficient dtypes (<code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono text-xs">category</code> for team/tournament columns, <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono text-xs">int16</code> for scores) to reduce RAM footprint.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <StatCard label="Total Matches" value="49,287" sub="1872 – 2024" />
          <StatCard label="Unique Teams" value="194+" sub="nations" />
          <StatCard label="Tournaments" value="150+" sub="types" />
          <StatCard label="World Cups" value="23" sub="in dataset" />
        </div>
        <p className="text-slate-600 text-sm leading-relaxed">
          All feature computation is done in a single chronological pass over the sorted dataset. This is the critical design constraint that prevents data leakage — ELO ratings, form windows, and H2H records are always computed from matches strictly before the one being predicted.
        </p>
      </Section>

      {/* Features */}
      <Section number="3" title="Feature Engineering">
        <p className="text-slate-600 text-base leading-relaxed mb-4">
          Nine features are computed per match using only data available before kick-off. The feature set is intentionally lean — three conceptual groups capture the signal that matters for football prediction without overfitting to noise.
        </p>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-5 text-sm text-slate-600 leading-relaxed">
          <span className="font-semibold text-slate-800">Leakage prevention: </span>
          The entire feature matrix is built in a single forward pass, sorted by date. ELO ratings are updated only after each match is processed, never before. This guarantees that predictions at inference time use the same information available at training time.
        </div>
        <div className="grid sm:grid-cols-3 gap-3 mb-5">
          {[
            { name: 'ELO Difference', desc: 'Skill gap between the two teams. K-factor is weighted by tournament importance: FIFA WC = 60, Confederations Cup = 50, Qualifier = 40, Friendly = 20.' },
            { name: 'Home ELO', desc: "Home team's absolute ELO rating, computed chronologically from a starting value of 1500 using a standard Elo update formula." },
            { name: 'Away ELO', desc: "Away team's absolute ELO rating on the same chronological pass — captured separately since relative skill and absolute level both matter." },
            { name: 'Home Form', desc: "Average points per game over the home team's last 5 matches (3 = win, 1 = draw, 0 = loss), capturing short-run momentum." },
            { name: 'Away Form', desc: "Average points per game over the away team's last 5 matches — momentum is asymmetric, so home and away form are kept separate." },
            { name: 'H2H Home Wins', desc: 'Home team wins in the last 10 direct encounters, capturing psychological head-to-head dynamics between specific nations.' },
            { name: 'H2H Draws', desc: 'Draws in the last 10 direct encounters. Some pairings are structurally draw-prone; this captures that pattern.' },
            { name: 'H2H Away Wins', desc: 'Away team wins in the last 10 head-to-head encounters between these two sides.' },
            { name: 'Is Neutral', desc: 'Binary flag: 1 if played on neutral ground. Home advantage is real in football; all WC bracket matches are set to 1.' },
          ].map(f => <FeatureCard key={f.name} {...f} />)}
        </div>
      </Section>

      {/* Model */}
      <Section number="4" title="Model">
        <p className="text-slate-600 text-base leading-relaxed mb-4">
          XGBoost was chosen for its proven strength on tabular data, native 3-class probability output, and fast training on CPU. Neural approaches (e.g. a simple MLP) were prototyped but showed no accuracy improvement on this dataset while being considerably slower to iterate on. The model outputs softmax probabilities across three classes — home win, draw, and away win — via <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono text-xs">multi:softprob</code>.
        </p>
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 font-mono text-sm text-slate-300 leading-loose mb-5">
          <span className="text-emerald-400">XGBClassifier</span>(<br />
          &nbsp;&nbsp;n_estimators=<span className="text-yellow-300">300</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-500"># enough trees without overfitting</span><br />
          &nbsp;&nbsp;max_depth=<span className="text-yellow-300">5</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-500"># shallow trees — football is noisy</span><br />
          &nbsp;&nbsp;learning_rate=<span className="text-yellow-300">0.05</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-500"># slow learning, better generalisation</span><br />
          &nbsp;&nbsp;subsample=<span className="text-yellow-300">0.8</span>,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-500"># row subsampling to reduce variance</span><br />
          &nbsp;&nbsp;colsample_bytree=<span className="text-yellow-300">0.8</span>,&nbsp;<span className="text-slate-500"># feature subsampling per tree</span><br />
          &nbsp;&nbsp;eval_metric=<span className="text-blue-400">'mlogloss'</span>,<br />
          &nbsp;&nbsp;objective=<span className="text-blue-400">'multi:softprob'</span>,&nbsp;<span className="text-slate-500"># 3-class probability output</span><br />
          &nbsp;&nbsp;n_jobs=<span className="text-yellow-300">1</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-slate-500"># single-threaded (Railway memory constraint)</span><br />
          )
        </div>
        <p className="text-slate-600 text-sm leading-relaxed">
          Class labels are encoded as 0 = home win, 1 = draw, 2 = away win. The model is serialised with <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 font-mono text-xs">joblib</code> after training and loaded as a singleton at API startup. Per-class probabilities are exposed directly in the API response so the frontend can render live win-probability bars on every matchup.
        </p>
      </Section>

      {/* Backtest */}
      <Section number="5" title="Backtest Results">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          Backtesting uses a strict temporal split: the model is trained on all matches before the World Cup year, then evaluated on that tournament's group stage and knockout rounds. This is the only honest evaluation protocol — any leakage of future data into training would inflate accuracy.
        </p>
        <div className="grid grid-cols-3 gap-4 mb-5">
          <StatCard label="2018 WC Accuracy" value="40.6%" sub="64 matches" />
          <StatCard label="2022 WC Accuracy" value="39.1%" sub="64 matches" />
          <StatCard label="Combined" value="39.8%" sub="+6.5pp above baseline" />
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm text-sm text-slate-600 leading-relaxed space-y-2">
          <p><span className="font-semibold text-slate-800">Baseline context:</span> A 3-class random classifier scores 33.3%. A naïve "always predict home win" classifier scores ~45% on historical data but fails on neutral-ground WC matches. The model's 39.8% on neutral-ground WC matches is therefore competitive.</p>
          <p><span className="font-semibold text-slate-800">Draw difficulty:</span> Draws are the hardest class — they make up ~25% of outcomes but are structurally hard to predict. A model that ignores draws would score higher on raw accuracy but would be useless for bracket simulation. The draw class is retained deliberately.</p>
          <p><span className="font-semibold text-slate-800">ELO dominance:</span> Feature importance analysis shows ELO difference is the strongest single predictor, accounting for ~40% of split gain. This aligns with football analytics literature — skill gap is the best long-run predictor of outcomes.</p>
        </div>
      </Section>

      {/* Engineering Challenges */}
      <Section number="6" title="Engineering Challenges">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          Building and deploying this system surfaced several non-trivial engineering problems. Solving them required debugging under production constraints.
        </p>
        <div className="flex flex-col gap-4">
          <ChallengeCard
            title="Out-of-memory crash on Railway (512 MB limit)"
            problem="The prediction service ran the feature pipeline twice — once to compute ELO/form/H2H, then again inside the training loop. With 49k rows and multiple intermediate DataFrames, peak RAM exceeded Railway's 512 MB container limit and the process was OOM-killed before the model finished training."
            solution="Refactored the pipeline to run once and return a single (X, y, enriched_df) tuple. Intermediate DataFrames are explicitly deleted (del df) before training. The enriched DataFrame is never stored — instead, final ELO ratings, form scores, and H2H records are extracted into compact dicts. Combined with category/int16 dtypes and n_jobs=1, peak RAM dropped ~60%."
          />
          <ChallengeCard
            title="CORS failures on Vercel preview deployments"
            problem="Vercel generates a unique URL for every pull request preview deployment (e.g. frontend-abc123-user-projects.vercel.app). Hardcoding allowed origins in the backend meant every new preview deploy broke CORS and required a manual backend redeployment."
            solution="Replaced the static origin list with a custom Starlette BaseHTTPMiddleware that matches origins against a compiled regex pattern. All *.vercel.app preview URLs matching the project pattern are allowed dynamically, with no config changes required per deploy."
          />
          <ChallengeCard
            title="Bracket state lost on page navigation"
            problem="The group stage picker and bracket challenge are separate React routes. When a user completed the group stage and navigated to the bracket, React Router unmounted the component and all state was lost. Refreshing the bracket page would reset to the default teams."
            solution="Implemented a three-tier state resolution strategy: (1) React Router location.state for fresh navigation from the group stage, (2) localStorage fallback parsed via buildR32() for refreshes, (3) hardcoded default R32 as a last resort. Group picks and submitted bracket username are both persisted to localStorage so the full UX survives refreshes and tab closes."
          />
          <ChallengeCard
            title="Leaderboard submissions silently failing"
            problem="The /user/predict endpoint required a match_id referencing a row in the matches table. But no matches were seeded in the database, so every submission returned a 404 — silently swallowed by .catch(() => null). Users saw 'Bracket submitted!' but nothing was saved."
            solution="Added a _seed_matches() function called at startup that inserts all 31 WC knockout matches (IDs 1–31) into the database if the table is empty. Bracket matchup IDs (r32_1, r16_1, etc.) are mapped to stable DB IDs via a MATCH_ID_MAP constant, replacing the fragile idx+1 index. The endpoint was also converted to an upsert so re-submissions update picks rather than 409ing."
          />
          <ChallengeCard
            title="Ephemeral SQLite database on Railway"
            problem="Railway's filesystem is ephemeral — it resets on each deployment. Using SQLite meant every backend redeploy wiped all user submissions and the leaderboard, making the feature non-functional in production."
            solution="The backend was architected from the start to read DATABASE_URL from the environment, switching between SQLite (dev) and PostgreSQL (production) automatically via SQLAlchemy's connection string detection. A managed PostgreSQL instance was provisioned on Railway and DATABASE_URL was injected as an environment variable — zero code changes required."
          />
        </div>
      </Section>

      {/* Product Features */}
      <Section number="7" title="Interactive Product">
        <p className="text-slate-600 text-base leading-relaxed mb-6">
          Beyond the ML model, the project is a fully functional web application with three interactive phases — each backed by live API calls to the prediction model.
        </p>
        <div className="flex flex-col gap-4">
          {[
            {
              step: '01',
              title: 'Group Stage Picker',
              desc: "Users pick the top 2 finishers from each of the 12 groups, then select 8 of 12 best third-place teams to fill the Round of 32. An AI suggestions feature runs the model's round-robin simulation for all 4 teams in a group and ranks them by predicted points — powered by a live /group-standings API call. All 12 groups warm up concurrently (staggered 200ms) on page load so probabilities are ready when users get to them.",
              tags: ['12 groups', '48 teams', 'AI suggestions', 'localStorage'],
            },
            {
              step: '02',
              title: 'Bracket Challenge',
              desc: 'A horizontally-scrollable interactive bracket spanning Round of 32 through the Final. Picking a winner cascades forward: the bracket auto-populates the next round slot, clears downstream picks (since the matchup changes), and fires a new /predict API call to fetch win probabilities for the newly-formed matchup — all in the same state update cycle. Submitted brackets are stored in PostgreSQL and survive across redeploys.',
              tags: ['31 matches', 'live probabilities', 'cascade picks', 'PostgreSQL'],
            },
            {
              step: '03',
              title: 'Live Leaderboard',
              desc: "Submitted brackets appear on a live leaderboard ranked by total points. Before the tournament the leaderboard shows 'Submitted' status for all entrants. Once matches are played, results are fed via an admin endpoint that scores every prediction for that match and updates user point totals — no manual recalculation required.",
              tags: ['real-time scoring', 'upsert predictions', 'ranked entries'],
            },
          ].map(f => (
            <div key={f.step} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex gap-5">
              <div className="text-3xl font-black text-slate-200 shrink-0 leading-none mt-0.5">{f.step}</div>
              <div>
                <div className="font-bold text-slate-900 mb-1.5">{f.title}</div>
                <p className="text-sm text-slate-600 leading-relaxed mb-3">{f.desc}</p>
                <div className="flex flex-wrap gap-1.5">
                  {f.tags.map(t => (
                    <span key={t} className="text-[10px] font-semibold bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full">{t}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Bracket Predictions */}
      <Section number="8" title="Model's 2026 Bracket Predictions">
        <p className="text-slate-600 text-base leading-relaxed mb-8">
          The model simulates all 5 knockout rounds by advancing the team with the higher win probability at each matchup. All matches are treated as neutral-ground (is_neutral = 1). Predictions are fetched live from the backend.
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
            className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-base"
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
            { n: '39.8%', label: 'Model accuracy', sub: 'vs 33.3% baseline' },
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
      <Section number="9" title="Tech Stack & Deployment">
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            { layer: 'Machine Learning', items: 'Python 3.12 · pandas · XGBoost · scikit-learn · joblib · numpy' },
            { layer: 'Backend API', items: 'FastAPI · SQLAlchemy 2.0 · Pydantic v2 · uvicorn · python-dotenv' },
            { layer: 'Database', items: 'PostgreSQL (production, Railway) · SQLite (local dev) · psycopg2' },
            { layer: 'Frontend', items: 'React 18 · Vite · Tailwind CSS v3 · React Router v6 · axios' },
            { layer: 'Deployment', items: 'Railway (backend + Postgres) · Vercel (frontend) · GitHub CI via git push' },
            { layer: 'Dataset', items: 'Kaggle — International Football Results 1872–2024 (49,287 matches)' },
          ].map(s => (
            <div key={s.layer} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className="text-sm font-bold text-slate-900 mb-1">{s.layer}</div>
              <div className="text-sm text-slate-500">{s.items}</div>
            </div>
          ))}
        </div>
        <div className="mt-4 bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-600">
          <span className="font-semibold text-slate-800">Deployment pipeline: </span>
          Git push to <code className="bg-white border border-slate-200 px-1.5 py-0.5 rounded font-mono text-xs">main</code> triggers automatic redeploys on both Railway and Vercel. The backend rebuilds the Docker container, runs <code className="bg-white border border-slate-200 px-1.5 py-0.5 rounded font-mono text-xs">_seed_matches()</code> on startup (idempotent — skips if rows already exist), and is live within ~2 minutes. The frontend deploys in ~30 seconds via Vite's production build.
        </div>
      </Section>

    </div>
  );
}
