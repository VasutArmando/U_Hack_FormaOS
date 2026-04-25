import math
import logging
from typing import List, Dict, Tuple
from fastapi import APIRouter, Request

from data_manager import DataManager

# Configure logger
logger = logging.getLogger('spatial_analytics')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)

# Standard pitch dimensions (meters)
FIELD_WIDTH = 68.0   # width of the pitch
FIELD_LENGTH = 105.0  # length of the pitch

router = APIRouter()

# ---------------------------------------------------------------------
# Helper geometry utilities – work on normalized 0‑100 grid
# ---------------------------------------------------------------------
def _euclidean_distance(p1: Dict, p2: Dict) -> float:
    """Return Euclidean distance in real meters between two points expressed
    on the normalized 0‑100 grid.
    """
    x1 = p1["x"] * (FIELD_WIDTH / 100.0)
    y1 = p1["y"] * (FIELD_LENGTH / 100.0)
    x2 = p2["x"] * (FIELD_WIDTH / 100.0)
    y2 = p2["y"] * (FIELD_LENGTH / 100.0)
    return math.hypot(x2 - x1, y2 - y1)

def _midpoint(p1: Dict, p2: Dict) -> List[float]:
    """Mid‑point in normalized coordinates (0‑100)."""
    return [(p1["x"] + p2["x"]) / 2.0, (p1["y"] + p2["y"]) / 2.0]

# ---------------------------------------------------------------------
# 1️⃣ Opponent Gap Detection (FB vs CB > 15 m)
# ---------------------------------------------------------------------
def _collect_defenders(dm: DataManager) -> List[Dict]:
    """Gather opponent defenders and annotate whether they are central (CB)
    or lateral (FB) based on role strings.
    Returns a list of dicts with id, name, role, x, y, is_central, is_lateral.
    """
    defenders = []
    for player in dm.players.values():
        role = (player.role or "").lower()
        # Simple heuristics – you can extend with more patterns if needed
        is_central = "central" in role or "cb" in role
        is_lateral = "lateral" in role or "fb" in role or "left" in role or "right" in role
        if "funda" in role:  # generic defender keyword (Romanian)
            defenders.append({
                "id": player.id,
                "name": player.name,
                "role": role,
                "x": player.x,
                "y": player.y,
                "is_central": is_central,
                "is_lateral": is_lateral,
            })
    return defenders

def detect_opponent_gaps(dm: DataManager) -> List[Dict]:
    """Identify vulnerable zones where a lateral defender (FB) is far
    (>15 m) from a central defender (CB). Returns a list of dictionaries
    containing player IDs, names, the distance and the midpoint which
    represents the exploitable space.
    """
    defenders = _collect_defenders(dm)
    central = [d for d in defenders if d["is_central"]]
    lateral = [d for d in defenders if d["is_lateral"]]
    zones: List[Dict] = []
    threshold = 15.0  # metres
    for cb in central:
        for fb in lateral:
            dist = _euclidean_distance(cb, fb)
            if dist > threshold:
                zones.append({
                    "central_id": cb["id"],
                    "central_name": cb["name"],
                    "lateral_id": fb["id"],
                    "lateral_name": fb["name"],
                    "distance_m": round(dist, 1),
                    "midpoint": _midpoint(cb, fb),
                })
    return zones

# ---------------------------------------------------------------------
# 2️⃣ Target Man Deep‑Pass Evaluation (Lukic)
# ---------------------------------------------------------------------
def evaluate_target_man_deep_passes(dm: DataManager) -> Dict:
    """Assess whether our central attacker (Lukic) enjoys a deep‑pass corridor.
    We count passes made by Lukic that land inside the attacking third
    (normalized x > 66) and scale the count to a per‑90‑minutes rate.
    The target benchmark is 5.41 deep passes per 90'.
    """
    # Find Lukic – case‑insensitive search in the player name
    lukic = next((p for p in dm.players.values() if "lukic" in p.name.lower()), None)
    if not lukic:
        logger.warning("Lukic not found in player roster – returning empty evaluation.")
        return {
            "player_id": None,
            "player_name": None,
            "deep_passes_per_90": 0.0,
            "meets_target": False,
        }
    # Count pass events for Lukic that end in the attacking third
    deep_passes = sum(
        1
        for ev in dm.events
        if ev.get("type") == "pass"
        and ev.get("player_id") == lukic.id
        and ev.get("x", 0) > 66
    )
    # Normalise to a 90‑minute window (5400 seconds)
    total_time = max((e.get("timestamp") or 0) for e in dm.events) or 5400
    per_90 = (deep_passes * 5400) / total_time if total_time else 0.0
    per_90 = round(per_90, 2)
    return {
        "player_id": lukic.id,
        "player_name": lukic.name,
        "deep_passes_per_90": per_90,
        "meets_target": per_90 >= 5.41,
    }

# ---------------------------------------------------------------------
# API endpoints – expose the two new analytics
# ---------------------------------------------------------------------
@router.get("/api/v1/analytics/opponent-gaps")
def get_opponent_gaps(request: Request, team_name: str = "Adversar") -> List[Dict]:
    dm = DataManager()
    return detect_opponent_gaps(dm)

@router.get("/api/v1/analytics/target-man-deep-pass")
def get_target_man_deep_pass(request: Request, team_name: str = "Adversar") -> Dict:
    dm = DataManager()
    return evaluate_target_man_deep_passes(dm)
