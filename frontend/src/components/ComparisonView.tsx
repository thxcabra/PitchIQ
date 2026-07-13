import type { ComparisonResult, PlayerSummary } from "../types";
import RadarChart from "./RadarChart";
import Avatar from "./Avatar";
import { money, num } from "../lib/format";
import { SERIES } from "../lib/colors";

const A_COLOR = SERIES.a;
const B_COLOR = SERIES.b;

// Overlaid radar + per-metric diverging bars (percentile-scaled) + market context.
export default function ComparisonView({ data }: { data: ComparisonResult }) {
  const { player_a: a, player_b: b, market_context: mkt } = data;

  const radar = [
    { name: a.name, color: A_COLOR, values: data.metrics.map((m) => m.a_percentile) },
    { name: b.name, color: B_COLOR, values: data.metrics.map((m) => m.b_percentile) },
  ];
  const winnerName = data.overall_winner === "a" ? a.name
    : data.overall_winner === "b" ? b.name : "Even";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <Side p={a} color={A_COLOR} align="left" />
        <div className="text-center shrink-0">
          <div className="text-[11px] uppercase tracking-wider text-pitch-muted">Edge</div>
          <div className="font-bold text-white">{winnerName}</div>
          <div className="text-xs text-pitch-muted num">{data.wins.a}-{data.wins.b} metrics</div>
        </div>
        <Side p={b} color={B_COLOR} align="right" />
      </div>

      <div className="card p-4">
        <RadarChart categories={data.metrics.map((m) => m.label)} series={radar} height={320} />
      </div>

      <div className="card p-4 space-y-3">
        {data.metrics.map((m) => (
          <div key={m.metric}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className={`num ${m.winner === "a" ? "text-white font-semibold" : "text-pitch-muted"}`}>
                {num(m.a_value)}
              </span>
              <span className="text-pitch-sub text-xs">{m.label}</span>
              <span className={`num ${m.winner === "b" ? "text-white font-semibold" : "text-pitch-muted"}`}>
                {num(m.b_value)}
              </span>
            </div>
            <div className="flex items-center gap-1 h-2.5">
              <div className="flex-1 flex justify-end">
                <div className="h-full rounded-l-full" style={{
                  width: `${m.a_percentile ?? 0}%`, background: A_COLOR,
                  opacity: m.winner === "a" ? 1 : 0.45,
                }} />
              </div>
              <div className="w-px h-full bg-pitch-line" />
              <div className="flex-1">
                <div className="h-full rounded-r-full" style={{
                  width: `${m.b_percentile ?? 0}%`, background: B_COLOR,
                  opacity: m.winner === "b" ? 1 : 0.45,
                }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-4 flex items-center justify-between">
        <MarketSideView name={a.name} value={mkt.a.market_value_eur} pctl={mkt.a.value_percentile} color={A_COLOR} />
        <div className="text-[11px] uppercase tracking-wider text-pitch-muted">Market value</div>
        <MarketSideView name={b.name} value={mkt.b.market_value_eur} pctl={mkt.b.value_percentile} color={B_COLOR} right />
      </div>
    </div>
  );
}

function Side({ p, color, align }: { p: PlayerSummary; color: string; align: "left" | "right" }) {
  return (
    <div className={`flex items-center gap-3 min-w-0 ${align === "right" ? "flex-row-reverse text-right" : ""}`}>
      <Avatar src={p.photo} name={p.name} size={48} />
      <div className="min-w-0">
        <div className="font-bold text-lg truncate" style={{ color }}>{p.name}</div>
        <div className="text-sm text-pitch-sub truncate">{p.role} · {p.club}</div>
      </div>
    </div>
  );
}

function MarketSideView({ name, value, pctl, color, right }: {
  name: string; value: number | null; pctl: number | null; color: string; right?: boolean;
}) {
  return (
    <div className={right ? "text-right" : ""}>
      <div className="font-semibold num" style={{ color }}>{money(value)}</div>
      <div className="text-xs text-pitch-muted num">
        {pctl != null ? `${Math.round(pctl)}th pct in cohort` : name}
      </div>
    </div>
  );
}
