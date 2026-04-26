"""
news_engine.py — Opponent Intelligence Engine
Integrates web scraping (GSP.ro / Prosport.ro) with Gemini AI for
structured pre-match opponent analysis.
"""

import json
import logging
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

import google.genai as genai
from google.genai import types as genai_types

from services.scraper import summarize_for_prompt
from services.news_cache import get_or_fetch

logger = logging.getLogger("forma_os_news")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
_genai_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None


# ---------------------------------------------------------------------------
# Legacy RSS helper (kept for direct usage in main.py assistant)
# ---------------------------------------------------------------------------

def fetch_news(query_term: str, is_player: bool = False, max_results: int = 5) -> List[str]:
    """Extrage titluri recente din Google News RSS despre un termen (legacy)."""
    if is_player:
        query_str = f'"{query_term}" fotbal (accidentare OR transfer OR criticat)'
    else:
        query_str = f'"{query_term}" fotbal (antrenor OR meci OR transfer)'

    query = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={query}&hl=ro&gl=RO&ceid=RO:ro"
    titles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item"):
                title = item.find("title")
                if title is not None and title.text:
                    titles.append(title.text)
                if len(titles) >= max_results:
                    break
    except Exception as e:
        logger.warning(f"RSS fetch failed for '{query_term}': {e}")
    return titles


# ---------------------------------------------------------------------------
# Gemini Helpers
# ---------------------------------------------------------------------------

# Model preference order — first available model wins
_MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]
_active_model: str = _MODEL_FALLBACK_ORDER[0]  # start with best model


def _resolve_model() -> str:
    """Return the first working Gemini model from the fallback list."""
    global _active_model
    if not _genai_client:
        return _MODEL_FALLBACK_ORDER[0]
    for model in _MODEL_FALLBACK_ORDER:
        try:
            _genai_client.models.generate_content(model=model, contents="ping")
            _active_model = model
            return model
        except Exception as e:
            if "404" in str(e) or "NOT_FOUND" in str(e):
                continue  # model not available — try next
            return model  # other errors (quota etc.) — still use this model
    return _MODEL_FALLBACK_ORDER[0]


def _call_gemini(prompt: str, model_name: str = "", retries: int = 2) -> str:
    """Call Gemini and return the raw text response. Retries on 429 rate limit.
    
    If model_name is empty, uses the globally resolved best available model.
    """
    import time, re as _re
    if not _genai_client:
        raise RuntimeError("Gemini client not initialised — GOOGLE_API_KEY missing.")
    
    # Use the working model (resolved at startup or passed explicitly)
    model = model_name if model_name else _active_model
    
    for attempt in range(retries + 1):
        try:
            response = _genai_client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "404" in err_str or "NOT_FOUND" in err_str:
                # Model unavailable — try next in fallback list
                current_idx = _MODEL_FALLBACK_ORDER.index(model) if model in _MODEL_FALLBACK_ORDER else -1
                if current_idx + 1 < len(_MODEL_FALLBACK_ORDER):
                    model = _MODEL_FALLBACK_ORDER[current_idx + 1]
                    logger.warning(f"Model {_MODEL_FALLBACK_ORDER[current_idx]} unavailable, falling back to {model}")
                    continue
                raise
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Try to parse the retryDelay from the error message
                delay_match = _re.search(r"retryDelay.*?(\d+)s", err_str)
                wait_secs = int(delay_match.group(1)) + 2 if delay_match else 30
                if attempt < retries:
                    logger.warning(
                        f"Gemini 429 quota hit on {model}. Waiting {wait_secs}s before retry "
                        f"({attempt + 1}/{retries})..."
                    )
                    time.sleep(wait_secs)
                    continue
            raise



def _clean_json(text: str) -> str:
    """Strip markdown code fences from Gemini JSON output."""
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ---------------------------------------------------------------------------
# Stage 1 — News Classification
# ---------------------------------------------------------------------------

CLASSIFICATION_PROMPT = """Ești un analist de fotbal român. Ai următoarele articole despre echipa '{opponent}':

{news_summary}

Clasifică fiecare articol în una din categoriile: injury, suspension, poor_form, positive_form, transfer_rumor, psychological, tactical, irrelevant.

Returnează JSON pur (fără explicații):
{{
  "team_sentiment": "positive|negative|neutral",
  "key_events": [
    {{"category": "injury|suspension|...", "description": "rezumat scurt 1 fraza", "player_hint": "nume jucator daca e mentionat sau null"}}
  ]
}}"""


