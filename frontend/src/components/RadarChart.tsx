import {
  PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart as RC, ResponsiveContainer,
  Legend, Tooltip,
} from "recharts";
import { CHART } from "../lib/colors";

export interface RadarSeries {
  name: string;
  color: string;
  values: (number | null)[];
}

// Renders one or more series over shared categories on a 0-100 (percentile) scale.
export default function RadarChart({
  categories, series, height = 340,
}: {
  categories: string[];
  series: RadarSeries[];
  height?: number;
}) {
  // key series by index (not by player name) — dataKeys with spaces/accents can fail to bind
  const data = categories.map((cat, i) => {
    const row: Record<string, number | string | null> = { category: cat };
    series.forEach((s, si) => (row[`s${si}`] = s.values[i]));
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RC data={data} outerRadius="72%">
        <PolarGrid stroke={CHART.grid} />
        <PolarAngleAxis dataKey="category" tick={{ fill: CHART.axis, fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: CHART.tick, fontSize: 9 }} axisLine={false} tickCount={5} />
        {series.map((s, si) => (
          <Radar key={si} name={s.name} dataKey={`s${si}`} stroke={s.color}
                 fill={s.color} fillOpacity={0.28} strokeWidth={2} isAnimationActive={false}
                 dot={{ r: 2.5, fill: s.color, strokeWidth: 0 }} />
        ))}
        <Tooltip
          contentStyle={{ background: CHART.tooltipBg, border: `1px solid ${CHART.tooltipBorder}`, borderRadius: 10, fontSize: 12 }}
          labelStyle={{ color: CHART.axis }}
          formatter={(v: number, n: string) => [`${Math.round(v)}th pct`, n]}
        />
        {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />}
      </RC>
    </ResponsiveContainer>
  );
}
