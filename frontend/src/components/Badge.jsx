// frontend/src/components/Badge.jsx
// Small status pill. tone → color; matches the app's rounded-full pill vocabulary.
const TONES = {
  amber: "bg-amber-100 text-amber-700 border-amber-300",
  green: "bg-green-100 text-green-700 border-green-300",
  sky: "bg-sky-100 text-sky-700 border-sky-300",
  slate: "bg-slate-100 text-slate-600 border-slate-300",
  red: "bg-red-100 text-red-600 border-red-300",
};

export default function Badge({ children, tone = "slate", className = "" }) {
  return (
    <span
      className={`inline-flex items-center gap-1 border text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${TONES[tone] || TONES.slate} ${className}`}
    >
      {children}
    </span>
  );
}
