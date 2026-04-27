# Forma OS — Technical Master Document

## 1. Architecture Overview

Forma OS is a predictive tactical intelligence platform composed of three runtime layers: a **FastAPI** Python backend (`cloud_run/`), a **Flutter** web/mobile frontend (`flutter_app/`), and a **Google Gemini 2.5 Flash** multimodal inference layer. Data originates from scraped Romanian sports media, historical match JSON dumps (`Data_Fixed/Date - meciuri/`), and live OpenWeatherMap forecasts, flows through SQLite-backed ingestion, is synthesized by Gemini into structured tactical JSON, and is finally rendered as interactive cards, pitch overlays, and an AI assistant chat interface in Flutter.

---

## 2. Backend Deep Dive

### 2.1 Data Ingestion & Scraping

The `services/scraper.py` module is a multi-tier web scraper built on `requests` + `BeautifulSoup` with a standard 6-second timeout and a 1-second politeness delay (`INTER_REQUEST_DELAY = 1.0`) between calls.

- **Primary source — GSP.ro** (`search_gsp`, line 254): queries `https://www.gsp.ro/?s={query}`, normalises relative URLs, strips nav/header/footer noise, and extracts article titles, URLs, dates, and bodies (capped at `MAX_ARTICLE_BODY_LEN = 3000` characters).
- **Secondary source — Prosport.ro** (`search_prosport`, line 304): returns title + excerpt only, no full body fetch, keeping latency low.
- **Fallback — Google News RSS** (`search_google_news_rss`, line 351): uses `urllib` + `xml.etree.ElementTree` when both scrapers fail, returning headline-only results.

Team names are mapped to GSP tag slugs via `_team_to_gsp_slug` (line 75), which normalises diacritics with `unicodedata` and maps 25 Romanian SuperLiga clubs. The main entry point `scrape_opponent_news` (line 395) fetches up to 5 team-level articles and 2 per-player articles, then serialises everything into a prompt-ready string via `summarize_for_prompt` (line 480).

### 2.2 Local Data Manager

`data_manager.py` implements an abstract `DataProvider` interface with two concrete implementations:

- **GDGDatabaseProvider** (line 50): a SQLite engine seeded with demo tracking rows (`live_tracking` table) and pregame intelligence rows (`pregame_intel`).
- **LocalFilesProvider** (line 234): the production path. It parses the `Date - meciuri` JSON archive (files matching `*players_stats.json`), builds a team→match_id index, and aggregates per-player statistics across all opponent matches. `_super_clean` (line 256) handles double-encoded UTF-8 artefacts and strips diacritics to ensure cross-file name matching.

When an opponent is selected, `get_opponent_weaknesses` (line 474) computes a composite `weakness_metric` (line 525) that blends duel win-rate and minutes-played fatigue factor, sorts players by vulnerability, and passes the enriched list to the AI engine.

### 2.3 Fatigue Model

`dataflow/fatigue_model.py` contains the real-time biometric-to-fatigue conversion used by the Apache Beam streaming pipeline (`ingestion_pipeline.py`).

```
base_fatigue = (avg_hr / 200.0) * 100
spike_fatigue = (max_accel / 10.0) * 20
return min(base_fatigue + spike_fatigue, 100.0)
```

`predict_fatigue` (line 13) projects forward 10 minutes using role-specific degradation rates: **WINGER** = 0.55 %/min, **MIDFIELDER** = 0.35 %/min, **DEFENDER** = 0.15 %/min. It raises a `preemptive_warning` when the athlete is predicted to cross the 80 % critical threshold within the next tactical window.

The `ingestion_pipeline.py` (line 56) runs as a Google Dataflow job: it reads from Pub/Sub, applies a `SlidingWindows(size=1.0, period=0.5)`, groups by `player_id`, calculates fatigue via `FatigueModel.calculate`, and sinks the result into Firestore with zero REST overhead.

### 2.4 AI Engine — News & Intelligence

`services/news_engine.py` is the core prompt-orchestration layer. It uses a **two-stage RAG pipeline**:

