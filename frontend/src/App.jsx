import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import BracketChallenge from "./pages/BracketChallenge";
import Leaderboard from "./pages/Leaderboard";
import Analysis from "./pages/Analysis";
import MyPredictions from "./pages/MyPredictions";
import NotFound from "./pages/NotFound";

function Nav() {
  const { pathname } = useLocation();
  const link = (to, label, active) => (
    <Link
      to={to}
      className={`text-[13px] font-semibold uppercase tracking-wider transition-colors ${
        active ? "text-gold-300" : "text-emerald-100/70 hover:text-white"
      }`}
    >
      {label}
    </Link>
  );
  return (
    <nav className="pitch-deep pitch-stripes border-b-4 border-gold-500 px-4 sm:px-6 py-3.5 flex items-center gap-4 sm:gap-8 sticky top-0 z-50">
      <Link to="/" className="flex items-center gap-2 group shrink-0">
        <span className="grid place-items-center w-8 h-8 rounded-lg bg-gold-400 text-pitch-950 font-display text-lg shadow-lg group-hover:scale-105 transition-transform">
          W
        </span>
        <span className="font-display text-white text-lg leading-none tracking-tight hidden sm:block">
          WC26 <span className="text-gold-400">PREDICTOR</span>
        </span>
      </Link>
      <div className="flex items-center gap-4 sm:gap-6 ml-auto">
        {link("/analysis", "Analysis", pathname === "/analysis")}
        {link("/my-predictions", "My Picks", pathname === "/my-predictions")}
        {link("/leaderboard", "Ranks", pathname === "/leaderboard")}
        <Link
          to="/"
          className={`font-display text-xs sm:text-sm px-3 sm:px-4 py-2 rounded-lg transition-all uppercase tracking-wide ${
            pathname === "/" || pathname === "/bracket"
              ? "bg-gold-400 text-pitch-950 shadow-[0_0_20px_rgba(251,191,36,0.4)]"
              : "bg-gold-500 hover:bg-gold-400 text-pitch-950 hover:scale-105"
          }`}
        >
          Bracket
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-dvh pitch-bg text-slate-900">
        <Nav />
        <main className="px-4 py-8">
          <Routes>
            <Route path="/" element={<BracketChallenge />} />
            <Route path="/bracket" element={<Navigate to="/" replace />} />
            <Route path="/groups" element={<Navigate to="/" replace />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/my-predictions" element={<MyPredictions />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
