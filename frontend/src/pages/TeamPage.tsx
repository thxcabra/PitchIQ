import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { TeamProfile } from "../types";
import Avatar, { Logo } from "../components/Avatar";
import Icon from "../components/Icon";
import NewsSection from "../components/NewsSection";
import Stat from "../components/Stat";
import { money, num } from "../lib/format";

export default function TeamPage() {
  const { id } = useParams();
  const [t, setT] = useState<TeamProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setT(null); setError(null);
    api.team(Number(id)).then(setT).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="text-center py-16 text-rose-300"><Icon name="alert" size={28} className="mx-auto mb-2" /> {error}</div>;
  if (!t) return <div className="space-y-6 animate-fade-up"><div className="skeleton h-20" /><div className="skeleton h-16" /><div className="skeleton h-96" /></div>;

  const c = t.club;
  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex items-center gap-4">
        {c.logo ? <Logo src={c.logo} size={64} /> : <Avatar src={null} name={c.name} size={64} />}
        <div className="min-w-0">
          <h1 className="text-3xl font-bold text-white tracking-tight truncate">{c.name}</h1>
          <p className="text-pitch-sub mt-0.5 flex items-center gap-1.5 flex-wrap">
            {c.competition && (
              <Link to={`/competition/${encodeURIComponent(c.competition)}`} className="hover:text-white transition-colors">
                {c.competition}
              </Link>
            )}
            {c.country && <><span className="text-pitch-muted">·</span><span>{c.country}</span></>}
            {c.coach && <><span className="text-pitch-muted">·</span><span>{c.coach}</span></>}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Squad" value={`${t.squad_count}`} />
        <Stat label="Avg age" value={c.avg_age ? num(c.avg_age, 1) : "—"} />
        <Stat label="Total goals" value={`${Math.round(t.total_goals)}`} />
        <Stat label="Top scorer" value={t.top_scorer ? `${t.top_scorer.player.name} (${Math.round(t.top_scorer.goals)})` : "—"} />
      </div>

      {c.stadium && (
        <p className="text-sm text-pitch-muted flex items-center gap-2">
          <Icon name="trophy" size={15} /> {c.stadium}
          {c.stadium_seats ? <span className="num">· {c.stadium_seats.toLocaleString("en-US")} seats</span> : null}
          {t.competitions.length > 0 && <span>· {t.competitions.join(" · ")}</span>}
        </p>
      )}

      <div className="card p-4">
        <h2 className="font-semibold text-white mb-3">Squad <span className="text-pitch-muted text-sm font-normal">· 2025-26</span></h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-pitch-muted border-b border-pitch-line">
                <th className="py-2 pr-4 font-medium">Player</th>
                <th className="py-2 pr-4 font-medium">Role</th>
                <th className="py-2 pr-4 font-medium text-right">Value</th>
                <th className="py-2 pr-4 font-medium text-right">Games</th>
                <th className="py-2 pr-4 font-medium text-right">Goals</th>
                <th className="py-2 pr-4 font-medium text-right">Assists</th>
              </tr>
            </thead>
            <tbody>
              {t.squad.map((s) => (
                <tr key={s.player.player_id} className="border-b border-pitch-line/50 hover:bg-pitch-card2/60 transition-colors">
                  <td className="py-2 pr-4">
                    <Link to={`/player/${s.player.player_id}`} className="flex items-center gap-2.5 text-white hover:text-pitch-accent transition-colors">
                      <Avatar src={s.player.photo} name={s.player.name} size={30} /> {s.player.name}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-pitch-sub">{s.player.role}</td>
                  <td className="py-2 pr-4 text-right num text-pitch-accent">{money(s.player.market_value_eur)}</td>
                  <td className="py-2 pr-4 text-right num">{Math.round(s.matches)}</td>
                  <td className="py-2 pr-4 text-right num text-white">{Math.round(s.goals)}</td>
                  <td className="py-2 pr-4 text-right num">{Math.round(s.assists)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <NewsSection query={c.name} />
    </div>
  );
}
