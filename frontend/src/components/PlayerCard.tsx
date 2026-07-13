import { Link } from "react-router-dom";
import type { PlayerSummary } from "../types";
import { money } from "../lib/format";
import Icon from "./Icon";
import Avatar, { Logo } from "./Avatar";

const POS: Record<string, { chip: string; bar: string }> = {
  Forward: { chip: "bg-rose-500/15 text-rose-300", bar: "bg-rose-400" },
  Midfielder: { chip: "bg-emerald-500/15 text-emerald-300", bar: "bg-emerald-400" },
  Defender: { chip: "bg-sky-500/15 text-sky-300", bar: "bg-sky-400" },
  Goalkeeper: { chip: "bg-amber-500/15 text-amber-300", bar: "bg-amber-400" },
};

export default function PlayerCard({ p }: { p: PlayerSummary }) {
  const pos = POS[p.position] ?? { chip: "bg-pitch-line2/50 text-pitch-sub", bar: "bg-pitch-muted" };
  return (
    <Link
      to={`/player/${p.player_id}`}
      className="group relative card p-4 pl-5 flex flex-col gap-2 overflow-hidden
                 transition-all duration-200 hover:-translate-y-0.5 hover:border-pitch-accent/50
                 hover:shadow-lift active:translate-y-0 active:scale-[0.99]"
    >
      <span className={`absolute left-0 top-0 h-full w-1 ${pos.bar} opacity-60 group-hover:opacity-100 transition-opacity`} />
      <div className="flex items-start gap-3">
        <Avatar src={p.photo} name={p.name} size={44} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="font-semibold text-white truncate group-hover:text-pitch-accent transition-colors">
              {p.name}
            </div>
            <span className={`chip ${pos.chip} shrink-0`}>{p.role}</span>
          </div>
          <div className="flex items-center gap-1.5 text-sm text-pitch-sub truncate">
            <Logo src={p.club_logo} size={15} /> {p.club}
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-pitch-sub truncate">{p.competition}</span>
        <span className="text-pitch-muted num">{p.age ? `${p.age}y` : ""}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-pitch-accent font-semibold num">{money(p.market_value_eur)}</span>
        <Icon name="chevronRight" size={16}
              className="text-pitch-muted group-hover:text-pitch-accent group-hover:translate-x-0.5 transition-all" />
      </div>
    </Link>
  );
}
