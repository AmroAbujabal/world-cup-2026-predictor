// frontend/src/pages/NotFound.jsx
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="max-w-lg mx-auto text-center py-24">
      <div className="text-6xl font-black text-slate-200 mb-4">404</div>
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Page not found</h1>
      <p className="text-slate-500 mb-8 text-sm">That URL doesn't exist. Head back to the predictor.</p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white font-bold px-6 py-3 rounded-xl transition-colors text-sm"
      >
        Back to Group Stage
      </Link>
    </div>
  );
}
