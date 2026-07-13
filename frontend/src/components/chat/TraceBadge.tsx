import { useState } from "react";
import type { QueryTrace } from "../../types";
import Icon from "../Icon";

// Shows, subtly, how the question was understood: the structured query the NLU produced.
// This is the visible proof that intent-extraction and the actual maths are separate —
// and which engine (LLM vs rule-based) resolved it.
export default function TraceBadge({ trace }: { trace: QueryTrace }) {
  const [open, setOpen] = useState(false);
  const filters = Object.entries(trace.filters || {}).filter(([, v]) => v != null && v !== "");

  return (
    <div className="mt-3 border-t border-pitch-line pt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs text-pitch-muted hover:text-pitch-sub flex items-center gap-1.5 transition-colors"
      >
        <span className={`chip ${trace.provider === "gemini"
          ? "bg-sky-500/15 text-sky-300" : "bg-pitch-line2/50 text-pitch-sub"}`}>
          <Icon name={trace.provider === "gemini" ? "sparkle" : "cpu"} size={11} />
          {trace.provider === "gemini" ? "LLM" : "rules"}
        </span>
        <span>understood as <b className="text-pitch-sub">{trace.intent}</b></span>
        <span className="underline">{open ? "hide" : "how?"}</span>
      </button>

      {open && (
        <div className="mt-2 text-xs bg-pitch-bg/60 rounded-lg p-3 space-y-1 font-mono">
          <Row k="intent" v={trace.intent} />
          <Row k="resolved by" v={trace.provider} />
          {trace.metric && <Row k="metric" v={trace.metric} />}
          {trace.entities.length > 0 && <Row k="players" v={trace.entities.join(", ")} />}
          {filters.map(([k, v]) => <Row key={k} k={k} v={String(v)} />)}
          {trace.notes && <Row k="notes" v={trace.notes} />}
          <div className="text-pitch-muted pt-1">↳ numbers computed deterministically from the data layer</div>
        </div>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-pitch-muted w-24 shrink-0">{k}</span>
      <span className="text-pitch-accent">{v}</span>
    </div>
  );
}