def _classify_news(news_summary: str, opponent_name: str) -> Dict[str, Any]:
    """Stage 1: Classify what type of news exists about the opponent."""
    if not GOOGLE_API_KEY or not news_summary.strip():
        return {"team_sentiment": "neutral", "key_events": []}

    prompt = CLASSIFICATION_PROMPT.format(
        opponent=opponent_name,
        news_summary=news_summary[:4000],
    )
    try:
        raw = _call_gemini(prompt)
        return json.loads(_clean_json(raw))
    except Exception as e:
        logger.warning(f"News classification failed: {e}")
        return {"team_sentiment": "neutral", "key_events": []}


# ---------------------------------------------------------------------------
# Stage 2 — Per-Player Intelligence Extraction
# ---------------------------------------------------------------------------

INTEL_PROMPT = """Ești Principal AI Analyst la echipa de fotbal U Cluj.

STATISTICI BRUTE ale jucătorilor adversarului '{opponent}' (din meciurile recente):
{stats_json}

CONTEXT DIN PRESĂ (articole GSP.ro, Prosport.ro, Google News):
{news_summary}

CLASIFICARE EVENIMENTELOR (etapa 1):
{classification_json}

CONDIȚII METEO LA MECI ({forecast_note}):
{weather_json}

ANALIZĂ DEZAVANTAJE CLIMATICE (bazată pe țara de naștere vs. condițiile meteo):
{climate_context}

SARCINĂ:
Analizează fiecare jucător și generează un raport de scouting tactic detaliat în ROMÂNĂ.
Folosește TOATE sursele: statistici, știri, tendințe tactice, condiții meteo și dezavantaje climatice.
Dacă un jucător are un dezavantaj climatic, menționează-l explicit în physical_state și mărește overall_weakness_score proporțional.

Returnează EXCLUSIV JSON pur (fără text suplimentar, fără markdown), în formatul:
[
  {{
    "id": "player_id_din_statistici",
    "name": "Nume Jucator",
    "birth_country": "Tara de nastere",
    "climate_danger": "High|Medium|Low|None",
    "physical_state": "Stare fizica detaliata - include info meteo si climatice daca exista",
    "psychological_state": "Stare mentala, moral, presiune, context",
    "tactical_tendencies": "Cum joaca, zonele preferate, slabiciunile tactice",
    "exploit_recommendation": "Sfat concret pentru U Cluj: cum sa exploateze aceasta veriga slaba",
    "overall_weakness_score": numeric_0_to_100
  }}
]"""


def _slim_stats(player: Dict) -> Dict:
    """Return only the most relevant stat fields to keep Gemini prompt compact."""
    totals = player.get("total", {})
    role = player.get("player_role") or (
        player.get("roles", {}).get("played", [{}])[0].get("position", "")
        if player.get("roles", {}).get("played") else ""
    )
    return {
        "playerId": str(player.get("playerId", "")),
        "name": player.get("name", "Unknown"),
        "role": role,
        "birth_country": player.get("birth_country", "Unknown"),
        "aggregated_minutes": player.get("aggregated_minutes", 0),
        "aggregated_matches": player.get("aggregated_matches", 0),
        "aggregated_duels": player.get("aggregated_duels", 0),
        "aggregated_duels_won": player.get("aggregated_duels_won", 0),
        "goals": totals.get("goals", 0),
        "assists": totals.get("goalAssists", 0),
        "yellowCards": totals.get("yellowCards", 0),
        "redCards": totals.get("redCards", 0),
        "shots": totals.get("shots", 0),
        "shotsOnTarget": totals.get("shotsOnTarget", 0),
        "keyPasses": totals.get("keyPasses", 0),
        "dribbles": totals.get("dribbles", 0),
        "dribblesWon": totals.get("dribblesWon", 0),
        "aerialDuels": totals.get("aerialDuels", 0),
        "aerialDuelsWon": totals.get("aerialDuelsWon", 0),
        "fouls": totals.get("fouls", 0),
        "offsides": totals.get("offsides", 0),
    }


def _default_profile(player: Dict) -> Dict:
    """Return a stats-only profile for a player when no Gemini analysis is available."""
    minutes = player.get("aggregated_minutes", 0)
    matches = player.get("aggregated_matches", 0)
    duels = max(player.get("aggregated_duels", 1), 1)
    won = player.get("aggregated_duels_won", 0)
    win_pct = round(won / duels * 100, 1)
    role = player.get("player_role", "")
    role_str = f" ({role})" if role else ""
    return {
        "id": str(player.get("playerId", "")),
        "name": player.get("name", "Jucător Necunoscut"),
        "physical_state": f"A jucat {matches} meciuri, {minutes} minute totale. Rata câștigare dueluri: {win_pct}%. Nu există informații din presă disponibile.",
        "psychological_state": "Nu există știri specifice despre starea psihologică a acestui jucător.",
        "tactical_tendencies": f"Rol{role_str}. Dueluri totale: {player.get('aggregated_duels', 0)}, câștigate: {won}.",
        "exploit_recommendation": "Analiză bazată exclusiv pe statistici. Monitorizați comportamentul în meci.",
        "overall_weakness_score": float(player.get("weakness_score", 40)),
    }


