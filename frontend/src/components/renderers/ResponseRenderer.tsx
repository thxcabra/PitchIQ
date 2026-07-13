import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Link } from "react-router-dom";
import type { ChatResponse, TableResponse, ChartResponse } from "../../types";
import ComparisonView from "../ComparisonView";
import RadarChart from "../RadarChart";
import TraceBadge from "../chat/TraceBadge";
import Icon from "../Icon";
import { money, num, percentileColor } from "../../lib/format";
import { SERIES, CHART } from "../../lib/colors";

// Renders any ChatResponse variant (table / chart / comparison / text / clarification / error).
export default function ResponseRenderer({
  resp, onAsk,
}: {
  resp: ChatResponse;
  onAsk: (q: string) => void;
}) {
  return (
    <div className="card p-4">
      <Body resp={resp} onAsk={onAsk} />
      <TraceBadge trace={resp.trace} />
    </div>
  );
}

function Body({ resp, onAsk }: { resp: ChatResponse; onAsk: (q: string) => void }) {
  switch (resp.type) {
    case "text":
      return (
        <div>
          {resp.title && <h3 className="font-semibold text-white mb-1">{resp.title}</h3>}
          <p className="text-pitch-sub whitespace-pre-line">{resp.text}</p>
        </div>
      );

    case "table":
      return <TableView resp={resp} />;

    case "chart":
      return <ChartView resp={resp} />;

    case "comparison":
      return (
        <div>
          <h3 className="font-semibold text-white mb-1">{resp.title}</h3>
          {resp.narrative && <p className="text-pitch-sub text-sm mb-3">{resp.narrative}</p>}
          <ComparisonView data={resp.data} />
        </div>
      );

    case "clarification":
      return (
        <div>
          <p className="text-pitch-text mb-3 flex items-center gap-2">
            <Icon name="help" size={18} className="text-pitch-accent2 shrink-0" /> {resp.message}
          </p>
          <div className="flex flex-wrap gap-2">
            {resp.options.map((o) => (
              <button key={o.query} className="btn hover:border-pitch-accent/50" onClick={() => onAsk(o.query)}>{o.label}</button>
            ))}
          </div>
        </div>
      );

    case "error":
      return (
        <div>
          <p className="text-rose-300 mb-2 flex items-center gap-2">
            <Icon name="alert" size={18} className="shrink-0" /> {resp.message}
          </p>
          {resp.suggestions.length > 0 && (
            <div>
              <p className="text-pitch-muted text-sm mb-2">Did you mean:</p>
              <div className="flex flex-wrap gap-2">
                {resp.suggestions.map((s) => (
                  <button key={s} className="btn" onClick={() => onAsk(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}
        </div>
      );
  }
}

function TableView({ resp }: { resp: TableResponse }) {
  const fmt = (kind: string, v: unknown) =>
    v == null ? "—"
      : kind === "money" ? money(v as number)
      : kind === "number" ? (Number.isInteger(v as number) ? String(v) : num(v as number))
      : String(v);
  return (
    <div>
      <h3 className="font-semibold text-white mb-1">{resp.title}</h3>
      {resp.narrative && <p className="text-pitch-sub text-sm mb-3">{resp.narrative}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-pitch-muted border-b border-pitch-line">
              {resp.columns.map((c) => (
                <th key={c.key} className={`py-2 pr-4 font-medium ${c.kind !== "text" ? "text-right" : ""}`}>
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {resp.rows.map((row, i) => (
              <tr key={i} className="border-b border-pitch-line/50 hover:bg-pitch-card2/60 transition-colors">
                {resp.columns.map((c) => (
                  <td key={c.key} className={`py-2.5 pr-4 text-pitch-sub ${c.kind !== "text" ? "text-right num" : ""}`}>
                    {c.key === "name" && row["player_id"] ? (
                      <Link className="text-white hover:text-pitch-accent transition-colors"
                            to={`/player/${row["player_id"]}`}>{String(row[c.key])}</Link>
                    ) : fmt(c.kind, row[c.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ChartView({ resp }: { resp: ChartResponse }) {
  const header = (
    <>
      <h3 className="font-semibold text-white mb-1">{resp.title}</h3>
      {resp.narrative && <p className="text-pitch-sub text-sm mb-3">{resp.narrative}</p>}
    </>
  );

  if (resp.chart_type === "radar") {
    const series = resp.series.map((s, i) => ({
      name: s.name, color: i === 0 ? SERIES.a : SERIES.b, values: s.values,
    }));
    return (
      <div>
        {header}
        <RadarChart categories={resp.categories} series={series} />
        {resp.footnote && <p className="text-xs text-pitch-muted mt-2">{resp.footnote}</p>}
      </div>
    );
  }

  // bar
  const data = resp.categories.map((c, i) => ({ category: c, value: resp.series[0]?.values[i] ?? 0 }));
  return (
    <div>
      {header}
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid stroke={CHART.grid} horizontal={false} />
          <XAxis type="number" tick={{ fill: CHART.axis, fontSize: 11 }}
                 domain={resp.value_kind === "percentile" ? [0, 100] : undefined} />
          <YAxis type="category" dataKey="category" width={120}
                 tick={{ fill: CHART.axis, fontSize: 11 }} />
          <Tooltip contentStyle={{ background: CHART.tooltipBg, border: `1px solid ${CHART.tooltipBorder}` }} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={resp.value_kind === "percentile" ? percentileColor(d.value) : SERIES.a} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {resp.footnote && <p className="text-xs text-pitch-muted mt-2">{resp.footnote}</p>}
    </div>
  );
}
