import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { ComparisonResult, PlayerSummary } from "../types";
import PlayerPicker from "../components/PlayerPicker";
import ComparisonView from "../components/ComparisonView";
import Icon from "../components/Icon";

export default function ComparePage() {
  const [params] = useSearchParams();
  const [a, setA] = useState<PlayerSummary | null>(null);
  const [b, setB] = useState<PlayerSummary | null>(null);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // preselect player A from ?a= (e.g. arriving from a profile)
  useEffect(() => {
    const id = params.get("a");
    if (id) api.player(id).then(setA).catch(() => {});
  }, [params]);

  useEffect(() => {
    if (!a || !b) { setResult(null); return; }
    setError(null);
    api.compare(a.player_id, b.player_id).then(setResult).catch((e) => setError(e.message));
  }, [a, b]);

  return (
    <div className="space-y-6 animate-fade-up">
      <h1 className="text-2xl font-bold text-white tracking-tight">Head-to-head comparison</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <PlayerPicker label="Player A" selected={a} onSelect={setA} />
        <PlayerPicker label="Player B" selected={b} onSelect={setB} />
      </div>

      {error && <p className="text-rose-300">{error}</p>}
      {!a || !b ? (
        <div className="text-center py-16 text-pitch-muted">
          <Icon name="scale" size={32} className="mx-auto mb-2 opacity-40" />
          <p>Pick two players to compare them visually.</p>
        </div>
      ) : result ? (
        <ComparisonView data={result} />
      ) : (
        <div className="skeleton h-96" />
      )}
    </div>
  );
}
