import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom';
import GroupStage from './pages/GroupStage';
import BracketChallenge from './pages/BracketChallenge';
import Leaderboard from './pages/Leaderboard';
import Analysis from './pages/Analysis';

function Nav() {
  const { pathname } = useLocation();
  const isActive = (to) => pathname === to || (to === '/' && pathname === '/');
  const link = (to, label) => (
    <Link
      to={to}
      className={`text-sm font-medium transition-colors ${
        isActive(to) ? 'text-white' : 'text-gray-500 hover:text-gray-200'
      }`}
    >
      {label}
    </Link>
  );
  return (
    <nav className="bg-gray-900/80 backdrop-blur border-b border-gray-800 px-6 py-4 flex items-center gap-8 sticky top-0 z-50">
      <Link to="/" className="text-base font-extrabold text-emerald-400 hover:text-emerald-300 transition-colors tracking-tight">
        WC 2026 Predictor
      </Link>
      <div className="flex items-center gap-6">
        {link('/', 'Analysis')}
        {link('/leaderboard', 'Leaderboard')}
        <Link
          to="/groups"
          className="text-sm font-bold bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1.5 rounded-lg transition-colors"
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
      <div className="min-h-screen bg-gray-950 text-white">
        <Nav />
        <main className="px-4 py-8">
          <Routes>
            <Route path="/" element={<Analysis />} />
            <Route path="/groups" element={<GroupStage />} />
            <Route path="/bracket" element={<BracketChallenge />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
