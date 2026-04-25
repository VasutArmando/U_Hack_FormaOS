import logging
from typing import List, Dict, Tuple
from fastapi import APIRouter, Request

from data_manager import DataManager

# -------------------------------------------------------------
# Tactical Engine – Corner & Weak‑Link Analysis
# -------------------------------------------------------------

logger = logging.getLogger('tactics_engine')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)

router = APIRouter()

# ---------------------------------------------------------------------
# Helper geometry utilities (same grid as DataManager – normalized 0‑100)
# ---------------------------------------------------------------------
def _midpoint(p1: Dict, p2: Dict) -> List[float]:
    """Mid‑point in normalized coordinates (0‑100)."""
    return [(p1["x"] + p2["x"]) / 2.0, (p1["y"] + p2["y"]) / 2.0]

# ---------------------------------------------------------------------
# 1️⃣ Defensive Corner Analysis
# ---------------------------------------------------------------------

def analyze_defensive_corner(dm: DataManager) -> Dict:
    """Scan the latest frame for the opponent defensive block during a corner.
    * Defensive box – our half of the pitch (x <= 33.5 on the 0‑100 grid).
    * 5+1 system – expect exactly five defenders inside the box and at most
      one free player (the 6th man) outside ready to recover.
    Returns a dict with counts, a flag for missing 6th man, and any empty
    zones in front of the goal (x between 45‑55, y < 30).
    """
    last_positions = dm.get_last_frame()
    defenders = []
    outsiders = []
    for pid, pos in last_positions.items():
        # Heuristic: treat any player with a defensive role as defender.
        player = dm.players.get(pid)
        if player and player.is_defender:
            if pos["x"] <= 33.5:
                defenders.append({"id": pid, "x": pos["x"], "y": pos["y"]})
            else:
                outsiders.append({"id": pid, "x": pos["x"], "y": pos["y"]})
    # Determine if the 6th man (free player) is present
    missing_6th = len(outsiders) == 0
    # Detect empty zones directly in front of the goal (central corridor)
    empty_front_zones = []
    for d in defenders:
        if 45 <= d["x"] <= 55 and d["y"] < 30:
            empty_front_zones.append(d)
    return {
        "defensive_players": len(defenders),
        "outside_players": len(outsiders),
        "missing_6th_man": missing_6th,
        "empty_front_zones": empty_front_zones,
    }

# ---------------------------------------------------------------------
# 2️⃣ Weak‑Link Identification (shortest central defender)
# ---------------------------------------------------------------------

def identify_weakest_central_defender(dm: DataManager) -> Dict:
    """Find the lowest‑standing central defender in the opponent block.
    Uses the 'y' coordinate (distance from own goal line) as a proxy for
    height – smaller y indicates a shorter player positioned deeper.
    Returns player details and a recommendation to target aerial balls.
    """
    central_defenders = [p for p in dm.players.values() if p.is_defender and ("central" in (p.role or "").lower() or "cb" in (p.role or "").lower())]
    if not central_defenders:
        return {"player_id": None, "player_name": None, "y": None, "recommendation": "No central defender data available."}
    shortest = min(central_defenders, key=lambda p: p.y)
    return {
        "player_id": shortest.id,
        "player_name": shortest.name,
        "y": round(shortest.y, 2),
        "recommendation": f"Target aerial balls towards {shortest.name} (shortest central defender).",
    }

# ---------------------------------------------------------------------
# 3️⃣ Predictive Corner Zone Recommendation
# ---------------------------------------------------------------------

def suggest_corner_attack_zone(dm: DataManager) -> Dict:
    """Based on opponent density, suggest the optimal corner attack zone.
    Zones are defined on the normalized x‑axis:
        * Bara 1 – left wing (0‑33.3)
        * Central – middle (33.3‑66.6)
        * Bara 2 – right wing (66.6‑100)
    The zone with the fewest opponent players is returned.
    """
    # Count opponents per zone using the latest positions
    zone_counts = {"Bara1": 0, "Central": 0, "Bara2": 0}
    for pid, pos in dm.get_last_frame().items():
        player = dm.players.get(pid)
        if not player or not player.is_defender:
            continue
        x = pos["x"]
        if x < 33.3:
            zone_counts["Bara1"] += 1
        elif x < 66.6:
            zone_counts["Central"] += 1
        else:
            zone_counts["Bara2"] += 1
    # Pick the zone with minimal density
    best_zone = min(zone_counts, key=zone_counts.get)
    return {
        "zone_counts": zone_counts,
        "recommended_zone": best_zone,
        "recommendation": f"Attack the corner from {best_zone} – lowest opponent density.",
    }

# ---------------------------------------------------------------------
# API endpoints – expose the three analyses
# ---------------------------------------------------------------------
@router.get("/api/v1/tactics/corner-defensive")
def get_corner_defensive(request: Request, team_name: str = "Adversar") -> Dict:
    dm = DataManager()
    return analyze_defensive_corner(dm)

@router.get("/api/v1/tactics/weak-link")
def get_weak_link(request: Request, team_name: str = "Adversar") -> Dict:
    dm = DataManager()
    return identify_weakest_central_defender(dm)

@router.get("/api/v1/tactics/corner-recommendation")
def get_corner_recommendation(request: Request, team_name: str = "Adversar") -> Dict:
    dm = DataManager()
    return suggest_corner_attack_zone(dm)