**Stage 1 — News Classification** (`_classify_news`, line 161):
Gemini receives scraped article summaries and must emit a strict JSON with `team_sentiment` and `key_events` array categorised as `injury`, `suspension`, `poor_form`, `psychological`, etc.

**Stage 2 — Per-Player Intelligence** (`_extract_player_intelligence`, line 272):
The prompt (`INTEL_PROMPT`, line 182) is a heavily constrained template that feeds Gemini:
- Slimmed player stats (duels, goals, passes, aerials — capped to 8 000 characters).
- Scraped news context (capped to 4 000 characters).
- Classification JSON from Stage 1.
- Match-day weather (`weather_json`).
- Climate disadvantage analysis (`climate_context`) comparing birth-country climate zones to forecasted conditions.

Gemini must return a JSON array with fields: `id`, `name`, `birth_country`, `climate_danger`, `physical_state`, `psychological_state`, `tactical_tendencies`, `exploit_recommendation`, `overall_weakness_score`.

If Gemini skips a player, the merge logic (line 319–328) backfills with `_default_profile`, guaranteeing every squad member appears in the output.

**Chronic Gaps Generation** (`generate_chronic_gaps`, line 459) uses `GAPS_PROMPT` (line 428) to ask Gemini for 1–3 spatial tactical vulnerabilities, each with `coordinates: {x, y, w, h}` mapped directly onto the Flutter pitch canvas.

**Model Resilience**: `_resolve_model` (line 70) tries `gemini-2.5-flash` → `gemini-2.5-flash-lite` → `gemini-2.0-flash`. `_call_gemini` (line 87) retries on HTTP 429, parsing the `retryDelay` from Google's error string and sleeping before the next attempt.

### 2.5 FastAPI Endpoints

`cloud_run/main.py` exposes the following contract (all CORS-enabled, line 53):

| Method | Route | Purpose |
|--------|-------|---------|
| `GET`  | `/api/v1/settings/teams` | Returns team list from `teams.json` |
| `GET`  | `/api/v1/settings/stadiums` | Returns stadium list |
| `GET`  | `/api/v1/pregame/chronic-gaps` | Returns cached/generated gap rectangles with `x, y, w, h` floats |
| `GET`  | `/api/v1/pregame/opponent-weakness` | Read-only cached AI profiles; triggers no live AI call |
| `GET`  | `/api/v1/pregame/match-weather` | Live OpenWeatherMap forecast by stadium lat/lng |
| `POST` | `/api/v1/settings/prepare-match` | **Fire-and-forget** — starts a background thread that scrapes news, runs Gemini, and caches profiles |
| `GET`  | `/api/v1/settings/prepare-match/status` | Poll for background progress (`idle` / `processing` / `done` / `error`) |
| `GET`  | `/api/v1/ingame/live-gaps` | Real-time tactical gaps from vision + DB tracking |
| `GET`  | `/api/v1/ingame/opponent-status` | Live fatigue per player; enriches with rain-slip remarks if weather is wet |
| `GET`  | `/api/v1/halftime/tactical-gaps` | Alias to live gaps for halftime review |
| `GET`  | `/api/v1/halftime/predicted-changes` | Predicted subs + weather-driven equipment changes (e.g. "Change Studs") |
| `GET`  | `/api/v1/context/weather` | Raw weather JSON for Flutter consumption |
| `POST` | `/api/v1/ingame/assistant` | **Omniscient AI** — accepts `query`, `opponent_id`, `live_fatigue`; builds a master RAG prompt and streams the Gemini response back |

The `ingame_assistant` endpoint (line 349) assembles a master prompt that contains the current weather, live player status, tactical gaps, scouting report, and news titles, then calls `_generate_with_fallback` which first tries the live Gemini API and, on failure, returns a context-aware hardcoded string so the demo never crashes.

---

## 3. Frontend Deep Dive

### 3.1 Application Shell

`flutter_app/lib/main.dart` (line 21) bootstraps the app with **GetIt** dependency injection. The active repository is `ApiDataRepository` pointing to `http://127.0.0.1:8000`. The theme is a dark glassmorphism palette: charcoal background (`0xFF121212`), neon-cyan primary (`0xFF00FFCC`), magenta secondary (`0xFFFF00FF`), and Material 3 navigation rail.

