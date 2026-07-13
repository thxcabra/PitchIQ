# PitchIQ — Project Knowledge Base

> Working notes and source-of-truth for the project. **This is not the README** — it's the
> raw material a README (or docs) is generated from. Keep it factual and current.

---

## 1. What it is

PitchIQ turns raw football data into a decision tool that is reachable both through fixed
screens **and** through natural language. Built for the SoccerSolver "Conversational
Analytics" full-stack challenge, then extended into a fuller app.

One-liner: *Conversational analytics over current European football — search, profile,
compare, and just ask.*

Stack: **React + TypeScript (Vite)** frontend · **Python + FastAPI** backend · **Recharts**
· **Gemini** (swappable) with a deterministic rule-based NLU fallback · Docker Compose.

---

## 2. Challenge requirements (what the brief asked for)

The original brief and how PitchIQ meets it:

- **View 1 — Player search:** name search + result cards (position, club, competition,
  market value) → link to profile. *Extended with photos + filters (position/role,
  country→competition, club) and a live match count.*
- **View 2 — Individual profile:** basic data + **contextualised** metrics (percentile vs
  the average for the position in the same competition), not raw numbers. *Extended: photo,
  overall rating, strengths/weaknesses, per-competition breakdown, season totals, similar
  players, and metric explanations.*
- **View 3 — Two-player comparison:** a **real visual** head-to-head (overlaid radar +
  per-metric diverging bars), not two tables; market-value context. Same logic as the chat.
- **View 4 — "Ask PitchIQ" (the core):** chat that resolves free text to a structured query
  and returns a chart / table / comparison / narrative. Handles ranking/filtering,
  lookup/explanation, comparison; fails gracefully on ambiguous/unknown/out-of-scope.
- **Backend:** clean routes, Pydantic response models, meaningful error codes, type hints
  throughout; percentile/comparison logic in a **service layer** (not endpoints); CSV access
  abstracted behind a repository; a distinct **NLU module** separate from query execution
  separate from the endpoint (three layers); a `POST /chat` returning a structured
  (discriminated-union) response; LLM keys via env var only; tests on core math + NLU.
- **Frontend:** chat component with message list, input, loading and error states; renders
  ≥2 response types dynamically from one component (table + chart + comparison + …).
- **Judgment:** the LLM is used for intent/entity extraction (and could do narrative), but
  **never** for the numbers — all percentile/ranking/comparison math is deterministic.

Extra features beyond the brief: **team profiles**, **competition profiles**, **player
photos + club crests + competition flags**, **news** (players/teams/competitions),
**bilingual chat (EN + PT-BR)**, and a **role-level position filter**.

---

## 3. Data

**Season: 2025-26** (current). Squads are up to date (e.g. Haaland at Man City, De Bruyne at
Napoli, Mbappé at Real Madrid).

**Primary source — Transfermarkt player-scores dataset** (github.com/dcaribou/transfermarkt-datasets,
CC0, no scraping). Per-appearance data is aggregated into **one row per (player, competition)**.
Also yields clubs (crest, stadium, coach, squad value/size, avg age) and competitions metadata.

**Hybrid enrichment — Understat** (via `soccerdata`, plain HTTP). Big-5 **league** rows are
enriched with **xG, xA, shots, key passes** (matched by name, with a token-subset fallback
for name variations like "Mbappe-Lottin"). Rows outside the Big-5 leagues keep the base
metrics; the radar falls back automatically.

