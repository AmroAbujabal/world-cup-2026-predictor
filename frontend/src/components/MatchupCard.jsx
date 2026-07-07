// frontend/src/components/MatchupCard.jsx

const KICKOFF_FMT = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function formatKickoff(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return KICKOFF_FMT.format(d).replace(",", " ·");
}

function kickoffPassed(iso) {
  if (!iso) return false;
  const d = new Date(iso);
  return !Number.isNaN(d.getTime()) && d.getTime() <= Date.now();
}

function StatusBar({
  status,
  homeScore,
  awayScore,
  matchDate,
  penaltyHome,
  penaltyAway,
  wentToPenalties,
  locked,
}) {
  if (status === "final" && homeScore != null) {
    return (
      <div className="px-3 py-1.5 bg-pitch-700 flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-widest text-white/70">
          FULL TIME
        </span>
        <span className="font-display text-base text-white nums leading-none">
          {homeScore}
          <span className="text-gold-400 mx-0.5">–</span>
          {awayScore}
          {wentToPenalties && penaltyHome != null && (
            <span className="text-gold-400 font-sans text-[10px] ml-1 align-middle">
              ({penaltyHome}-{penaltyAway}p)
            </span>
          )}
        </span>
      </div>
    );
  }
  if (status === "live") {
    return (
      <div className="px-3 py-1.5 bg-red-600 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse inline-block" />
        <span className="text-[10px] font-bold tracking-widest text-white">
          LIVE NOW
        </span>
      </div>
    );
  }
  const kickoff = formatKickoff(matchDate);
  return (
    <div
      className={`px-3 py-1.5 flex items-center justify-between ${locked ? "bg-red-50" : "bg-gold-400"}`}
    >
      <span
        className={`text-[10px] font-bold tracking-widest ${locked ? "text-red-600" : "text-pitch-950"}`}
      >
        {locked ? "LOCKED" : "UPCOMING"}
      </span>
      {kickoff && (
        <span
          className={`text-[10px] font-bold nums ${locked ? "text-red-400" : "text-pitch-900"}`}
        >
          {kickoff}
        </span>
      )}
    </div>
  );
}

// Three-way Win / Draw / Loss energy bar
function ProbBar({ home, draw, away, live }) {
  const p = (v) => `${Math.round(v * 100)}%`;
  return (
    <div className="px-2.5 py-2 bg-slate-50 border-t-2 border-slate-100">
      <div
        className={`flex h-2 rounded-full overflow-hidden bg-slate-200 ${live ? "shimmer" : ""}`}
      >
        <div className="bg-pitch-500" style={{ width: p(home) }} />
        <div className="bg-slate-400" style={{ width: p(draw) }} />
        <div className="bg-electric-500" style={{ width: p(away) }} />
      </div>
      <div className="flex justify-between mt-1 text-[9px] font-bold tracking-wide nums">
        <span className="text-pitch-600">W {p(home)}</span>
        <span className="text-slate-400">D {p(draw)}</span>
        <span className="text-electric-600">L {p(away)}</span>
      </div>
    </div>
  );
}

export default function MatchupCard({
  matchup,
  onPick,
  userPick,
  loadingProbs,
}) {
  const {
    id,
    team1,
    team2,
    prob1,
    prob2,
    status,
    homeScore,
    awayScore,
    matchDate,
    probHome,
    probDraw,
    probAway,
    wentToPenalties,
    penaltyHome,
    penaltyAway,
    isUpset,
  } = matchup;

  const isFinal = status === "final";
  const isLive = status === "live";
  const passed = kickoffPassed(matchDate);
  const locked = isFinal || isLive || passed;
  const has3Way = probHome != null && probDraw != null && probAway != null;

  if (!team1 && !team2)
    return (
      <div className="w-44 rounded-2xl border-2 border-dashed border-slate-200 bg-white/50 p-4 grid place-items-center text-[11px] font-bold text-slate-300 tracking-widest h-[92px]">
        TBD
      </div>
    );

  const penWinnerHome =
    wentToPenalties && penaltyHome != null && penaltyHome > penaltyAway;
  const penWinnerAway =
    wentToPenalties && penaltyAway != null && penaltyAway > penaltyHome;
  const homeWon = isFinal && (homeScore > awayScore || penWinnerHome);
  const awayWon = isFinal && (awayScore > homeScore || penWinnerAway);

  return (
    <div className="w-44 relative pop">
      {isUpset && (
        <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 z-20 bg-gold-400 text-pitch-950 text-[9px] font-display px-2 py-0.5 rounded-full shadow-md tracking-wide">
          UPSET
        </span>
      )}
      <div
        className={`bg-white rounded-2xl overflow-hidden shadow-[0_2px_10px_rgba(5,56,37,0.08)] border-2 transition-transform ${
          isUpset
            ? "border-gold-400 shadow-[0_0_18px_rgba(251,191,36,0.35)]"
            : "border-slate-200"
        } ${!locked ? "hover:-translate-y-0.5" : ""}`}
      >
        <StatusBar
          status={status}
          homeScore={homeScore}
          awayScore={awayScore}
          matchDate={matchDate}
          penaltyHome={penaltyHome}
          penaltyAway={penaltyAway}
          wentToPenalties={wentToPenalties}
          locked={locked}
        />

        {[
          {
            team: team1,
            prob: has3Way ? probHome : prob1,
            outcome: "home_win",
            won: homeWon,
          },
          {
            team: team2,
            prob: has3Way ? probAway : prob2,
            outcome: "away_win",
            won: awayWon,
          },
        ].map(({ team, prob, outcome, won }, i) => {
          if (!team)
            return (
              <div
                key={i}
                className={`px-3 py-2.5 text-[11px] text-slate-300 font-bold ${i === 0 ? "border-b border-slate-100" : ""}`}
              >
                TBD
              </div>
            );
          const picked = userPick === team;
          const otherPicked = userPick && userPick !== team;
          const clickable = !locked && !!team2;
          return (
            <button
              key={i}
              onClick={() => clickable && onPick(id, team, outcome)}
              disabled={!clickable}
              className={`w-full px-3 py-2.5 text-left transition-colors ${clickable ? "cursor-pointer" : "cursor-default"}
              ${i === 0 ? "border-b border-slate-100" : ""}
              ${won ? "bg-gold-50" : picked ? "bg-pitch-700 text-white" : otherPicked ? "bg-slate-50 text-slate-400" : clickable ? "hover:bg-pitch-50 text-slate-800" : "text-slate-700"}
            `}
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className={`font-display text-[13px] leading-tight truncate ${won ? "text-gold-600" : ""}`}
                >
                  {team}
                </span>
                <span
                  className={`text-[11px] font-bold shrink-0 nums ${
                    isFinal
                      ? won
                        ? "text-gold-500"
                        : "text-slate-300"
                      : picked
                        ? "text-gold-300"
                        : "text-slate-400"
                  }`}
                >
                  {isFinal
                    ? won
                      ? "✓"
                      : ""
                    : prob != null && !loadingProbs
                      ? `${Math.round(prob * 100)}%`
                      : loadingProbs
                        ? "…"
                        : ""}
                </span>
              </div>
            </button>
          );
        })}

        {!isFinal && has3Way && team1 && team2 && (
          <ProbBar
            home={probHome}
            draw={probDraw}
            away={probAway}
            live={isLive}
          />
        )}

        {isFinal && wentToPenalties && (
          <div className="px-3 py-1 bg-gold-50 border-t border-gold-100 text-[9px] font-semibold text-gold-700/80 leading-tight">
            Penalties — counts as a draw
          </div>
        )}
      </div>
    </div>
  );
}