def _extract_player_intelligence(
    db_stats: List[Dict],
    news_summary: str,
    classification: Dict,
    opponent_name: str,
    match_weather: Dict = None,
    climate_context: str = "",
) -> List[Dict]:
    """Stage 2: Per-player structured intelligence using full context.

    Guarantees that EVERY player in db_stats appears in the output —
    Gemini may skip some (especially unnamed ones); we merge fallbacks in.
    """
    if not GOOGLE_API_KEY:
        return [_default_profile(p) for p in db_stats]

    weather = match_weather or {}
    forecast_note = weather.get("forecast_note", "condițiile curente")
    weather_display = {
        k: v for k, v in weather.items() if k != "forecast_note"
    } if weather else {"info": "Date meteo indisponibile"}

    slimmed = [_slim_stats(p) for p in db_stats]

    prompt = INTEL_PROMPT.format(
        opponent=opponent_name,
        stats_json=json.dumps(slimmed, ensure_ascii=False)[:8000],
        news_summary=news_summary[:4000],
        classification_json=json.dumps(classification, ensure_ascii=False),
        forecast_note=forecast_note,
        weather_json=json.dumps(weather_display, ensure_ascii=False),
        climate_context=climate_context or "Nu există dezavantaje climatice semnificative.",
    )

    gemini_profiles: List[Dict] = []
    try:
        raw = _call_gemini(prompt)
        gemini_profiles = json.loads(_clean_json(raw))
        for p in gemini_profiles:
            try:
                p["overall_weakness_score"] = float(p.get("overall_weakness_score", 50))
            except (ValueError, TypeError):
                p["overall_weakness_score"] = 50.0
    except Exception as e:
        logger.error(f"Player intelligence extraction failed: {e}")
        return [_default_profile(p) for p in db_stats]

    # Merge: make sure every player in db_stats has an entry
    returned_ids = {str(p.get("id", "")) for p in gemini_profiles}
    returned_names = {p.get("name", "").lower() for p in gemini_profiles}

    for original in db_stats:
        pid = str(original.get("playerId", ""))
        pname = original.get("name", "").lower()
        if pid not in returned_ids and pname not in returned_names:
            gemini_profiles.append(_default_profile(original))
            logger.debug(f"Added fallback profile for '{original.get('name', pid)}'")

    return gemini_profiles


# ---------------------------------------------------------------------------
# Main Public API
# ---------------------------------------------------------------------------

def generate_pregame_intelligence(
    db_data: List[Dict[str, Any]],
    opponent_name: str = "Adversar",
) -> List[Dict[str, Any]]:
    """
    Legacy entry point — still works for GDGDatabaseProvider.
    Uses RSS fallback (no scraping) since we don't have player names here.
    """
    player_news_context = {}
    for p in db_data:
        p_name = p.get("name", "Unknown")
        if p_name not in ("Unknown",) and not p_name.startswith("Player"):
            player_news_context[p_name] = fetch_news(p_name, is_player=True, max_results=2)

    team_news = fetch_news(opponent_name, is_player=False, max_results=5)

    if not GOOGLE_API_KEY:
        for p in db_data:
            p["overall_weakness_score"] = float(p.get("weakness_score", 50))
        return db_data

    news_summary = f"Știri echipă: {json.dumps(team_news)}\nȘtiri jucători: {json.dumps(player_news_context)}"
    classification = _classify_news(news_summary, opponent_name)
    return _extract_player_intelligence(db_data, news_summary, classification, opponent_name)


def generate_pregame_intelligence_v2(
    db_stats: List[Dict[str, Any]],
    opponent_name: str,
    scraped_news: Dict[str, Any],
    match_weather: Dict[str, Any] = None,
    climate_context: str = "",
) -> List[Dict[str, Any]]:
    """
    Enhanced entry point — uses full scraped articles + match-day weather + climate analysis.
    Called by LocalFilesProvider.
    """
    from services.climate_engine import (
        get_player_climate_zone,
        assess_climate_disadvantage,
        build_climate_context_for_prompt,
    )

    # If climate_context not pre-built, build it now from player birth_country + weather
    if not climate_context and match_weather:
        for p in db_stats:
            zone = get_player_climate_zone(p.get("birth_country", ""))
            assessment = assess_climate_disadvantage(zone, match_weather)
            p["_climate_zone"] = zone
            p["_climate_assessment"] = assessment
        climate_context = build_climate_context_for_prompt(db_stats)

    news_summary = summarize_for_prompt(scraped_news, max_chars_per_section=2500)

    # Stage 1: classify events
    classification = _classify_news(news_summary, opponent_name)
    logger.info(
        f"News classification for '{opponent_name}': "
        f"sentiment={classification.get('team_sentiment')}, "
        f"events={len(classification.get('key_events', []))}"
    )

    # Stage 2: per-player intelligence with weather + climate enrichment
    profiles = _extract_player_intelligence(
        db_stats, news_summary, classification, opponent_name,
        match_weather=match_weather,
        climate_context=climate_context,
    )

    # Post-process: stamp climate_danger + birth_country onto each profile
    # Build a lookup from the db_stats we enriched
    stats_by_name = {
        p.get("name", "").lower(): p for p in db_stats
    }
    for profile in profiles:
        name_key = profile.get("name", "").lower()
        original = stats_by_name.get(name_key, {})
        # If Gemini already set climate_danger, keep it; otherwise inject from our engine
        if not profile.get("climate_danger"):
            assessment = original.get("_climate_assessment", {})
            profile["climate_danger"] = assessment.get("severity", "None")
        if not profile.get("birth_country"):
            profile["birth_country"] = original.get("birth_country", "Unknown")

    return profiles