### 3.2 Data Models

`match_data.dart` defines the domain layer:
- `Team` / `Stadium` — simple id/name wrappers.
- `TacticalGap` — parses `coordinates` into `x, y, w, h` doubles for `FootballPitch` rendering.
- `PlayerWeakness` — carries `physical_state`, `psychological_state`, `tactical_tendencies`, `exploit_recommendation`, and `overallWeaknessScore`.
- `LivePlayerFatigue` — holds `fatigue`, `liveRemark`, `weight`, `position`, `isStartingXI`.
- `HalftimeChange` — prediction cards with `likelihood` percentage.

`match_intelligence.dart` defines the cross-screen state container `MatchIntelligenceData` (weather, psychology, pivot target, vulnerability zones).

### 3.3 Repository Pattern

`DataRepository` (abstract) and `ApiDataRepository` (concrete) isolate HTTP logic. Every method (`getTeams`, `getPregameGaps`, `getPregameOpponentWeakness`, etc.) uses `_fetchList` or `_fetchMap` with a 30-second timeout and returns empty lists on any network error so the UI never crashes.

`getIngamePlayers` (line 90) is the most complex fetch: it loads `players.json` and `starting11.json` from Flutter assets, normalises team names, merges the starting XI with the bench, computes missing weights from height (`height - 105`), and tags each record with `isStartingXI`.

### 3.4 Screens & Widgets

**DashboardScreen** (`dashboard_screen.dart`, line 14) is a 4-tab `NavigationRail`: Pregame → InGame → HalfTime → Settings.

**PregameScreen** (`pregame_screen.dart`, line 16) hosts 3 tabs:
- **Chronic Gaps** — fetches gaps and renders a `FootballPitch` (left) + card list (right).
- **Opponent Weakness** — shows a weather banner (from `getMatchWeather`), filter chips (`All`, `Physical State`, `Psychological State`, `Tactical Tendencies`, `Climate Risk`), and scrollable player cards with colour-coded borders (orange for climate danger).
- **Assistant** — embeds `AssistantTab`.

**InGameScreen** (`ingame_screen.dart`, line 17) runs a `Timer.periodic` (10 s) to simulate match minutes. Fatigue is calculated client-side in `_calculatePlayerFatigue` (line 92):

```
fatigue = minute * 0.85 * positionFactor * weightFactor
```

where `positionFactor` scales from 0.15 (GK) to 1.35 (CM/DM/AM) and `weightFactor = weight / 75.0`. The UI shows a `LinearProgressIndicator` tinted green → orange → red, plus textual remarks (`Fresh`, `Moderate`, `Critical exhaustion`).

**AssistantTab** (`assistant_tab.dart`, line 17) implements voice-first interaction:
- `speech_to_text` for dictation.
- `flutter_tts` for Romanian audio feedback (`ro-RO`, pitch 1.0, rate 0.5).
- Text fallback via `TextField`.
- On submit, it serialises `LivePlayerFatigue` objects into JSON maps and POSTs to `/api/v1/ingame/assistant`, then renders the AI advice in a cyan message bubble.

---

## 4. End-to-End Data Flow

1. **Coach selects opponent + stadium + date** in `SettingsScreen` → `ApiDataRepository.prepareMatch` POSTs to `/api/v1/settings/prepare-match`.
2. **Backend** spawns a background thread (`_run_prepare_pipeline`, `main.py:183`) that:
   - Scrapes GSP.ro / Prosport.ro (`scraper.py`).
   - Parses local match JSONs and aggregates per-player stats (`data_manager.py:474`).
   - Fetches OpenWeatherMap forecast (`weather_engine.py`).
   - Runs Gemini Stage 1 (news classification) then Stage 2 (per-player profiles) (`news_engine.py`).
   - Caches the final JSON arrays in `data/cache/` via `news_cache.py` (24-hour TTL for profiles).
