export function money(v: number | null | undefined): string {
  if (v == null) return "n/d";
  if (v >= 1_000_000) return `€${(v / 1_000_000).toFixed(v >= 10_000_000 ? 0 : 1)}M`;
  if (v >= 1_000) return `€${(v / 1_000).toFixed(0)}K`;
  return `€${v}`;
}

export function num(v: number | null | undefined, digits = 2): string {
  if (v == null) return "—";
  return Number(v).toFixed(digits);
}

export function pct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${Math.round(v)}`;
}

// green (elite) -> amber -> red (poor), for percentile chips
export function percentileColor(p: number | null | undefined): string {
  if (p == null) return "#64748b";
  if (p >= 80) return "#22c55e";
  if (p >= 60) return "#84cc16";
  if (p >= 40) return "#eab308";
  if (p >= 20) return "#f97316";
  return "#ef4444";
}