# ---------------------------------------------------------------------------
# Chronic Gaps Generation
# ---------------------------------------------------------------------------

GAPS_PROMPT = """Ești Principal AI Analyst la echipa de fotbal U Cluj.

ANALIZĂ DE VULNERABILITĂȚI JUCĂTORI PENTRU ADVERSARUL '{opponent}':
{weakness_summary}

ISTORIC MECIURI (rezumat):
{matches_summary}

SARCINĂ:
Pe baza stării fizice/psihologice a jucătorilor și a tendințelor din meciurile trecute, identifică 1-3 GOLURI TACTICE CRONICE (Chronic Gaps) în așezarea sau jocul adversarului.
Acestea pot fi flancuri vulnerabile, distanțe prea mari între linii, sau probleme la tranziția negativă.

Pentru fiecare vulnerabilitate, trebuie să furnizezi o locație aproximativă (ex: "Left Flank", "Central Defensive Midfield") și coordonate spațiale aproximative pentru un teren de fotbal reprezentat ca un procent din ecran:
- x: de la 0 (stânga) la 100 (dreapta)
- y: de la 0 (sus) la 100 (jos)
- w: lățimea zonei
- h: înălțimea zonei
(ex: x: 10.0, y: 30.0, w: 20.0, h: 40.0)

Returnează EXCLUSIV JSON pur în formatul:
[
  {{
    "id": "unique_gap_id",
    "location": "Numele zonei vulnerabile",
    "description": "Descrierea tactică detaliată a vulnerabilității (în ROMÂNĂ)",
    "severity": "Critical|High|Medium",
    "coordinates": {{"x": float, "y": float, "w": float, "h": float}}
  }}
]"""


def generate_chronic_gaps(
    opponent_name: str,
    weakness_data: List[Dict[str, Any]],
    matches_summary: str
) -> List[Dict[str, Any]]:
    if not GOOGLE_API_KEY:
        # Fallback offline
        return [{
            "id": "gap_offline_1",
            "location": "Flancul Stâng / Half Space",
            "description": f"Date istorice arată o vulnerabilitate cronică pe flancul stâng pentru {opponent_name}.",
            "severity": "High",
            "coordinates": {"x": 20.0, "y": 20.0, "w": 30.0, "h": 60.0}
        }]

    # Slim down weakness data to save tokens
    slim_weakness = []
    for p in weakness_data:
        slim_weakness.append({
            "name": p.get("name", ""),
            "score": p.get("overall_weakness_score", 0),
            "physical": p.get("physical_state", ""),
            "tactics": p.get("tactical_tendencies", "")
        })
    
    prompt = GAPS_PROMPT.format(
        opponent=opponent_name,
        weakness_summary=json.dumps(slim_weakness, ensure_ascii=False)[:3000],
        matches_summary=matches_summary[:2000]
    )

    try:
        raw = _call_gemini(prompt)
        gaps = json.loads(_clean_json(raw))
        # Ensure Rect format compatibility
        for gap in gaps:
            coords = gap.get("coordinates", {})
            gap["coordinates"] = {
                "x": float(coords.get("x", 0)),
                "y": float(coords.get("y", 0)),
                "w": float(coords.get("w", 0)),
                "h": float(coords.get("h", 0))
            }
        return gaps
    except Exception as e:
        logger.error(f"Chronic gaps extraction failed: {e}")
        return [{
            "id": "gap_error_1",
            "location": "Unknown",
            "description": "A apărut o eroare la generarea gap-urilor tactice. Monitorizați meciul live.",
            "severity": "Medium",
            "coordinates": {"x": 40.0, "y": 40.0, "w": 20.0, "h": 20.0}
        }]