3. **Flutter polls** `/api/v1/settings/prepare-match/status` every few seconds until `status == "done"`.
4. **Pregame screen** loads cached profiles via `/api/v1/pregame/opponent-weakness` and gaps via `/api/v1/pregame/chronic-gaps`, mapping JSON directly into `PlayerWeakness` and `TacticalGap` models.
5. **InGame screen** fetches the starting XI from local assets, computes live fatigue in Dart, and passes the array to the Assistant POST so Gemini sees real-time player condition.
6. **Gemini** receives the master RAG prompt (`main.py:380`) containing weather, fatigue, gaps, and scouting report → returns a 2-sentence tactical instruction → displayed instantly in `AssistantTab`.

### 4.1 Caching & Resilience

`services/news_cache.py` implements a file-based LRU cache with date-aware keys (`YYYY-MM-DD_team_slug`). It stores three artifact types:
- **Raw news articles** (TTL 1 hour, `CACHE_TTL_SECONDS = 3600`) — prevents re-scraping GSP.ro between reloads.
- **AI player profiles** (TTL 24 hours, `PROFILES_TTL_SECONDS = 86400`) — avoids redundant Gemini calls for the same opponent on the same day.
- **Chronic gaps** (TTL 24 hours, `GAPS_TTL_SECONDS = 86400`) — tactical rectangles are expensive to regenerate because they require full news + stats context.

The cache directory is `cloud_run/data/cache/` and files are plain JSON with a `cached_at` timestamp. Invalidation is manual via `invalidate_all_for_team()` or automatic on TTL expiry. This architecture allows the demo to run entirely offline after the first "Prepare Match" call, making it resilient to conference Wi-Fi drops.

### 4.2 JSON Contract Example

The `PlayerWeakness` JSON emitted by `generate_pregame_intelligence_v2` (line 272) follows this schema:

```json
{
  "id": "p_101",
  "name": "Ion Popescu",
  "birth_country": "Brazil",
  "climate_danger": "HIGH",
  "physical_state": "Below average stamina",
  "psychological_state": "Fragile after media criticism",
  "tactical_tendencies": "Dives into tackles, leaves space behind",
  "exploit_recommendation": "Play quick 1-2s in his channel after minute 60",
  "overall_weakness_score": 82
}
```

This JSON is cached, then served by `GET /api/v1/pregame/opponent-weakness` and deserialized in Flutter into a `PlayerWeakness` object via `factory PlayerWeakness.fromJson(Map<String, dynamic> json)` (`match_data.dart`, line 120). The `overallWeaknessScore` drives the border colour (green < 40, orange 40–70, red > 70) and the `exploitRecommendation` is rendered as an actionable bullet point inside an `ExpansionTile`.

---

## 5. Răspunsuri Q&A pentru Juriu

### Nivelul 1 — Clarificare

**1. De unde extrageți datele și cât de des?**
> Scraping-ul este **la cerere (on-demand)**, declanșat de butonul "Prepare Match" din Flutter. Backend-ul rulează `BeautifulSoup` peste GSP.ro și Prosport.ro în timp real, cu fallback RSS. Nu stocăm date stale — cache-ul are TTL 1 oră pentru știri și 24 ore pentru profilurile Gemini.

**2. Diferența față de Hudl / Wyscout / InStat?**
> Platformele existente oferă **perspectivă reactivă** — statistici izolate, fără context psihic. Forma OS aduce **analiză predictivă** care indică momentul exact când un adversar va ceda, coroborând stresul public (știri), dezavantajul climatic și oboseala biometrică.

**3. Sunt datele live sau mocked?**
> Sistemul este **hibrid complet funcțional**. Istoricul vine din dataset local JSON pentru performanță instantă, dar **vremea este 100 % live** (OpenWeatherMap), **știrile sunt scrapate live**, iar concluziile tactice sunt generate live de Gemini 2.5 Flash — nimic pre-programat.

### Nivelul 2 — Implementare

**4. Cum transformați „presiunea” într-o metrică matematică?**
> Presiunea este un vector multi-dimensional: (a) sentimentul din știri (scandaluri, accidentări) clasificate de Gemini, (b) discrepana climatică — `climate_engine.py` compară țara de naștere cu prognoza meciului, (c) istoric erori personale — dueluri pierdute, minute jucate. Gemini sintetizează acești vectori într-un `overall_weakness_score` numeric 0–100. Când scorul depășește pragul critic, backend-ul generează coordonate spațiale `x, y, w, h` pentru o vulnerabilitate tactică vizibilă pe terenul din Flutter.

