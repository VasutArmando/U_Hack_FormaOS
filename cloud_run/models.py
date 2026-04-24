from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

# --- ENUMS ---

class AlertType(str, Enum):
    GAP = "GAP"
    INJURY_RISK = "INJURY_RISK"
    BIOMECHANICAL = "BIOMECHANICAL"
    TACTICAL = "TACTICAL"

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# --- FIRESTORE COLLECTIONS MODELS (Secțiunea VII) ---

class Player(BaseModel):
    """Schema for players/{player_id} collection"""
    name: str
    number: int
    position: str
    age: int
    minutes_last_3_matches: int
    sprint_speed_baseline: float
    sprint_speed_current: float
    high_intensity_events: int
    sleep_quality_score: int
    subjective_fatigue: int
    days_since_last_injury: int
    injury_risk_pct: float
    fatigue_pct: float
    biomechanical_deviation_deg: float

class MatchState(BaseModel):
    """Schema for matches/current_match collection"""
    home_score: int
    away_score: int
    minute: int
    possession_pct: float
    home_positions: List[List[float]]
    away_positions: List[List[float]]

class Alert(BaseModel):
    """Schema for alerts/{auto_id} collection"""
    type: AlertType
    severity: AlertSeverity
    player: str
    message: str
    minute: int
    timestamp: Optional[datetime] = None  # Using None to allow firestore.SERVER_TIMESTAMP at write time
    acknowledged: bool

# --- FASTAPI MODELS (Secțiunea VI) ---

class MatchContext(BaseModel):
    """Main MatchContext class for the /analyze endpoint"""
    oracle_data: Dict[str, Any]
    xray_data: Dict[str, Any]
    shield_data: Dict[str, Any]
    match_state: Dict[str, Any]
    coach_question: str = ""
