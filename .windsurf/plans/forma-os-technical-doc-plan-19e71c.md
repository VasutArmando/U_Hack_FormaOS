# Forma OS Technical Master Doc — Plan

Generate a 2000-word technical deep-dive (`TECHNICAL_MASTER_DOC.md`) covering every backend function, API route, data flow from JSON → Gemini prompt → Flutter screen, plus Romanian Q&A answers for the jury.

## Plan Steps

1. **Write `TECHNICAL_MASTER_DOC.md`** at `e:\U_HACK_FINAL\TECHNICAL_MASTER_DOC.md` with:
   - **Section 1 – Architecture Overview**: FastAPI backend (`cloud_run/`), Flutter frontend (`flutter_app/`), data sources (`Data_Fixed/`), and the Gemini Multimodal bridge.
   - **Section 2 – Data Ingestion & Scraping**: Explain `services/scraper.py` (GSP.ro, Prosport.ro, Google News RSS), `news_cache.py` TTL system, and `data_manager.py` local JSON/SQLite parsing.
   - **Section 3 – Fatigue & Intelligence Logic**: Detail `fatigue_model.py` (`calculate`, `predict_fatigue`), `news_engine.py` (Stage-1 classification prompt, Stage-2 per-player prompt, `_call_gemini` with model fallback), and `climate_engine.py` climate-risk scoring.
   - **Section 4 – FastAPI Endpoints**: Document every route in `main.py` (`/api/v1/settings/teams`, `/api/v1/pregame/chronic-gaps`, `/api/v1/pregame/opponent-weakness`, `/api/v1/ingame/live-gaps`, `/api/v1/ingame/opponent-status`, `/api/v1/ingame/assistant`, `/api/v1/settings/prepare-match`, etc.) with request/response shape and caching strategy.
   - **Section 5 – Flutter Data Flow**: Trace `ApiDataRepository` → `DataRepository` abstraction → `match_data.dart` models (`Team`, `Stadium`, `TacticalGap`, `PlayerWeakness`, `LivePlayerFatigue`, `HalftimeChange`) → screen widgets (`pregame_screen.dart`, `ingame_screen.dart`, `assistant_tab.dart`). Include the `fatigue` calculation formula in `_InGameScreenState._calculatePlayerFatigue`.
   - **Section 6 – Gemini Prompt Engineering**: Show exact prompt templates (`CLASSIFICATION_PROMPT`, `INTEL_PROMPT`, `GAPS_PROMPT`) and how JSON from `Data_Fixed/` gets serialized into them.
   - **Section 7 – Q&A Jury Answers (Romanian)**: Provide concise, pitch-ready answers for all 9 questions, mapping each to the actual code implementation (e.g., scraping on-demand via `prepare_match`, mock vs live data transparency, fatigue metric math, Gemini choice rationale, business model, hallucination mitigation via strict JSON prompts, legal scaling path to official APIs, and emotional UI/UX argument).

2. **Target**: `e:\U_HACK_FINAL\TECHNICAL_MASTER_DOC.md`, ~2000 words, Markdown, code citations using `filename:line` format.

3. **Verify**: Ensure all 9 Q&A answers are present and every cited function/class is real (already validated via file reads).

---
*Plan approved by user → call `exitplanmode` then write the document.*
