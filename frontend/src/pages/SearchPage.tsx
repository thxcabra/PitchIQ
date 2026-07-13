import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type SearchFilters } from "../api/client";
import type { Meta, PlayerSummary } from "../types";
import PlayerCard from "../components/PlayerCard";
import Icon from "../components/Icon";

const BROAD = ["Forward", "Midfielder", "Defender", "Goalkeeper"];

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {Array.from({ length: 9 }).map((_, i) => <div key={i} className="skeleton h-[104px]" />)}
    </div>
  );
}

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [position, setPosition] = useState("");
  const [country, setCountry] = useState("");
  const [competition, setCompetition] = useState("");
  const [club, setClub] = useState("");
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(false);
  const timer = useRef<number>();
  const nav = useNavigate();

  useEffect(() => { api.meta().then(setMeta).catch(() => {}); }, []);

  // competitions available for the chosen country (or all)
  const competitions = useMemo(() => {
    if (!meta) return [];
    const idx = country ? meta.competition_index.filter((c) => c.country === country) : meta.competition_index;
    return idx.map((c) => c.competition);
  }, [meta, country]);

  // if the selected competition no longer belongs to the country, clear it
  useEffect(() => {
    if (competition && !competitions.includes(competition)) setCompetition("");
  }, [competitions, competition]);

  const anyFilter = position || country || competition || club;

  useEffect(() => {
    window.clearTimeout(timer.current);
    // `position` holds a broad position OR a detailed role — route it to the right filter
    const isBroad = BROAD.includes(position);
    const filters: SearchFilters = {
      position: isBroad ? position : undefined,
      role: position && !isBroad ? position : undefined,
      country, competition, club,
    };
    if (q.trim().length < 2 && !anyFilter) { setResults([]); setTotal(0); return; }
    timer.current = window.setTimeout(async () => {
      setLoading(true);
      try {
        const r = await api.search(q, filters, 60);
        setResults(r.results); setTotal(r.total);
      } finally { setLoading(false); }
    }, 220);
    return () => window.clearTimeout(timer.current);
  }, [q, position, country, competition, club, anyFilter]);

  return (
    <div className="space-y-6">
      <section className="text-center py-6">
        <h1 className="text-3xl font-bold text-white">
          Scout <span className="text-pitch-accent">European</span> football
        </h1>
        <p className="text-pitch-sub mt-2">
          {meta
            ? `${meta.player_count.toLocaleString("en-US")} players · ${meta.competitions.length} competitions · ${meta.season}`
            : "Loading…"}
        </p>
        <div className="max-w-xl mx-auto mt-5 relative">
          <Icon name="search" size={18}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-pitch-muted pointer-events-none" />
          <input
            autoFocus
            className="input text-lg pl-11"
            placeholder="Search a player… (e.g. Haaland, Mbappé, Lautaro)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        {/* filter by position / country → competition / club */}
        <div className="max-w-3xl mx-auto mt-3 flex flex-wrap gap-2 justify-center">
          <select className="input max-w-[12rem]" value={position} onChange={(e) => setPosition(e.target.value)}>
            <option value="">Any position</option>
            {(meta?.role_groups ?? BROAD.map((p) => ({ position: p, roles: [] }))).map((g) => (
              <optgroup key={g.position} label={g.position}>
                <option value={g.position}>All {g.position.toLowerCase()}s</option>
                {g.roles.map((r) => <option key={r} value={r}>{r}</option>)}
              </optgroup>
            ))}
          </select>
          <select className="input max-w-[11rem]" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">Any country</option>
            {meta?.countries.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="input max-w-[15rem]" value={competition} onChange={(e) => setCompetition(e.target.value)}>
            <option value="">{country ? `All ${country} competitions` : "Any competition"}</option>
            {competitions.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input className="input max-w-[11rem]" placeholder="Club filter…" value={club}
                 onChange={(e) => setClub(e.target.value)} />
          {anyFilter && (
            <button className="btn" onClick={() => { setPosition(""); setCountry(""); setCompetition(""); setClub(""); }}>
              Clear
            </button>
          )}
        </div>

        <button className="btn mt-4" onClick={() => nav("/chat")}>
          <Icon name="chat" size={16} /> Or just ask a question <Icon name="arrowRight" size={15} />
        </button>
      </section>

      {loading && results.length === 0 && <SkeletonGrid />}

      {results.length > 0 && (
        <>
          <p className="text-center text-pitch-muted text-sm">
            Showing <span className="text-pitch-sub num">{results.length}</span>
            {total > results.length ? <> of <span className="text-pitch-sub num">{total.toLocaleString("en-US")}</span></> : ""} players
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {results.map((p) => <PlayerCard key={p.player_id} p={p} />)}
          </div>
          {total > results.length && (
            <p className="text-center text-pitch-muted text-xs">Narrow the filters to see more specific results.</p>
          )}
        </>
      )}

      {!loading && (q.trim().length >= 2 || anyFilter) && results.length === 0 && (
        <div className="text-center py-12 text-pitch-muted">
          <Icon name="search" size={28} className="mx-auto mb-2 opacity-40" />
          <p>No players match those filters.</p>
        </div>
      )}
    </div>
  );
}
