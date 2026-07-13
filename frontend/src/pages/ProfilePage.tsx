import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { PlayerProfile } from "../types";
import RadarChart from "../components/RadarChart";
import Icon from "../components/Icon";
import Avatar, { Logo } from "../components/Avatar";
import PlayerCard from "../components/PlayerCard";
import NewsSection from "../components/NewsSection";
import InfoTip from "../components/InfoTip";
import Stat from "../components/Stat";
import { money, num, pct, percentileColor } from "../lib/format";
import { SERIES } from "../lib/colors";

const T_PERCENTILE = "Percentile ranks a player against others in the same position and competition. 100 = best in that group, 50 = the group average. Cards are colour-coded green (elite) to red (low).";
const T_PER90 = "“/90” means per 90 minutes played, so players with different game time compare fairly. E.g. 0.8 goals /90 is roughly a goal every 112 minutes.";
const T_XG = "xG (expected goals) is the quality of the chances a player takes, from shot location and type. xA is the same idea for chances created. All figures come from real match data — never estimated by AI.";

const POS_ACCENT: Record<string, string> = {
  Forward: "text-rose-300", Midfielder: "text-emerald-300",
  Defender: "text-sky-300", Goalkeeper: "text-amber-300",
};

export default function ProfilePage() {
  const { id } = useParams();
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setProfile(null); setError(null);
    api.profile(id).then(setProfile).catch((e) => setError(e.message));
  }, [id]);

  if (error) return (
    <div className="text-center py-16 text-rose-300">
      <Icon name="alert" size={28} className="mx-auto mb-2" /> Could not load player: {error}
    </div>
  );
  if (!profile) return (
    <div className="space-y-6 animate-fade-up">
      <div className="skeleton h-10 w-64" />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-16" />)}</div>
      <div className="skeleton h-24" /><div className="skeleton h-40" />
    </div>
  );

  const p = profile.player;
  const radar = [{ name: p.name, color: SERIES.a, values: profile.metrics.map((m) => m.percentile) }];

  return (
    <div className="space-y-6 animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4 min-w-0">
          <Avatar src={p.photo} name={p.name} size={72} />
          <div className="min-w-0">
            <h1 className="text-3xl font-bold text-white tracking-tight truncate">{p.name}</h1>
            <p className="text-pitch-sub mt-0.5 flex items-center gap-1.5 flex-wrap">
              <span className={`font-medium ${POS_ACCENT[p.position] ?? ""}`}>{p.role}</span>
              <span className="text-pitch-muted">·</span>
              {p.club_id ? (
                <Link to={`/team/${p.club_id}`} className="inline-flex items-center gap-1 hover:text-white transition-colors">
                  <Logo src={p.club_logo} size={16} /> {p.club}
                </Link>
              ) : <span>{p.club}</span>}
              {p.nation && <><span className="text-pitch-muted">·</span><span>{p.nation}</span></>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {profile.rating != null && (
            <div className="text-center px-3">
              <div className="text-3xl font-bold num" style={{ color: percentileColor(profile.rating) }}>
                {Math.round(profile.rating)}
              </div>
              <div className="text-[10px] uppercase tracking-wider text-pitch-muted">rating</div>
            </div>
          )}
          <Link to={`/compare?a=${p.player_id}`} className="btn btn-accent">
            <Icon name="scale" size={16} /> Compare <Icon name="arrowRight" size={15} />
          </Link>
        </div>
      </div>

      {(profile.strengths.length > 0 || profile.weaknesses.length > 0) && (
        <div className="flex flex-wrap gap-2">
          {profile.strengths.map((s) => (
            <span key={s.label} className="chip bg-emerald-500/15 text-emerald-300">
              <Icon name="bolt" size={12} /> {s.label} · {pct(s.percentile)}
            </span>
          ))}
          {profile.weaknesses.map((w) => (
            <span key={w.label} className="chip bg-rose-500/12 text-rose-300/90">
              {w.label} · {pct(w.percentile)}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Position" value={p.role} />
        <Stat label="Age" value={p.age ? `${p.age}` : "—"} />
        <Stat label="Main competition" value={p.competition} />
        <Stat label="Market value" value={money(p.market_value_eur)} />
      </div>

      <div className="card p-4">
        <h2 className="font-semibold text-white mb-3 flex items-center gap-1.5">Season totals
          <span className="text-pitch-muted text-sm font-normal"> · 2025-26 · all competitions</span>
          <InfoTip text="Raw season totals summed across every competition this player featured in (league, cups, continental, internationals). xG/Shots/Key passes are available for the Big-5 leagues only." />
        </h2>
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-y-4 gap-x-2">
          {profile.totals.map((t) => (
            <div key={t.key} className="text-center border-l border-pitch-line first:border-l-0 sm:border-l">
              <div className="text-2xl font-bold text-white num">
                {t.value == null ? <span className="text-pitch-muted">—</span>
                  : t.key === "xg" || t.key === "xa" ? num(t.value, 1)
                  : Math.round(t.value).toLocaleString("en-US")}
              </div>
              <div className="text-[11px] uppercase tracking-wide text-pitch-muted mt-0.5">{t.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-4">
        <h2 className="font-semibold text-white mb-3">Competitions this season</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-pitch-muted border-b border-pitch-line">
                <th className="py-2 pr-4 font-medium">Competition</th>
                <th className="py-2 pr-4 font-medium">Club</th>
                <th className="py-2 pr-4 font-medium text-right">Games</th>
                <th className="py-2 pr-4 font-medium text-right">Minutes</th>
                <th className="py-2 pr-4 font-medium text-right">Goals</th>
                <th className="py-2 pr-4 font-medium text-right">Assists</th>
              </tr>
            </thead>
            <tbody>
              {profile.breakdown.map((b, i) => (
                <tr key={i} className="border-b border-pitch-line/50 hover:bg-pitch-card2/60 transition-colors">
                  <td className="py-2.5 pr-4 text-white">
                    <Link to={`/competition/${encodeURIComponent(b.competition)}`}
                          className="hover:text-pitch-accent transition-colors">{b.competition}</Link>
                    <span className="ml-2 chip bg-pitch-line2/50 text-pitch-sub">{b.competition_type}</span>
                  </td>
                  <td className="py-2.5 pr-4 text-pitch-sub">{b.club}</td>
                  <td className="py-2.5 pr-4 text-right num">{b.matches ?? "—"}</td>
                  <td className="py-2.5 pr-4 text-right num">{b.minutes?.toLocaleString("en-US") ?? "—"}</td>
                  <td className="py-2.5 pr-4 text-right text-white num">{b.goals ?? "—"}</td>
                  <td className="py-2.5 pr-4 text-right num">{b.assists ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4">
          <h2 className="font-semibold text-white mb-1 flex items-center gap-2">
            <Icon name="radar" size={16} className="text-pitch-accent" /> Performance radar
            <InfoTip text={T_PERCENTILE} />
          </h2>
          <p className="text-xs text-pitch-muted mb-2">
            Each spoke is a percentile vs {profile.cohort_label} ({profile.cohort_size} players). 50 = average, 100 = best.
          </p>
          <RadarChart categories={profile.metrics.map((m) => m.label)} series={radar} />
        </div>

        <div className="card p-4">
          <h2 className="font-semibold text-white mb-1 flex items-center gap-1.5">
            Contextualised metrics <InfoTip text={T_PERCENTILE} />
          </h2>
          <p className="text-xs text-pitch-muted mb-3">
            value <span className="text-pitch-sub">·90</span> vs cohort average · percentile
          </p>
          <div className="space-y-3.5">
            {profile.metrics.map((m) => (
              <div key={m.metric}>
                <div className="flex items-center justify-between text-sm mb-1.5">
                  <span className="text-pitch-sub">{m.label}</span>
                  <span className="text-pitch-sub num">
                    {num(m.value)} <span className="text-pitch-muted">· avg {num(m.cohort_average)}</span>
                    <span className="ml-2 font-semibold num" style={{ color: percentileColor(m.percentile) }}>
                      {pct(m.percentile)}<span className="text-[10px]">pct</span>
                    </span>
                  </span>
                </div>
                <div className="h-2 rounded-full bg-pitch-bg2 overflow-hidden">
                  <div className="h-full rounded-full transition-[width] duration-500 ease-out"
                       style={{ width: `${m.percentile ?? 0}%`, background: percentileColor(m.percentile) }} />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-pitch-line text-xs text-pitch-muted leading-relaxed space-y-1">
            <p><b className="text-pitch-sub">/90</b> — {T_PER90}</p>
            <p><b className="text-pitch-sub">xG / xA</b> — {T_XG}</p>
          </div>
        </div>
      </div>

      {profile.similar.length > 0 && (
        <div>
          <h2 className="font-semibold text-white mb-3 flex items-center gap-1.5">
            Similar players
            <span className="text-xs font-normal text-pitch-muted">· nearest {profile.cohort_label}</span>
            <InfoTip text="Players with the most similar statistical profile, measured by distance across the same per-90 metrics within this position and competition." />
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {profile.similar.map((sp) => <PlayerCard key={sp.player_id} p={sp} />)}
          </div>
        </div>
      )}

      <NewsSection query={`${p.name} ${p.club}`} />
    </div>
  );
}
