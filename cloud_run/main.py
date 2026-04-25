import os
import json
import logging
import random
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, Request, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import firebase_admin
from firebase_admin import auth

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from tasks import analyze_heavy_payload
from oracle.passing_networks import get_opponent_passing_network
from data_manager import DataManager
from intelligence_engine import TacticalBrain
from services.psychology.psychology_logic import PsychologyBrain
from services.psychology.sentiment_logic import SentimentScout

from tactical_intelligence import TacticalIntelligence
from set_piece_analytics import SetPieceAnalyzer
from spatial_analytics import target_man_optimization, detect_opponent_gaps
from set_piece_analytics import detect_defensive_5plus1

# ---------------------------------------------------------------
# FastAPI Application & Global Config
# ---------------------------------------------------------------
app = FastAPI(title="FORMA OS - Backend Hub (Refactored)")

# CORS – allow any origin for Flutter integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (kept from previous version)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------
# Logging (structured JSON for demo)
# ---------------------------------------------------------------
class GcpJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {"severity": record.levelname, "message": record.getMessage(), "module": record.module}
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms
        return json.dumps(log_record)

logger = logging.getLogger("forma_os")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(GcpJsonFormatter())
if not logger.handlers:
    logger.addHandler(handler)

# ---------------------------------------------------------------
# Security (Firebase token – demo friendly)
# ---------------------------------------------------------------
security = HTTPBearer()
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

def verify_firebase_token(cred: HTTPAuthorizationCredentials = Depends(security)):
    if DEMO_MODE:
        return {"uid": "demo-sabau", "COACH": True, "club_id": "tenant_u_cluj"}
    try:
        token = auth.verify_id_token(cred.credentials)
        if "club_id" not in token:
            raise HTTPException(status_code=403, detail="Missing tenant identifier.")
        return token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

# ---------------------------------------------------------------
# Global Instances
# ---------------------------------------------------------------
data_manager = DataManager()
tactical_brain = TacticalBrain()
psychology_brain = PsychologyBrain()
tactical_intel = TacticalIntelligence()
psychology_cache: Dict[str, Any] = {}

# ---------------------------------------------------------------
# Helper – Load local JSON with graceful fallback
# ---------------------------------------------------------------
BASE_DATA_PATH = Path(__file__).parent / ".." / "data" / "raw_json"

def _load_json(file_name: str) -> Any:
    path = (BASE_DATA_PATH / file_name).resolve()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Missing JSON file: {path}. Returning fallback for U Cluj.")
        # Minimal fallback structure – can be expanded per endpoint
        return {}
    except json.JSONDecodeError:
        logger.error(f"Corrupt JSON in file: {path}. Returning empty dict.")
        return {}

# ---------------------------------------------------------------
# WebSocket – Telemetry (unchanged from previous version)
# ---------------------------------------------------------------
active_websockets: List[WebSocket] = []

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    home_base = [[20.0, 30.0], [25.5, 45.1], [40.2, 50.0], [35.0, 20.0]]
    try:
        while True:
            jittered = [[p[0] + random.uniform(-0.3, 0.3), p[1] + random.uniform(-0.3, 0.3)] for p in home_base]
            payload = {"type": "LIVE_TELEMETRY", "timestamp": time.time(), "home_positions_live": jittered}
            await websocket.send_json(payload)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# ---------------------------------------------------------------
# Settings Module
# ---------------------------------------------------------------
@app.get("/api/v1/settings/teams")
@limiter.limit("20/minute")
async def get_teams() -> List[Dict]:
    """Return the full list of SuperLiga teams from `teams.json`."""
    data = _load_json("teams.json")
    return data.get("teams", [])

@app.get("/api/v1/settings/stadiums")
@limiter.limit("20/minute")
async def get_stadiums() -> List[Dict]:
    """Return active Romanian stadiums from `stadiums.json`."""
    data = _load_json("stadiums.json")
    return data.get("stadiums", [])

# ---------------------------------------------------------------
# Pregame Module
# ---------------------------------------------------------------
@app.get("/api/v1/pregame/chronic-gaps")
@limiter.limit("15/minute")
async def pregame_chronic_gaps() -> List[Dict]:
    """Historical tactical gap locations and severity.
    Source: `pregame_gaps.json`.
    """
    data = _load_json("pregame_gaps.json")
    return data.get("gaps", [])

@app.get("/api/v1/pregame/opponent-weakness")
@limiter.limit("15/minute")
async def pregame_opponent_weakness(
    physical_state: str | None = None,
    psychological_state: str | None = None,
) -> List[Dict]:
    """List opponent players with filters.
    - `physical_state` can be `injury`, `weather_impact`, etc.
    - `psychological_state` can be `low_morale`, `negative_media`.
    """
    data = _load_json("pregame_opponent_weakness.json")
    players = data.get("players", [])
    if physical_state:
        players = [p for p in players if p.get("physical_state") == physical_state]
    if psychological_state:
        players = [p for p in players if p.get("psychological_state") == psychological_state]
    return players

# ---------------------------------------------------------------
# In‑Game (Live) Module
# ---------------------------------------------------------------
@app.get("/api/v1/ingame/live-gaps")
@limiter.limit("20/minute")
async def ingame_live_gaps() -> List[Dict]:
    """Current exploitable gaps based on live conditions.
    Source: `ingame_gaps.json`.
    """
    data = _load_json("ingame_gaps.json")
    return data.get("gaps", [])

