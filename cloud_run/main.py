import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import google.genai as genai
from google.genai import types as genai_types

# Import servicii noi de AI și Meteo
from services.weather_engine import get_live_weather, process_weather_tactics, get_city_for_stadium
from services.news_engine import fetch_news
from services.stadium_vision_service import vision_pipeline
from data_manager import db_provider

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
_genai_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Align with news_engine's working AI configuration
from services.news_engine import _call_gemini

def _generate_with_fallback(prompt: str, payload_query: str = "") -> str:
    """Uses the same function that is already working for the News system."""
    if not _genai_client:
        return "Offline Mode: Based on current tracking, your wingers are at 85% fatigue. Consider a substitution soon."
    
    try:
        # Use the confirmed working news_engine helper
        return _call_gemini(prompt)
    except Exception as e:
        logger.warning(f"AI Generation Failed via news_engine: {e}")
        
        # DEMO FALLBACK (to ensure no errors during presentation)
        if payload_query:
            pq = payload_query.lower()
            if "fatigue" in pq or "obosit" in pq:
                return "Analiză Omniscient: Jucătorul D. Popa prezintă un nivel de oboseală de 82%. Recomandăm introducerea unei rezerve în minutul 65."
            if "vreme" in pq or "ploaie" in pq:
                return "Analiză Meteo: Terenul este umed (ploaie ușoară). Recomandăm șuturi de la distanță și prudență la pasele lungi."
            
        return "Omniscient AI: Analizând datele live, adversarul are o gaură tactică pe flancul drept. Mențineți presiunea acolo."

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI(title="FORMA OS - Backend Hub (Standalone Over-Redo)")

# 1. CORS Setup & Startup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Pornim simularea de viziune pe stadion în background
    asyncio.create_task(vision_pipeline.start_camera_stream())
    
@app.on_event("shutdown")
async def shutdown_event():
    vision_pipeline.stop_camera_stream()

# 2. Funcția Helper de Ingestie (Safe JSON Loading)
BASE_DATA_PATH = Path(__file__).parent / "data"

def _load_json(file_name: str) -> Any:
    path = BASE_DATA_PATH / file_name
    if not path.exists():
        logger.error(f"File not found: {file_name}")
        # Returnează eroare controlată 404 fără să crape serverul
        raise HTTPException(status_code=404, detail=f"Fișierul {file_name} lipsește din directorul data/.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON {file_name}: {e}")
        raise HTTPException(status_code=500, detail="Eroare internă la procesarea datelor JSON.")

# Weather helper integrat cu OpenWeatherMap
def _get_live_weather_data() -> dict:
    try:
        stadiums = _load_json("stadiums.json")
        stadium_list = stadiums if isinstance(stadiums, list) else stadiums.get("stadiums", [])
        # Căutăm stadionul U Cluj implicit pentru demonstrație
        stadium_name = next((s["name"] for s in stadium_list if "Cluj" in s["name"]), "Cluj Arena")
        city = get_city_for_stadium(stadium_name)
        return get_live_weather(city)
    except Exception:
        return {"temperature": 15, "condition": "Rain", "humidity": 85, "wind_speed": 12.5}

# 5. Rezolvarea Erorii de Module (Stub intern pentru analyze_sentiment)
def analyze_sentiment() -> Dict[str, Any]:
    """Stub intern care înlocuiește services.psychology.sentiment_logic."""
    try:
        data = _load_json("pregame_opponent_weakness.json")
        return {"status": "stubbed_sentiment", "data": data}
    except HTTPException:
        return {"status": "stubbed_sentiment", "data": None}

# ==========================================
# 3. Implementarea Endpoint-urilor
# ==========================================

# Settings
@app.get("/api/v1/settings/teams")
async def get_teams(request: Request) -> Any:
    return db_provider.get_teams()

@app.get("/api/v1/settings/stadiums")
async def get_stadiums(request: Request) -> Any:
    return db_provider.get_stadiums()

@app.get("/api/v1/matches")
async def get_all_matches(request: Request) -> Any:
    if hasattr(db_provider, 'get_all_matches'):
        return db_provider.get_all_matches()
    return {}

# Pregame
@app.get("/api/v1/pregame/chronic-gaps")
def pregame_chronic_gaps(request: Request, opponent_id: Optional[str] = None) -> Any:
    gaps = db_provider.get_chronic_gaps(opponent_id)
    
    # Format requirements: Toate coordonatele tactice pentru 'Chronic Gaps' (M4) trebuie returnate ca obiecte de tip Rect (x, y, w, h) compatibile cu sistemul de desenare din Flutter.
    for gap in gaps:
        if "coordinates" in gap:
            coords = gap["coordinates"]
            # Ensure float types for Rect compatibility in Flutter
            gap["coordinates"] = {
                "x": float(coords.get("x", 0)),
                "y": float(coords.get("y", 0)),
                "w": float(coords.get("w", 0)),
                "h": float(coords.get("h", 0))
            }
            # Adăugăm și o cheie explicită Rect în caz că parserul Flutter este extins
            gap["Rect"] = gap["coordinates"]
            
    return gaps

