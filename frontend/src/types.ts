// Mirrors the backend Pydantic models (app/models/responses.py).

export interface PlayerSummary {
  player_id: string;
  name: string;
  photo: string | null;
  position: string;
  role: string;
  age: number | null;
  nation: string | null;
  height_cm: number | null;
  foot: string | null;
  club: string;
  club_id: number | null;
  club_logo: string | null;
  competition: string;
  country: string;
  market_value_eur: number | null;
}

export interface MetricContext {
  metric: string;
  label: string;
  value: number | null;
  cohort_average: number | null;
  percentile: number | null;
}

export interface SeasonTotal {
  key: string;
  label: string;
  value: number | null;
}

export interface CompetitionLine {
  competition: string;
  competition_type: string;
  club: string;
  matches: number | null;
  minutes: number | null;
  goals: number | null;
  assists: number | null;
}

export interface MetricHighlight {
  label: string;
  percentile: number;
}

export interface PlayerProfile {
  player: PlayerSummary;
  cohort_label: string;
  cohort_size: number;
  rating: number | null;
  strengths: MetricHighlight[];
  weaknesses: MetricHighlight[];
  totals: SeasonTotal[];
  metrics: MetricContext[];
  breakdown: CompetitionLine[];
  similar: PlayerSummary[];
}

// --- team & competition profiles ---
export interface ClubInfo {
  club_id: number;
  name: string;
  logo: string | null;
  competition: string | null;
  country: string | null;
  squad_value: number | null;
  squad_size: number | null;
  avg_age: number | null;
  stadium: string | null;
  stadium_seats: number | null;
  coach: string | null;
}

export interface SquadMember {
  player: PlayerSummary;
  goals: number;
  assists: number;
  minutes: number;
  matches: number;
}

export interface TeamProfile {
  club: ClubInfo;
  squad_count: number;
  total_goals: number;
  competitions: string[];
  top_scorer: SquadMember | null;
  squad: SquadMember[];
}

export interface CompetitionInfo {
  competition_id: string;
  competition: string;
  type: string;
  country: string;
  confederation: string | null;
  flag: string | null;
}

export interface CompetitionClub {
  club_id: number;
  name: string;
  logo: string | null;
  goals: number;
}

export interface CompetitionProfile {
  competition: CompetitionInfo;
  player_count: number;
  club_count: number;
  total_goals: number;
  top_scorers: PlayerSummary[];
  top_value: PlayerSummary[];
  clubs: CompetitionClub[];
}

export interface ComparisonMetric {
  metric: string;
  label: string;
  a_value: number | null;
  b_value: number | null;
  a_percentile: number | null;
  b_percentile: number | null;
  winner: "a" | "b" | null;
}

export interface MarketSide {
  market_value_eur: number | null;
  value_percentile: number | null;
}

export interface ComparisonResult {
  player_a: PlayerSummary;
  player_b: PlayerSummary;
  metrics: ComparisonMetric[];
  wins: Record<string, number>;
  overall_winner: "a" | "b" | "tie";
  market_context: { a: MarketSide; b: MarketSide };
}

export interface SearchResponse {
  query: string;
  count: number;
  total: number;
  results: PlayerSummary[];
}

export interface CompetitionIndexEntry {
  competition: string;
  country: string;
  competition_type: string;
}

export interface NewsArticle {
  title: string;
  link: string;
  source: string | null;
  published: string | null;
}

export interface NewsResponse {
  query: string;
  articles: NewsArticle[];
}

export interface Meta {
  player_count: number;
  row_count: number;
  season: string;
  competitions: string[];
  competition_index: CompetitionIndexEntry[];
  countries: string[];
  positions: string[];
  roles: string[];
  role_groups: { position: string; roles: string[] }[];
  metrics: { key: string; label: string; unit: string }[];
  nlu_provider: string;
}

// --- chat discriminated union -------------------------------------------------
export interface QueryTrace {
  intent: string;
  provider: string;
  metric: string | null;
  entities: string[];
  filters: Record<string, unknown>;
  notes: string | null;
}

export interface TextResponse {
  type: "text";
  title: string | null;
  text: string;
  trace: QueryTrace;
}

export interface Column {
  key: string;
  label: string;
  kind: "text" | "number" | "money";
}

export interface TableResponse {
  type: "table";
  title: string;
  columns: Column[];
  rows: Record<string, unknown>[];
  narrative: string | null;
  trace: QueryTrace;
}

export interface ChartSeries {
  name: string;
  values: (number | null)[];
}

export interface ChartResponse {
  type: "chart";
  chart_type: "radar" | "bar";
  title: string;
  categories: string[];
  series: ChartSeries[];
  value_kind: "percentile" | "raw";
  narrative: string | null;
  footnote: string | null;
  trace: QueryTrace;
}

export interface ComparisonResponse {
  type: "comparison";
  title: string;
  data: ComparisonResult;
  narrative: string | null;
  trace: QueryTrace;
}

export interface ClarificationOption {
  label: string;
  query: string;
}

export interface ClarificationResponse {
  type: "clarification";
  message: string;
  options: ClarificationOption[];
  trace: QueryTrace;
}

export interface ErrorResponse {
  type: "error";
  message: string;
  suggestions: string[];
  trace: QueryTrace;
}

export type ChatResponse =
  | TextResponse
  | TableResponse
  | ChartResponse
  | ComparisonResponse
  | ClarificationResponse
  | ErrorResponse;
