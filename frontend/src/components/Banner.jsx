// frontend/src/components/Banner.jsx
// Full-width notice strip. tone → color scheme. Optional eyebrow + accent left rule.
const TONES = {
  amber: "bg-amber-50 border-amber-300 text-amber-900",
  green: "bg-green-50 border-green-300 text-green-900",
  sky: "bg-sky-50 border-sky-200 text-sky-900",
  slate: "bg-slate-50 border-slate-200 text-slate-800",
  red: "bg-red-50 border-red-200 text-red-900",
  gold: "bg-gold-50 border-gold-300 text-gold-900",
};

const EYEBROW = {
  amber: "text-amber-600",
  green: "text-green-600",
  sky: "text-sky-600",
  slate: "text-slate-500",
  red: "text-red-600",
  gold: "text-gold-700",
};

export default function Banner({
  tone = "slate",
  eyebrow,
  title,
  children,
  icon,
  action,
  className = "",
}) {
  return (
    <div
      className={`border rounded-2xl px-5 py-4 flex items-start gap-4 ${TONES[tone] || TONES.slate} ${className}`}
    >
      {icon && (
        <div className="text-2xl leading-none shrink-0 mt-0.5">{icon}</div>
      )}
      <div className="flex-1 min-w-0">
        {eyebrow && (
          <p
            className={`text-[11px] font-bold uppercase tracking-widest mb-0.5 ${EYEBROW[tone]}`}
          >
            {eyebrow}
          </p>
        )}
        {title && (
          <p className="font-display text-lg font-bold leading-tight">
            {title}
          </p>
        )}
        {children && (
          <div className="text-sm mt-0.5 opacity-90">{children}</div>
        )}
      </div>
      {action && <div className="shrink-0 self-center">{action}</div>}
    </div>
  );
}
