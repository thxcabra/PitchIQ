import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { NewsArticle } from "../types";
import Icon from "./Icon";

function ago(published: string | null): string {
  if (!published) return "";
  const d = new Date(published);
  if (isNaN(d.getTime())) return "";
  const mins = Math.floor((Date.now() - d.getTime()) / 60000);
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
  return `${Math.floor(mins / 1440)}d ago`;
}

// Latest news for a player / team / competition. Hides itself if nothing is returned.
export default function NewsSection({ query }: { query: string }) {
  const [articles, setArticles] = useState<NewsArticle[] | null>(null);

  useEffect(() => {
    let live = true;
    setArticles(null);
    api.news(query, 6).then((r) => live && setArticles(r.articles)).catch(() => live && setArticles([]));
    return () => { live = false; };
  }, [query]);

  if (articles !== null && articles.length === 0) return null;

  return (
    <div className="card p-4">
      <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
        <Icon name="globe" size={16} className="text-pitch-accent" /> Latest news
      </h2>
      {articles === null ? (
        <div className="space-y-2">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="skeleton h-9" />)}</div>
      ) : (
        <ul className="divide-y divide-pitch-line/60">
          {articles.map((a, i) => (
            <li key={i}>
              <a href={a.link} target="_blank" rel="noopener noreferrer"
                 className="group flex items-start gap-3 py-2.5 hover:bg-pitch-card2/50 -mx-2 px-2 rounded-lg transition-colors">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-pitch-accent/60 shrink-0" />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm text-pitch-text group-hover:text-white transition-colors leading-snug">
                    {a.title}
                  </span>
                  <span className="text-xs text-pitch-muted">
                    {a.source}{a.source && a.published ? " · " : ""}{ago(a.published)}
                  </span>
                </span>
                <Icon name="arrowRight" size={14} className="mt-1 text-pitch-muted opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