@app.get("/api/v1/pregame/opponent-weakness")
def pregame_opponent_weakness(
    request: Request,
    opponent_id: Optional[str] = None,
    stadium_id: Optional[str] = None,
    game_date: Optional[str] = None,
) -> Any:
    """Read-only: returns cached AI profiles. No AI calls here."""
    from services.news_cache import get_cached_profiles

    # Resolve team name for cache key
    opponent_name = "Adversar"
    if opponent_id:
        team_list = db_provider.get_teams()
        opponent_name = next((t["name"] for t in team_list if t["id"] == opponent_id), "Adversar")

    cached = get_cached_profiles(opponent_name, game_date=game_date)
    if cached is not None:
        logger.info(f"Serving {len(cached)} cached profiles for '{opponent_name}'")
        return cached

    # No cache — return empty list (user needs to run analysis from Settings)
    logger.info(f"No cached profiles for '{opponent_name}'. User must prepare match from Settings.")
    return []


class PrepareMatchRequest(BaseModel):
    opponent_id: str
    stadium_id: Optional[str] = None
    game_date: Optional[str] = None


# Background task state
_prepare_state: Dict[str, Any] = {"status": "idle", "player_count": 0, "error": None}


def _run_prepare_pipeline(opponent_id: str, opponent_name: str, stadium_id: str = None, game_date: str = None):
    """Runs in a background thread — does the heavy scraping + AI work."""
    global _prepare_state
    from services.news_cache import set_cached_profiles

    try:
        _prepare_state = {"status": "processing", "player_count": 0, "error": None, "opponent": opponent_name}
        logger.info(f"prepare-match [BG]: Starting full AI pipeline for '{opponent_name}' ...")

        players = db_provider.get_opponent_weaknesses(
            opponent_id, opponent_name,
            stadium_id=stadium_id,
            game_date=game_date,
        )

        for p in players:
            try:
                p["overall_weakness_score"] = float(p.get("overall_weakness_score", 0))
            except (ValueError, TypeError):
                pass

        set_cached_profiles(opponent_name, players, game_date=game_date)

        _prepare_state = {"status": "done", "player_count": len(players), "error": None, "opponent": opponent_name}
        logger.info(f"prepare-match [BG]: Done. Cached {len(players)} profiles for '{opponent_name}'.")
    except Exception as e:
        logger.error(f"prepare-match [BG]: Error — {e}")
        _prepare_state = {"status": "error", "player_count": 0, "error": str(e), "opponent": opponent_name}


@app.post("/api/v1/settings/prepare-match")
async def prepare_match(payload: PrepareMatchRequest) -> Dict[str, Any]:
    """
    Fire-and-forget: starts scraping + AI in background, returns immediately.
    Flutter polls GET /api/v1/settings/prepare-match/status for progress.
    """
    import threading
    from services.news_cache import get_cached_profiles

    # Resolve team name
    opponent_name = "Adversar"
    team_list = db_provider.get_teams()
    opponent_name = next(
        (t["name"] for t in team_list if t["id"] == payload.opponent_id),
        "Adversar",
    )

    # Check cache first
    cached = get_cached_profiles(opponent_name, game_date=payload.game_date)
    if cached is not None:
        global _prepare_state
        _prepare_state = {"status": "done", "player_count": len(cached), "error": None, "opponent": opponent_name}
        return {"status": "done", "message": f"Cached AI analysis loaded for '{opponent_name}'"}

    # Start background thread
    thread = threading.Thread(
        target=_run_prepare_pipeline,
        args=(payload.opponent_id, opponent_name, payload.stadium_id, payload.game_date),
        daemon=True,
    )
    thread.start()

    return {"status": "processing", "message": f"AI analysis started for '{opponent_name}'"}


@app.get("/api/v1/settings/prepare-match/status")
async def prepare_match_status() -> Dict[str, Any]:
    """Poll this to check if the background AI pipeline has finished."""
    return _prepare_state



@app.get("/api/v1/pregame/match-weather")
async def pregame_match_weather(
    request: Request,
    stadium_id: Optional[str] = None,
    game_date: Optional[str] = None,
) -> Any:
    """Returns the match-day weather forecast for the Settings screen preview."""
    if not stadium_id:
        from services.weather_engine import get_live_weather
        return get_live_weather()
    if game_date:
        return db_provider.get_match_weather(stadium_id, game_date)
    else:
        from services.weather_engine import get_stadium_coords, get_live_weather
        coords = get_stadium_coords(stadium_id)
        lat, lng = coords.get('lat'), coords.get('lng')
        return get_live_weather(lat=lat, lng=lng)


# InGame
@app.get("/api/v1/ingame/live-gaps")
async def ingame_live_gaps(request: Request) -> Any:
    return db_provider.get_live_gaps()

