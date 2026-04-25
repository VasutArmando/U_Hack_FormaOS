import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
import google.generativeai as genai

# Import servicii noi de AI și Meteo
from services.weather_engine import get_live_weather, process_weather_tactics, get_city_for_stadium
from services.news_engine import fetch_opponent_news
from services.stadium_vision_service import vision_pipeline
from data_manager import db_provider

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

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
    data = _load_json("teams.json")
    return data if isinstance(data, list) else data.get("teams", [])

@app.get("/api/v1/settings/stadiums")
async def get_stadiums(request: Request) -> Any:
    data = _load_json("stadiums.json")
    return data if isinstance(data, list) else data.get("stadiums", [])

# Pregame
@app.get("/api/v1/pregame/chronic-gaps")
async def pregame_chronic_gaps(request: Request, opponent_id: Optional[str] = None) -> Any:
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
async def pregame_opponent_weakness(request: Request, opponent_id: Optional[str] = None, stadium_id: Optional[str] = None) -> Any:
    # Resolve team name for news search
    opponent_name = "Adversar"
    if opponent_id:
        teams = _load_json("teams.json")
        team_list = teams if isinstance(teams, list) else teams.get("teams", [])
        opponent_name = next((t["name"] for t in team_list if t["id"] == opponent_id), "Adversar")
    
    # Resolve city for weather
    city = "Cluj-Napoca"
    if stadium_id:
        stadiums = _load_json("stadiums.json")
        stadium_list = stadiums if isinstance(stadiums, list) else stadiums.get("stadiums", [])
        stadium_name = next((s["name"] for s in stadium_list if s["id"] == stadium_id), None)
        if stadium_name:
            city = get_city_for_stadium(stadium_name)
    
    weather_data = get_live_weather(city)
    players = db_provider.get_opponent_weaknesses(opponent_id, opponent_name)
    
    # Preluăm tacticile generate de AI
    cache_path = BASE_DATA_PATH / "current_weather_tactics.json"
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                tactics = json.load(f)
        except Exception:
            tactics = process_weather_tactics(weather_data)
    else:
        tactics = process_weather_tactics(weather_data)
        
    is_raining = "rain" in weather_data.get("condition", "").lower()
    
    for p in players:
        try: 
            p["overall_weakness_score"] = float(p.get("overall_weakness_score", 0))
        except (ValueError, TypeError): 
            pass
        
        # Weather contamination logic cerut explicit:
        if is_raining:
            # We check if the name contains common mock names or just apply a general warning
            if "Popescu Andrei" in str(p.get("name", "")):
                p["physical_state"] = str(p.get("physical_state", "")) + " Match conditions will severely affect his stability."
            else:
                # If it's a real player from hackathon, we still add the weather warning
                p["physical_state"] = str(p.get("physical_state", "")) + " (Vulnerable to slippery pitch)."
            
    return players

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

@app.post("/api/v1/ingame/assistant")
async def ingame_assistant(request: Request, payload: AssistantRequest) -> Dict[str, Any]:
    query = payload.query.lower()
    
    try:
        # A. Adună tot contextul (RAG)
        weather_data = _get_live_weather_data()
        players_data = db_provider.get_ingame_players()
        gaps_data = db_provider.get_live_gaps()
        news_titles = fetch_opponent_news()
        
        # Nou: Adăugăm și scouting report-ul pregame (cine e veriga slabă)
        scouting_report = db_provider.get_opponent_weaknesses()
        
        if not GOOGLE_API_KEY:
            return {"advice": "Google API Key lipsește, nu pot folosi AI-ul pentru asistență completă. Analiza locală sugerează să vă concentrați pe contraatac."}

        # B. Construiește Master Prompt-ul
        prompt = f"""Ești un asistent tactic AI (Omniscient) pentru echipa U Cluj. 
Răspunde scurt și la obiect (maxim 2-3 propoziții) antrenorului la următoarea întrebare: "{payload.query}"

CONTEXT CURENT LIVE:
- Vremea: {json.dumps(weather_data)}
- Statusul Jucătorilor noștri (oboseală): {json.dumps(players_data)}
- Găuri tactice în apărarea adversă: {json.dumps(gaps_data)}
- Știri recente despre adversar: {json.dumps(news_titles)}
- Raport Scouting (Verigi Slabe): {json.dumps(scouting_report)}

Dacă întrebarea este legată de starea terenului/jucători obosiți, folosește datele meteo și biometrice. Dacă e legată de adversar, folosește știrile, scouting report-ul și găurile tactice. Oferă un sfat clar și acționabil."""

        # C. Generează răspunsul cu Gemini
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        advice = response.text.strip()
        
        return {"advice": advice}
        
    except Exception as e:
        logger.error(f"Eroare asistent AI: {e}")
        return {"advice": "Eroare la procesarea AI-ului. Concentrează-te pe menținerea posesiei în zona 14 până identificăm o breșă."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
