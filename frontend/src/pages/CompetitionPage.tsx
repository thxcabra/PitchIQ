import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { CompetitionProfile } from "../types";
import Avatar, { Logo } from "../components/Avatar";
import Icon from "../components/Icon";
import NewsSection from "../components/NewsSection";
import Stat from "../components/Stat";
import { money } from "../lib/format";

export default function CompetitionPage() {
  const { name } = useParams();
  const [c, setC] = useState<CompetitionProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;
    setC(null); setError(null);
    api.competition(name).then(setC).catch((e) => setError(e.message));
  }, [name]);

  if (error) return <div className="text-center py-16 text-rose-300"><Icon name="alert" size={28} className="mx-auto mb-2" /> {error}</div>;
  if (!c) return <div className="space-y-6 animate-fade-up"><div className="skeleton h-20" /><div className="skeleton h-16" /><div className="skeleton h-96" /></div>;

  const comp = c.competition;
  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex items-center gap-4">
        {comp.flag ? <Logo src={comp.flag} size={44} className="rounded-sm ring-1 ring-pitch-line" />
          : <span className="grid place-items-center w-12 h-12 rounded-lg bg-pitch-accent/15 text-pitch-accent"><Icon name="trophy" size={24} /></span>}
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">{comp.competition}</h1>
          <p className="text-pitch-sub mt-0.5">{comp.type} · {comp.country}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Stat label="Players" value={c.player_count.toLocaleString("en-US")} numeric />
        <Stat label="Clubs" value={`${c.club_count}`} numeric />
        <Stat label="Total goals" value={Math.round(c.total_goals).toLocaleString("en-US")} numeric />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4">
          <h2 className="font-semibold text-white mb-3">Top scorers</h2>
          <div className="space-y-1">
            {c.top_scorers.map((p, i) => (
              <Link key={p.player_id} to={`/player/${p.player_id}`}
                    className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-pitch-card2/60 transition-colors">
                <span className="text-pitch-muted num w-5 text-right">{i + 1}</span>
                <Avatar src={p.photo} name={p.name} size={32} />
                <div className="min-w-0 flex-1">
                  <div className="text-white truncate">{p.name}</div>
                  <div className="text-xs text-pitch-muted flex items-center gap-1"><Logo src={p.club_logo} size={13} /> {p.club}</div>
                </div>
                <span className="text-pitch-accent font-semibold num">{money(p.market_value_eur)}</span>
              </Link>
            ))}
          </div>
        </div>

        <div className="card p-4">
          <h2 className="font-semibold text-white mb-3">Clubs <span className="text-pitch-muted text-sm font-normal">· by goals</span></h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
            {c.clubs.map((club) => (
              <Link key={club.club_id} to={`/team/${club.club_id}`}
                    className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-pitch-card2/60 transition-colors">
                <Logo src={club.logo} size={22} />
                <span className="text-pitch-sub truncate flex-1">{club.name}</span>
                <span className="text-pitch-muted num text-sm">{Math.round(club.goals)}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <NewsSection query={comp.competition} />
    </div>
  );
}
