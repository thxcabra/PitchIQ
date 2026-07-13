import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { PlayerSummary } from "../types";
import { money } from "../lib/format";

export default function PlayerPicker({
  label, selected, onSelect,
}: {
  label: string;
  selected: PlayerSummary | null;
  onSelect: (p: PlayerSummary | null) => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const timer = useRef<number>();

  useEffect(() => {
    window.clearTimeout(timer.current);
    if (q.trim().length < 2) { setResults([]); return; }
    timer.current = window.setTimeout(async () => {
      setResults((await api.search(q, {}, 8)).results);
      setOpen(true);
    }, 200);
    return () => window.clearTimeout(timer.current);
  }, [q]);

  if (selected) {
    return (
      <div className="card p-4 flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-pitch-muted">{label}</div>
          <div className="font-semibold text-white">{selected.name}</div>
          <div className="text-sm text-pitch-sub">
            {selected.role} · {selected.club} · {money(selected.market_value_eur)}
          </div>
        </div>
        <button className="btn" onClick={() => { onSelect(null); setQ(""); }}>Change</button>
      </div>
    );
  }

  return (
    <div className="relative">
      <label className="text-xs uppercase tracking-wide text-pitch-muted">{label}</label>
      <input
        className="input mt-1"
        placeholder="Search a player…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
      />
      {open && results.length > 0 && (
        <ul className="absolute z-20 mt-1 w-full card overflow-hidden shadow-xl">
          {results.map((p) => (
            <li key={p.player_id}>
              <button
                className="w-full text-left px-4 py-2 hover:bg-pitch-line/60 transition-colors"
                onClick={() => { onSelect(p); setOpen(false); }}
              >
                <span className="text-white">{p.name}</span>
                <span className="text-pitch-muted text-sm"> · {p.club} · {p.role}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
