// A labelled stat tile. `numeric` renders the value in the mono figures font.
export default function Stat({ label, value, numeric }: { label: string; value: string; numeric?: boolean }) {
  return (
    <div className="card px-4 py-3">
      <div className="text-[11px] uppercase tracking-wider text-pitch-muted">{label}</div>
      <div className={`text-white font-semibold mt-0.5 truncate ${numeric ? "num" : ""}`}>{value}</div>
    </div>
  );
}