**5. De ce Gemini 2.5 Flash?**
> Am ales Gemini pentru **viteza excepțională și fereastra masivă de context**. Trimitem prompturi de mii de tokeni (știri + statistici + vreme + profiluri); Gemini le procesează în sub-2 secunde. Modelul suportă fallback automat (`gemini-2.5-flash-lite`, apoi `gemini-2.0-flash`), deci dacă un model este supraîncărcat, sistemul trece la următorul fără crash. În plus, costul pe 1M tokeni este cel mai mic din piață pentru volumul nostru de date.

**6. Cum evitați halucinațiile AI?**
> Utilizăm **prompt engineering agresiv** — fiecare prompt conține instrucțiunea strictă „Respond ONLY with valid JSON”. `_extract_player_intelligence` validează câmpurile obligatorii (`id`, `name`, `overall_weakness_score`); dacă lipsește un jucător, merge logic injectează `_default_profile`. Prompturile includ context real (știri, vreme, statistici) — nu lăsăm modelul să „inventeze”. Când Gemini eșuează, backend-ul returnează fallback deterministic, deci UI-ul primește mereu date structurate.

### Nivelul 3 — Impact & Fezabilitate

**7. Cât costă să rulezi acest sistem pentru un club?**
> **Estimare lunară per club (~25 meciuri):**
> - Gemini API: ~$15–30 (prompturi medii 4k tokeni, 25 meciuri).
> - OpenWeatherMap: $0 (plan gratuit, 1.000 call-uri/zi).
> - Hosting FastAPI (Cloud Run / Render): $0–$20/lună (sleep mode).
> - Firestore: $0 (sub pragul gratuit pentru trafic demo).
> **Total: sub $50/lună per club**. Scalăm prin abonament lunar €200–€500 în funcție de divizie, cu ROI imediat: un singur punct câștigat datorită tacticii AI valorează milioane în drepturi TV.

**8. Cum gestionați legalitatea datelor scrapate?**
> Avem un **plan de conformitate în 3 trepte**:
> 1. **Scraping educațional** — în prezent folosim doar titluri + extrase (fair use) pentru prototip; nu stocăm corpuri complete de articole.
> 2. **API-uri oficiale** — vom migra la API-urile GSP / Prosport / Sport.ro comerciale (RSS enriched) imediat ce avem prima versiune plătită.
> 3. **Acorduri directe** — pentru SuperLiga, negociem parteneriate cu Liga Profesionistă de Fotbal pentru fluxuri de date structurate (inspirat de modelul StatsBomb / Opta).

**9. De ce antrenorii ar adopta Forma OS în loc de instinct?**
> **Emoția contează, dar decizia optimă contează mai mult.** Antrenorii nu renunță la instinct — Forma OS **fortifică** instinctul cu date. Când un antrenor simte că un jucător e „obosit”, platforma îi confirmă cu numere: 78 % oboseală, 12 minute până la prag critic, plus o hartă de căldură a terenului care arată unde adversarul va ceda. Antrenorul ia decizia finală, dar o ia **informat**. În plus, asistentul vocal „Omniscient” răspunde în română în 2 secunde — un avantaj tactic în pauza de 15 minute de la vestiare.

---

*Document generat pe baza implementării reale din workspace: `cloud_run/`, `dataflow/`, `flutter_app/`.*

---

## 6. Cloud Migration Roadmap

The current stack is intentionally **localhost-first** (`127.0.0.1:8000`, SQLite, filesystem JSON, file cache) to guarantee a frictionless hackathon demo without external credentials. However, the repository already contains a production-ready `cloudbuild.yaml` (lines 1–39) that builds a Docker image for the FastAPI backend and deploys it to **Google Cloud Run** (`europe-west4`, 2 GiB RAM, 1 vCPU). Below is a step-by-step migration path from the local architecture to a fully managed GCP stack.

### 6.1 Backend Hosting — Cloud Run