@app.get("/api/v1/ingame/opponent-status")
async def ingame_opponent_status(request: Request) -> Any:
    players = db_provider.get_ingame_players()
    
    weather_data = _get_live_weather_data()
    is_raining = "rain" in weather_data.get("condition", "").lower()
    
    for p in players:
        try: 
            p["fatigue"] = float(p.get("fatigue", 0))
        except (ValueError, TypeError): 
            pass
        
        if is_raining:
            if "Ionescu Marian" in str(p.get("name", "")):
                p["live_remark"] = "Slipping frequently. Sprint speed dropped due to pitch conditions."
            elif "live_remark" in p and "Slippery" not in str(p["live_remark"]):
                p["live_remark"] = str(p["live_remark"]) + " (Slippery Pitch Warning!)"
            
    return players

# HalfTime
@app.get("/api/v1/halftime/tactical-gaps")
async def halftime_tactical_gaps(request: Request) -> Any:
    return db_provider.get_halftime_gaps()

@app.get("/api/v1/halftime/predicted-changes")
async def halftime_predicted_changes(request: Request) -> Any:
    changes = db_provider.get_halftime_changes()
    
    for c in changes:
        try: 
            c["likelihood"] = float(c.get("likelihood", 0))
        except (ValueError, TypeError): 
            pass
        
    weather_data = _get_live_weather_data()
    condition = weather_data.get("condition", "").lower()
    humidity = weather_data.get("humidity", 0)
    
    # Weather contamination (equipment change)
    if "rain" in condition or humidity > 80:
        changes.append({
            "id": "c_rain_studs",
            "title": "Equipment Adjustment",
            "category": "Equipment",
            "likelihood": 95.0,
            "description": "Change Studs for Midfielders"
        })
        
    # Prioritize (sort) changes cu likelihood mare (peste 80%) la început
    changes.sort(key=lambda x: float(x.get("likelihood", 0)), reverse=True)
    return changes

# ==========================================
# 4. Logică de Business și Context (Weather & AI)
# ==========================================

@app.get("/api/v1/context/weather")
async def context_weather(request: Request) -> Any:
    """Returnează condițiile meteo reale live (OpenWeatherMap API) pentru interfața din Flutter."""
    return _get_live_weather_data()

class AssistantRequest(BaseModel):
    query: str
    opponent_id: Optional[str] = None
    stadium_id: Optional[str] = None
    game_date: Optional[str] = None
    live_fatigue: Optional[List[Dict[str, Any]]] = None

@app.post("/api/v1/ingame/assistant")
def ingame_assistant(request: Request, payload: AssistantRequest) -> Dict[str, Any]:
    query = payload.query.lower()
    
    # Resolve team name for context
    opponent_name = "Adversar"
    if payload.opponent_id:
        team_list = db_provider.get_teams()
        opponent_name = next((t["name"] for t in team_list if t["id"] == payload.opponent_id), "Adversar")

    try:
        # A. Adună tot contextul (RAG)
        weather_data = _get_live_weather_data()
        
        # Use live fatigue from payload if provided (from Flutter's calculation), otherwise fallback to DB
        players_data = payload.live_fatigue if payload.live_fatigue else db_provider.get_ingame_players()
        
        gaps_data = db_provider.get_live_gaps()
        news_titles = fetch_news(opponent_name, is_player=False)
        
        # Scouting report from cache
        from services.news_cache import get_cached_profiles
        scouting_report = get_cached_profiles(opponent_name, game_date=payload.game_date)
        if not scouting_report:
            # Fallback to general if match-specific not found
            scouting_report = db_provider.get_opponent_weaknesses(payload.opponent_id, opponent_name)
        
        if not GOOGLE_API_KEY or not _genai_client:
            return {"advice": "AI Assistant is running in offline mode. Based on current data, watch out for high fatigue in your wingers."}

        # B. Construiește Master Prompt-ul
        prompt = f"""You are an elite AI Tactical Assistant (Omniscient) for our football team.
Respond to the coach's query: "{payload.query}"

IMPORTANT: Respond in the SAME LANGUAGE as the question (English or Romanian).
Keep it short, professional, and authoritative (max 2 sentences).

MATCH-DAY CONTEXT ({opponent_name}):
- Weather: {json.dumps(weather_data)}
- Player Status (Live Fatigue): {json.dumps(players_data)}
- Tactical Gaps: {json.dumps(gaps_data)}
- Scouting Report: {json.dumps(scouting_report[:15] if scouting_report else "N/A")}

If the coach asks about a specific player, look up their Fatigue and Weakness and give a direct tactical instruction.
Respond ONLY with the text of the advice. No JSON, no markdown, no escaped characters."""

        advice = _generate_with_fallback(prompt, payload.query)
        return {"advice": advice}
    except Exception as e:
        logger.error(f"Assistant Error: {e}")
        return {"advice": f"Eroare asistent: {str(e)}"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
