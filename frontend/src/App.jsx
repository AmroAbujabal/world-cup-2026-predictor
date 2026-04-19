import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import BracketChallenge from './pages/BracketChallenge';
import Leaderboard from './pages/Leaderboard';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center gap-8">
          <Link to="/" className="text-lg font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
            ⚽ World Cup 2026 Predictor
          </Link>
          <Link to="/leaderboard" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
            Leaderboard
          </Link>
        </nav>
        <main className="px-4 py-8">
          <Routes>
            <Route path="/" element={<BracketChallenge />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