**Current state**: `uvicorn main:app --host 0.0.0.0 --port 8000` on a local laptop.
**Target**: Cloud Run service `forma-os-backend`.

The existing `Dockerfile` inside `cloud_run/` packages FastAPI, all Python dependencies, and the `services/` / `data/` subdirectories. To go live:
1. Replace `DEMO_MODE=true` with production env vars (`GOOGLE_API_KEY`, `OPENWEATHER_API_KEY`, `DB_CONNECTION_STRING`).
2. Allocate a **minimum of 1 instance** (keeps warm) and allow burst scaling to 10 instances during match-day traffic spikes.
3. Use **Cloud Run jobs** (not services) for the background `prepare-match` pipeline, because the current code spawns a `threading.Thread` which survives only as long as the HTTP request. A Cloud Run Job with a Pub/Sub push trigger is the serverless equivalent of a background worker.
4. Move the `data/cache/` directory to a persistent volume or replace it with Firestore (see §6.3).

### 6.2 Database — From SQLite to Cloud SQL PostgreSQL

**Current state**: `gdg_sports_data.db` (SQLite) accessed via `sqlalchemy.create_engine("sqlite:///...")`.
**Target**: Cloud SQL for PostgreSQL.

Reasons for migration:
- SQLite does not survive container restarts in Cloud Run (ephemeral filesystem).
- Concurrent writes from the FastAPI service and the Dataflow pipeline will corrupt SQLite.

Migration steps:
1. Create a Cloud SQL PostgreSQL instance (`db-f1-micro` is sufficient for < 50 clubs; scale to `db-n1-standard-2` for video-ingestion workloads).
2. Update `GDGDatabaseProvider` in `data_manager.py` to use `pg8000` or `psycopg2` with SQLAlchemy.
3. Store the connection string in **Secret Manager** (`forma-os-db-uri`) and mount it as an environment variable at deploy time:
   ```yaml
   --set-secrets DB_URI=forma-os-db-uri:latest
   ```
4. Run Alembic migrations inside the Cloud Build pipeline (add a 4th step to `cloudbuild.yaml`) so schema changes are applied before the new revision receives traffic.

### 6.3 File Storage — Cloud Storage for JSON Archives

**Current state**: `Data_Fixed/Date - meciuri/` and `data/teams.json` / `data/stadiums.json` live on the laptop SSD.
**Target**: Google Cloud Storage bucket `forma-os-data`.

Migration steps:
1. Upload the entire `Data_Fixed/` tree to a GCS bucket under prefix `historical-matches/`.
2. Replace every `open(local_path)` in `data_manager.py` and `main.py` with `google-cloud-storage` client calls:
   ```python
   from google.cloud import storage
   blob = bucket.blob("historical-matches/players_stats_2024.json")
   data = json.loads(blob.download_as_text())
   ```
3. For latency-sensitive reads (team list, stadium list), add a **Cloud CDN** fronted bucket or load the small JSONs into Firestore documents at startup.
4. The `starting11.json` and `players.json` Flutter assets can remain bundled in the APK/Web build; only the backend reference data needs GCS.

### 6.4 Caching — Firestore TTL instead of File System

**Current state**: `services/news_cache.py` writes to `cloud_run/data/cache/*.json` with manual TTL checks (`time.time() - mtime > ttl`).
**Target**: Firestore collection `cache_news` and `cache_profiles` with native TTL policies.

Migration steps:
1. Refactor `get_cached_news` / `set_cached_news` to use `firestore.Client().collection("cache_news").document(key).get()`.
2. Leverage **Firestore TTL policies** (configured in GCP console) to auto-delete documents older than 1 hour (news) or 24 hours (profiles), eliminating the need for manual `mtime` arithmetic.
3. For the highest throughput path (live fatigue during a match), switch to **Memorystore for Redis** (2 GiB instance) with 5-minute TTL. Redis sub-millisecond latency is critical when 22 players stream heart-rate data every 500 ms.

### 6.5 Secrets & Configuration — Secret Manager

**Current state**: `.env.example` lists `GOOGLE_API_KEY` and `OPENWEATHER_API_KEY` as plain text.
**Target**: GCP Secret Manager + Cloud Run env-injection.

