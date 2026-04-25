import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import servicii noi de AI și Meteo
from services.weather_engine import get_live_weather, process_weather_tactics, get_city_for_stadium

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI(title="FORMA OS - Backend Hub (Standalone Over-Redo)")

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def pregame_chronic_gaps(request: Request) -> Any:
    data = _load_json("pregame_gaps.json")
    gaps = data if isinstance(data, list) else data.get("gaps", [])
    
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
async def pregame_opponent_weakness(request: Request) -> Any:
    weather_data = _get_live_weather_data()
    raw_data = _load_json("pregame_opponent_weakness.json")
    players = raw_data if isinstance(raw_data, list) else raw_data.get("players", [])
    
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
            if "Popescu Andrei" in str(p.get("name", "")):
                p["physical_state"] = str(p.get("physical_state", "")) + " Match conditions will severely affect his stability."
            
            # Putem pune tactical suggestion global într-un state psihologic / descriere dacă vrem
            
    return players

# InGame
@app.get("/api/v1/ingame/live-gaps")
async def ingame_live_gaps(request: Request) -> Any:
    data = _load_json("ingame_gaps.json")
    return data if isinstance(data, list) else data.get("gaps", [])

@app.get("/api/v1/ingame/opponent-status")
async def ingame_opponent_status(request: Request) -> Any:
    data = _load_json("ingame_players.json")
    players = data if isinstance(data, list) else data.get("players", [])
    
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
    data = _load_json("halftime_gaps.json")
    return data if isinstance(data, list) else data.get("gaps", [])

@app.get("/api/v1/halftime/predicted-changes")
async def halftime_predicted_changes(request: Request) -> Any:
    data = _load_json("halftime_changes.json")
    changes = data if isinstance(data, list) else data.get("changes", [])
    
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
    
    # A. Interogări despre Jucători (Oboseală/Status)
    if any(k in query for k in ["oboseală", "oboseala", "obosit", "jucător", "jucator", "ionescu", "popescu", "fatigue"]):
        try:
            raw_p = _load_json("ingame_players.json")
            players_data = raw_p if isinstance(raw_p, list) else raw_p.get("players", [])
            
            # Caută dacă e menționat vreun nume de jucător în query
            mentioned_player = None
            for p in players_data:
                name_parts = p.get("name", "").lower().split()
                if any(part in query for part in name_parts if len(part) >= 3):
                    mentioned_player = p
                    break
            
            # Găsește jucătorul menționat sau cel mai obosit jucător
            target_player = mentioned_player if mentioned_player else max(players_data, key=lambda p: float(p.get("fatigue", 0)))
            
            short_name = target_player.get("name", "Jucătorul").split()[0]
            remark = target_player.get("live_remark", "Prezintă semne de oboseală.")
            
            # Sabău Style
            return {"advice": f"{short_name} este epuizat! {remark} Trebuie să atacăm acea zonă acum!"}
        except Exception:
            pass # Lăsăm să cadă în Fallback
            
    # B. Interogări despre Tactica Adversarului (Găuri/Spații)
    if any(k in query for k in ["spații", "spatii", "găuri", "gauri", "unde", "vulnerabil"]):
        try:
            raw_g = _load_json("ingame_gaps.json")
            gaps_data = raw_g if isinstance(raw_g, list) else raw_g.get("gaps", [])
            
            # Returnează locația și descrierea gap-ului cu severitatea cea mai mare (Critical sau High)
            critical_gaps = [g for g in gaps_data if str(g.get("severity", "")).lower() == "critical"]
            if not critical_gaps:
                critical_gaps = [g for g in gaps_data if str(g.get("severity", "")).lower() == "high"]
            if not critical_gaps:
                critical_gaps = gaps_data
            
            if critical_gaps:
                gap = critical_gaps[0]
                # Sabău Style
                return {"advice": f"Adversarul e vulnerabil pe {gap.get('location')}! {gap.get('description')} Forțați atacul acolo imediat!"}
        except Exception:
            pass # Lăsăm să cadă în Fallback
            
    # C. Stabilitate (Fallback)
    return {"advice": "Analizez datele de joc... Concentrează-te pe menținerea posesiei în zona 14 până identificăm o breșă."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