**Images:** player photos from Transfermarkt `image_url`; club crests from the TM crest URL
pattern (`.../wappen/head/{club_id}.png`); competition flags from flagcdn by country (cups
fall back to a trophy icon — TM competition logos don't resolve).

**Market value:** the historical valuation nearest the season midpoint, falling back to the
player's current then peak TM value.

**Coverage & trade-offs:**
- ~12,300 rows · ~6,900 players · **44 competitions** · **14 top-division leagues** + domestic
  cups + UEFA Champions/Europa/Conference League (+ qualifiers, super cups) + World Cup + AFCON.
- Market value ~81% (the missing ~19% are lower-profile players TM simply doesn't value → "n/d").
- **Europe-centric:** Americas/Asia/Oceania and African-domestic leagues are **not** available
  from the free non-scraping sources. FBref (which has them, with rich stats) blocks scraping
  via Cloudflare — confirmed 403 even with a headless browser.
- **Event data (xG/shots/key passes) is Big-5 leagues only** (Understat coverage). Cups,
  continental and smaller leagues use goals/assists/minutes/cards, so their radars are thinner.

**Build:** `backend/scripts/build_dataset.py` (build-time only; needs `pandas` + `soccerdata`).
It downloads/joins the sources and writes `backend/app/data/players.csv`, `clubs.csv`,
`competitions.csv`. The **runtime never touches the network or these libs** — it reads the CSVs
with the stdlib. Committed CSVs mean the app runs without rebuilding.

Selected season = start year (2025 = 2025-26). Why not 2022-23? An earlier attempt used a
FBref mirror whose 2022-23 slice was only a mid-season snapshot; the current TM source is
complete and current.

---

## 4. Architecture

### Backend (`backend/app/`) — three layers for the conversational flow

```
POST /chat
  1. NLU (nlu/)            free text -> StructuredQuery
       interpreter.py      orchestrates: LLM (validated/grounded) OR rule-based fallback
       llm_provider.py     Gemini via REST responseSchema (swappable)
       rule_based.py       deterministic parser (EN + PT), zero-cost fallback
       extractors.py       closed vocabularies (competitions, countries, roles, ages...)
       query_models.py     StructuredQuery / QueryFilters
  2. execution (chat/executor.py)   StructuredQuery -> ChatResponse, calling the SAME services
  3. endpoint (routes/chat.py)      thin, Pydantic-typed
```

- **Services** (`services/`) own all football logic and are reused by REST views AND the chat:
  `search`, `stats` (percentiles / cohort averages / profile / similar players), `ranking`
  (filter + sort), `comparison`, `team`, `competition`, `news`.
- **Repository** (`data/repository.py`) abstracts CSV access; loads players + clubs +
  competitions once; exposes rows (per-competition) and person-grouped views.
- **Metrics catalog** (`metrics.py`) is the closed set of metrics a query can name; the NLU
  validates the LLM's chosen metric against it. `resolve_metric` maps free text (EN + PT).
- **Shared text helpers** (`text.py`): `deaccent`, `normalize`.
- Discriminated-union `ChatResponse` (`models/responses.py`): `text | table | chart |
  comparison | clarification | error`, each carrying a `QueryTrace` (how it was understood).

### Frontend (`frontend/src/`)

- Pages: `SearchPage`, `ProfilePage`, `TeamPage`, `CompetitionPage`, `ComparePage`, `ChatPage`.
- Shared components: `Icon` (Phosphor), `Avatar`/`Logo`, `Stat`, `PlayerCard`, `PlayerPicker`,
  `RadarChart`, `ComparisonView`, `InfoTip`, `NewsSection`, `chat/TraceBadge`,
  `renderers/ResponseRenderer` (switches on the discriminated union).
- `lib/`: `format` (money/num/pct/percentileColor), `colors` (shared chart palette).
- `api/client.ts`: single typed client; `types.ts` mirrors the backend models.

### API surface

`GET /players/search` · `GET /players/{id}` · `GET /players/{id}/profile` ·
`GET /compare` · `POST /chat` · `GET /meta` · `GET /health` ·
`GET /teams/search` · `GET /teams/{club_id}` · `GET /competitions` ·
`GET /competitions/{name}` · `GET /news?q=`.

---

## 5. The conversational layer (deep dive)

**Approach: LLM for intent/entities only; never for the maths.** `POST /chat` sends the
question to Gemini with a constrained `responseSchema` (structured output — the
"function-calling for extraction" pattern) and gets back a `StructuredQuery`
(intent, metric, entities, filters). The executor then calls deterministic services.

Three design choices:
1. **Grounding & validation** — everything the LLM returns is normalised against closed
   vocabularies (`nlu/extractors.py`): "EPL" → Premier League, "strikers" → the Centre-Forward
   role, an aliased metric → its canonical key. An invalid intent or unresolvable metric is
   rejected → rule-based fallback. The LLM can't inject an unknown metric/competition.
2. **Deterministic entity resolution** — the LLM extracts only the raw name text; the
   `search_service` resolves it to a real player (typo-tolerant: "halaand" → Haaland;
   same-name tie-break by market value/minutes so "Mbappe" → Kylian). Unknown names resolve
   to nothing → graceful error.
3. **Explain trace** — every response carries the `StructuredQuery` that produced it, shown
   subtly in the UI (which engine resolved it: LLM vs rules).

**Bilingual (EN + PT-BR):** the rule-based interpreter has English *and* Portuguese
vocabulary/triggers, accent-insensitive (e.g. "artilheiros da Champions League",
"melhores atacantes da Série A por gols"). With a key, Gemini understands any language.

**Queries handled:** ranking/filtering across any competition; lookup (player vs cohort
average, radar of percentiles); comparison (identical to View 3). Ambiguous ("best player")
→ clarification chips; unknown player → error + suggestions; out-of-scope / out-of-coverage
region ("top scorers in Brazil") → scoped explanation.

**Correctness guarantee:** the LLM output schema has no numeric result fields. Percentiles /
rankings / comparisons are computed in the services from the data; the chat calls those exact
functions, so a chat number is byte-for-byte the number in Views 1-3. Covered by tests and
auditable via the on-screen trace.

**Swappable & free:** provider + key via env only (`LLM_PROVIDER`, `GEMINI_API_KEY`). Default
is Gemini free tier (~$0 for the demo). With no key, the rule-based NLU handles everything.

---

## 6. Tech decisions (and why)

- **One row per (player, competition)** — the model that makes per-competition queries and
  the profile breakdown possible.
- **Committed CSVs + stdlib runtime** — no DB, no runtime network dependency; `pandas`/`soccerdata`
  are build-time only; the app boots instantly and runs offline.
- **Rule-based NLU as a first-class fallback** — the demo works with zero cost / no key, and
  the LLM path degrades to it on any failure.
- **Discriminated-union chat responses** — the frontend renders each shape dynamically from
  one component; adding a response type is one case.
- **Google News RSS** for news — free, no key, graceful (hides the section on failure).
- **Phosphor icons + Geist/Geist Mono + single emerald accent** — a technical-dashboard look;
  no emojis, no AI-purple, tabular mono figures for data.

---

## 7. Testing

`backend/tests/` (pytest): `test_stats_service.py` (percentiles / cohort scoping / ranking /
filtering / lower-is-better inversion) and `test_nlu.py` (rule-based extraction for the
canonical queries + LLM-output grounding + fallbacks). 17 tests. Run: `cd backend && pytest`.

---

## 8. Running

**Docker:** `cp .env.example .env` (optional `GEMINI_API_KEY`) then `docker-compose up` →
frontend http://localhost:5173, backend http://localhost:8000/docs. nginx serves the built
frontend and proxies `/api` → backend.

**Local:** backend `pip install -r requirements.txt && uvicorn app.main:app --reload`;
frontend `npm install && npm run dev` (proxies `/api` → :8000).

**Rebuild data (optional):** `pip install -r backend/scripts/requirements-build.txt` then
`python backend/scripts/build_dataset.py`.

Env vars (`.env.example`): `LLM_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `CORS_ORIGINS`,
`CSV_PATH`, `VITE_API_URL`.

---

## 9. Metric glossary (for the docs)

- **/90** — per 90 minutes played; normalises for game time (0.8 goals/90 ≈ a goal every 112 min).
- **Percentile** — rank vs others in the same position + competition (100 = best, 50 = average).
- **xG / xA** — expected goals / assists: the quality of chances taken / created (Understat,
  Big-5 leagues only). All figures come from match data, never estimated by the LLM.
- **Rating** — average percentile across the player's radar metrics.
- **Similar players** — nearest statistical profile (z-normalised distance) within the cohort.

---

## 10. Known limitations & what I'd improve

- Coverage is Europe-centric; no Americas/Asia/Oceania/African-domestic (free-source ceiling).
- Event data (xG/shots) is Big-5 leagues only; thinner radars elsewhere.
- ~19% of players lack a market value (shown "n/d").
- Club attribution: squads use each player's primary (most-minutes) club; a mid-season mover
  appears at whichever club they played most.
- Single-turn chat (no conversational memory); LLM narrative is currently templated/deterministic.
- Future: broader data via a paid/allowed source; conversational memory; embeddings-based
  entity resolution + similar-players; a DB behind the repository; extract shared `useResource`
  hook and a `DataTable` primitive on the frontend; caching the LLM layer.
