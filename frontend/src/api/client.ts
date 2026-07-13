import type {
  ChatResponse, ClubInfo, CompetitionInfo, CompetitionProfile, ComparisonResult, Meta,
  NewsResponse, PlayerProfile, PlayerSummary, SearchResponse, TeamProfile,
} from "../types";

// In dev, Vite proxies /api -> backend. In prod/docker, set VITE_API_URL to the API origin.
const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface SearchFilters {
  position?: string;
  role?: string;
  competition?: string;
  country?: string;
  club?: string;
}

export const api = {
  meta: () => req<Meta>("/meta"),
  search: (q: string, filters: SearchFilters = {}, limit = 24) => {
    const params = new URLSearchParams({ q, limit: String(limit) });
    for (const [k, v] of Object.entries(filters)) if (v) params.set(k, v);
    return req<SearchResponse>(`/players/search?${params.toString()}`);
  },
  player: (id: string) => req<PlayerSummary>(`/players/${id}`),
  profile: (id: string) => req<PlayerProfile>(`/players/${id}/profile`),
  compare: (a: string, b: string) =>
    req<ComparisonResult>(`/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
  chat: (message: string) =>
    req<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ message }) }),
  team: (clubId: number) => req<TeamProfile>(`/teams/${clubId}`),
  teamSearch: (q: string) => req<ClubInfo[]>(`/teams/search?q=${encodeURIComponent(q)}`),
  competitions: () => req<CompetitionInfo[]>("/competitions"),
  competition: (name: string) => req<CompetitionProfile>(`/competitions/${encodeURIComponent(name)}`),
  news: (q: string, limit = 6) => req<NewsResponse>(`/news?q=${encodeURIComponent(q)}&limit=${limit}`),
};
