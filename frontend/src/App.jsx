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
      className={`text-[13px] font-medium transition-colors ${
        active ? "text-slate-900" : "text-slate-500 hover:text-slate-900"
      }`}
    >
      {label}
    </Link>
  );
  return (
    <nav className="bg-white/80 backdrop-blur border-b border-slate-200/80 px-4 sm:px-8 py-4 flex items-center gap-4 sm:gap-8 sticky top-0 z-50">
      <Link to="/" className="flex items-center gap-2.5 group shrink-0">
        <span className="grid place-items-center w-7 h-7 rounded-md bg-slate-900 text-white font-semibold text-sm group-hover:bg-pitch-700 transition-colors">
          W
        </span>
        <span className="text-slate-900 text-[15px] font-semibold tracking-tight hidden sm:block">
          World Cup&nbsp;
          <span className="text-slate-400 font-normal">Predictor</span>
        </span>
      </Link>
      <div className="flex items-center gap-4 sm:gap-7 ml-auto">
        {link("/", "Overview", pathname === "/")}
        {link("/my-predictions", "My Picks", pathname === "/my-predictions")}
        {link("/leaderboard", "Ranks", pathname === "/leaderboard")}
        <Link
          to="/bracket"
          className="text-[13px] font-semibold px-4 py-2 rounded-full bg-slate-900 text-white hover:bg-pitch-700 transition-colors"
        >
          Play bracket
        </Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-dvh bg-white text-slate-900">
        <Nav />
        <main className="px-4 sm:px-6 py-10 sm:py-14">
          <Routes>
            <Route path="/" element={<Analysis />} />
            <Route path="/analysis" element={<Navigate to="/" replace />} />
            <Route path="/bracket" element={<BracketChallenge />} />
            <Route
              path="/groups"
              element={<Navigate to="/bracket" replace />}
            />
            <Route path="/my-predictions" element={<MyPredictions />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