@app.get("/api/v1/ingame/opponent-status")
@limiter.limit("20/minute")
async def ingame_opponent_status() -> List[Dict]:
    """Live fatigue and performance remarks for opponent players.
    Source: `ingame_players.json`.
    """
    data = _load_json("ingame_players.json")
    return data.get("players", [])

class AssistantRequest(BaseModel):
    query: str
    # Optional context fields could be added later

@app.post("/api/v1/ingame/assistant")
@limiter.limit("30/minute")
async def ingame_assistant(request: Request, payload: AssistantRequest) -> Dict:
    """AI Assistant – simple rule‑based responder using local JSON.
    It parses the query and returns a concise answer.
    """
    query = payload.query.lower()
    # Load player data once
    players_data = _load_json("ingame_players.json").get("players", [])
    # Simple heuristics
    if "obosit" in query or "fatigue" in query:
        # Expect a name after the keyword
        for player in players_data:
            name = player.get("name", "").lower()
            if name in query:
                fatigue = player.get("fatigue", "N/A")
                return {"advice": f"{player.get('name')} are un nivel de oboseală de {fatigue}."}
        return {"advice": "Nu am găsit jucătorul cerut în datele live."}
    if "goluri" in query and "apărare" in query:
        gaps = _load_json("ingame_gaps.json").get("gaps", [])
        defense_gaps = [g for g in gaps if g.get("type") == "defense"]
        return {"advice": f"În prezent există {len(defense_gaps)} zone vulnerabile în apărare."}
    # Fallback generic response using Gemini (if available)
    try:
        # Re‑use the existing psychology_brain for Gemini calls
        response = psychology_brain.generate_plan(query)
        # Return concise coach advice format
    return {"advice": response}
    except Exception as e:
        logger.error(f"Assistant fallback failed: {e}")
        return {"advice": "Nu am putut genera un răspuns în acest moment."}

# ---------------------------------------------------------------
# Half‑Time Module
# ---------------------------------------------------------------
@app.get("/api/v1/halftime/tactical-gaps")
@limiter.limit("15/minute")
async def halftime_tactical_gaps() -> List[Dict]:
    """Analysis of gaps after the first half.
    Source: `halftime_gaps.json`.
    """
    data = _load_json("halftime_gaps.json")
    return data.get("gaps", [])

@app.get("/api/v1/halftime/predicted-changes")
@limiter.limit("15/minute")
async def halftime_predicted_changes() -> List[Dict]:
    """Predicted opponent adjustments (Offensive, Equipment, Tactical).
    Source: `halftime_changes.json` sorted by likelihood.
    """
    data = _load_json("halftime_changes.json")
    changes = data.get("changes", [])
    # Ensure descending order by a 'likelihood' key if present
    changes.sort(key=lambda x: x.get("likelihood", 0), reverse=True)
    return changes

# ---------------------------------------------------------------
# Settings Persistence – Save current match configuration
# ---------------------------------------------------------------
class MatchConfig(BaseModel):
    opponent: str
    date: str
    stadium: str

@app.post("/api/v1/settings/save")
@limiter.limit("10/minute")
async def save_match_settings(payload: MatchConfig) -> Dict:
    """Simulate persisting match configuration to `current_match.json`."""
    config_path = Path(__file__).parent / ".." / "data" / "raw_json" / "current_match.json"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(payload.dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Match configuration saved: {config_path}")
        return {"status": "saved", "path": str(config_path)}
    except Exception as e:
        logger.error(f"Failed to save match config: {e}")
        raise HTTPException(status_code=500, detail="Unable to save configuration.")

# ---------------------------------------------------------------
# Existing Scout & Analytics Endpoints (preserved for compatibility)
# ---------------------------------------------------------------
@app.get("/api/v1/scout/opponent-report")
async def api_v1_scout_opponent_report(request: Request, team_name: str = "Adversar") -> Dict:
    logger.info(f"Generating opponent report for {team_name}")
    dm = DataManager()
    psy_report = psychology_brain.analyze_team(team_name)
    gaps = detect_opponent_gaps(dm)
    xga = dm.get_opponent_xga(team_name)
    prompt = (
        f"Psychology report: {psy_report.get('mental_report', '')}\n"
        f"Vulnerability index: {psy_report.get('vulnerability_index', '')}\n"
        f"Spatial gaps count: {len(gaps)} – details: {gaps}\n"
        f"Opponent expected goals against (xGA): {xga}\n"
        "Generate a concise Winning Game Plan for U Cluj, focusing on exploiting the identified weaknesses."
    )
    try:
        winning_plan = psychology_brain.generate_plan(prompt)
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        winning_plan = "[Gemini unavailable – fallback plan]"
    return {
        "team": team_name,
        "psychology": psy_report,
        "spatial_gaps": gaps,
        "opponent_xga": xga,
        "winning_game_plan": winning_plan,
    }

@app.get("/api/v1/scout/live-gaps")
async def api_v1_scout_live_gaps(request: Request) -> List[Dict]:
    dm = DataManager()
    gaps = detect_opponent_gaps(dm)
    logger.info(f"Live gaps returned: {len(gaps)} zones")
    return gaps

# ---------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
