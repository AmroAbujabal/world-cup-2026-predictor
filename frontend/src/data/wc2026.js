// FIFA World Cup 2026 — 48 teams, 12 groups (official draw, December 2024)
export const GROUPS = {
  A: ['Mexico',      'South Africa',          'South Korea',  'Czech Republic'],
  B: ['Canada',      'Bosnia and Herzegovina', 'Qatar',        'Switzerland'],
  C: ['Brazil',      'Morocco',               'Haiti',        'Scotland'],
  D: ['USA',         'Paraguay',              'Australia',    'Turkey'],
  E: ['Germany',     'Curacao',               'Ivory Coast',  'Ecuador'],
  F: ['Netherlands', 'Japan',                 'Sweden',       'Tunisia'],
  G: ['Belgium',     'Iran',                  'Egypt',        'New Zealand'],
  H: ['Spain',       'Uruguay',               'Saudi Arabia', 'Cape Verde'],
  I: ['France',      'Senegal',               'Iraq',         'Norway'],
  J: ['Argentina',   'Algeria',               'Austria',      'Jordan'],
  K: ['Portugal',    'DR Congo',              'Uzbekistan',   'Colombia'],
  L: ['England',     'Croatia',               'Ghana',        'Panama'],
};

export const GROUP_LABELS = Object.keys(GROUPS);

// Build R32 bracket from completed group picks + 8 best 3rd-place teams
// groupPicks: { A: { winner, runnerUp }, B: ... }
// thirdPlace: array of 8 team names (user-selected)
export function buildR32(groupPicks, thirdPlace) {
  const w = g => groupPicks[g]?.winner;
  const r = g => groupPicks[g]?.runnerUp;
  const t = i => thirdPlace[i];
  return [
    { id: 'r32_1',  team1: w('A'), team2: r('B') },
    { id: 'r32_2',  team1: w('B'), team2: r('A') },
    { id: 'r32_3',  team1: w('C'), team2: r('D') },
    { id: 'r32_4',  team1: w('D'), team2: r('C') },
    { id: 'r32_5',  team1: w('E'), team2: r('F') },
    { id: 'r32_6',  team1: w('F'), team2: r('E') },
    { id: 'r32_7',  team1: w('G'), team2: r('H') },
    { id: 'r32_8',  team1: w('H'), team2: r('G') },
    { id: 'r32_9',  team1: w('I'), team2: r('J') },
    { id: 'r32_10', team1: w('J'), team2: r('I') },
    { id: 'r32_11', team1: w('K'), team2: r('L') },
    { id: 'r32_12', team1: w('L'), team2: r('K') },
    { id: 'r32_13', team1: t(0),   team2: t(1) },
    { id: 'r32_14', team1: t(2),   team2: t(3) },
    { id: 'r32_15', team1: t(4),   team2: t(5) },
    { id: 'r32_16', team1: t(6),   team2: t(7) },
  ];
}
