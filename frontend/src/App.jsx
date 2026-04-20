import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom';
import GroupStage from './pages/GroupStage';
import BracketChallenge from './pages/BracketChallenge';
import Leaderboard from './pages/Leaderboard';
import Analysis from './pages/Analysis';

function Nav() {
  const { pathname } = useLocation();
  const isCompete = pathname === '/' || pathname === '/groups' || pathname === '/bracket';
  const link = (to, label, active) => (
    <Link
      to={to}
      className={`text-sm font-medium transition-colors ${
        active ? 'text-white font-semibold' : 'text-slate-400 hover:text-white'
      }`}
    >
      {label}
    </Link>
  );
  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-4 flex items-center gap-8 sticky top-0 z-50">
      <Link to="/" className="text-base font-extrabold text-amber-400 hover:text-amber-300 transition-colors tracking-tight">
        WC 2026 Predictor
      </Link>
      <div className="flex items-center gap-6">
        {link('/analysis', 'Analysis', pathname === '/analysis')}
        {link('/leaderboard', 'Leaderboard', pathname === '/leaderboard')}
        <Link
          to="/"
          className={`text-sm font-bold px-4 py-1.5 rounded-lg transition-colors ${
            isCompete
              ? 'bg-amber-400 text-slate-900'
              : 'bg-amber-500 hover:bg-amber-400 text-slate-900'
          }`}
        >
          Compete →
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-amber-50 text-slate-900">
        <Nav />
        <main className="px-4 py-8">
          <Routes>
            <Route path="/" element={<GroupStage />} />
            <Route path="/groups" element={<GroupStage />} />
            <Route path="/bracket" element={<BracketChallenge />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