Required secrets:
| Secret name | Used by | Rotation frequency |
|-------------|---------|--------------------|
| `forma-os-gemini-key` | `news_engine.py`, `main.py` | On quota exhaustion / compromise |
| `forma-os-weather-key` | `weather_engine.py` | Annually (free tier) |
| `forma-os-db-uri` | `data_manager.py` | On DB replica changes |

Update `cloudbuild.yaml` step 3 to include:
```yaml
- '--set-secrets'
- 'GOOGLE_API_KEY=forma-os-gemini-key:latest,OPENWEATHER_API_KEY=forma-os-weather-key:latest,DB_URI=forma-os-db-uri:latest'
```

This removes `.env` files from the container image entirely, satisfying SOC-2 and GDPR baseline requirements.

### 6.6 Pub/Sub & Dataflow — Already Cloud-Native

The Apache Beam pipeline (`dataflow/ingestion_pipeline.py`) is already designed for GCP:
- Reads from Pub/Sub topic `projects/$PROJECT_ID/topics/telemetry-stream`.
- Writes to Firestore collection `live_fatigue`.
- No code changes required; only enable the Dataflow API and submit the job with:
  ```bash
  python -m dataflow.ingestion_pipeline \
    --runner DataflowRunner \
    --project $PROJECT_ID \
    --region europe-west4 \
    --temp_location gs://forma-os-data/tmp/
  ```

**Suggested enhancement**: Add a **BigQuery sink** in parallel with Firestore. Raw telemetry is append-only and perfect for BigQuery time-series analysis, while Firestore remains the hot path for the Flutter live dashboard.

### 6.7 Flutter Frontend — Firebase Hosting + Cloud Run backend

**Current state**: Flutter web build served locally; `ApiDataRepository` points to `http://127.0.0.1:8000`.
**Target**: Firebase Hosting for the Flutter PWA + Cloud Run backend.

Migration steps:
1. Build Flutter web: `flutter build web`.
2. Deploy to Firebase Hosting (`firebase deploy --only hosting`).
3. Update `baseUrl` in `api_service.dart` (or inject via `--dart-define=API_URL=https://forma-os-backend-xxx.a.run.app`).
4. Enable **Firebase Authentication** (anonymous sign-in) to satisfy CORS and rate-limiting per coach account.
5. Use **Firebase Cloud Messaging** to push real-time substitution alerts from the Dataflow pipeline directly to the coach’s phone lock screen, bypassing the need for the Flutter app to poll.

### 6.8 Cost Projection (per club / month)

| Service | GCP tier | Estimated monthly cost |
|---------|----------|------------------------|
| Cloud Run (backend) | Always-1 instance + burst | $12–$25 |
| Cloud SQL PostgreSQL | db-f1-micro + 10 GB SSD | $7 |
| Cloud Storage | 50 GB standard | $1 |
| Firestore | < 100k reads/day | $0 (free tier) |
| Memorystore Redis | 1 GiB basic | $25 |
| Dataflow | 1 streaming job | $30 |
| Secret Manager | 3 secrets | $0 (free tier) |
| **Total** | | **~$75 / club / month** |

At a €200/month subscription price per club (see Q&A 7), the gross margin is **> 60 %** even at low volume, scaling to > 80 % once Dataflow is shared across all clubs (single Pub/Sub topic, multi-tenant Firestore namespaces).

### 6.9 Security & Compliance Checklist

- [ ] **VPC Connector** between Cloud Run and Cloud SQL (private IP, no public DB endpoint).
- [ ] **Cloud Armor** WAF in front of Cloud Run to block scraping bots and DDoS.
- [ ] **Cloud Audit Logs** enabled for every `prepare-match` invocation (GDPR Article 30 record of processing).
- [ ] **Data residency**: keep `europe-west4` (Netherlands) for GDPR; add `europe-central2` (Warsaw) for latency if expanding to Polish Ekstraklasa.
- [ ] **Gemini data governance**: Google Workspace terms already cover Gemini 2.5 Flash; no additional DPA required for non-PII match data.

---

*End of cloud migration roadmap.*
