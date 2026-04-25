import math
import logging
from typing import List, Dict, Tuple
from data_manager import DataManager

logger = logging.getLogger('set_piece_analyzer')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)
from typing import List, Dict, Tuple

# Constants for pitch zones (normalized 0‑100 grid)
DEFENSIVE_BOX_MAX_X = 20.0  # our defensive half left side (0‑20)
CENTRAL_ZONE_X = (45.0, 55.0)  # central corridor for goal‑line defence
COMPACTNESS_THRESHOLD = 0.12  # minimal player density (players per unit area) for a disciplined block

def _bounding_box(players: List[Dict]) -> Tuple[float, float, float, float]:
    """Return (min_x, max_x, min_y, max_y) covering all given players."""
    xs = [p["x"] for p in players]
    ys = [p["y"] for p in players]
    return min(xs), max(xs), min(ys), max(ys)

def _box_area(min_x: float, max_x: float, min_y: float, max_y: float) -> float:
    return max(0.0, (max_x - min_x)) * max(0.0, (max_y - min_y))

def _player_density(players: List[Dict]) -> float:
    """Density = number of players / bounding‑box area (in normalized units)."""
    if not players:
        return 0.0
    min_x, max_x, min_y, max_y = _bounding_box(players)
    area = _box_area(min_x, max_x, min_y, max_y)
    return len(players) / area if area > 0 else float('inf')

def analyze_defensive_corner(frame: List[Dict]) -> Dict:
    """Analyse a defensive‑corner frame.

    The *frame* argument is a list of player dictionaries – each must contain at least:
        ``{"id": str, "x": float, "y": float, "role": str}``
    Roles are free‑form strings; we look for the substrings ``"cb"`` (center‑back) and ``"st"`` (striker).

    Returns a dictionary with the following keys:
        * ``"players_in_box"`` – list of players whose ``x`` coordinate lies inside the defensive box.
        * ``"compact_block"`` – boolean indicating whether the 5+1 block is geometrically compact
          (density above ``COMPACTNESS_THRESHOLD``).
        * ``"central_defenders"`` – list of CB/ST players that occupy the central defensive corridor.
        * ``"alert"`` – optional message when the block is under‑populated or not compact.
    """
    # 1️⃣ Players inside the defensive box (our half‑field left side)
    box_players = [p for p in frame if p.get("x", 0) <= DEFENSIVE_BOX_MAX_X]

    # 2️⃣ Identify central defenders (CB or ST) inside the central corridor
    central_players = []
    for p in box_players:
        role = (p.get("role") or "").lower()
        if "cb" in role or "st" in role:
            if CENTRAL_ZONE_X[0] <= p.get("x", 0) <= CENTRAL_ZONE_X[1]:
                central_players.append(p)

    # 3️⃣ Compactness – we expect at least 5 players + 1 free slot (total 6 positions)
    occupied = len(box_players)
    free_slots = max(0, 6 - occupied)
    compact = _player_density(box_players) >= COMPACTNESS_THRESHOLD

    result: Dict = {
        "players_in_box": box_players,
        "occupied": occupied,
        "free_slots": free_slots,
        "compact_block": compact,
        "central_defenders": central_players,
    }

    if occupied < 5 or free_slots < 1:
        result["alert"] = "⚠️ Defensive corner deviates from the 5+1 system – not enough players."
    elif not compact:
        result["alert"] = "⚠️ Defensive block density below optimal – consider tightening formation."
    elif not central_players:
        result["alert"] = "⚠️ No CB/ST positioned in the central defensive corridor."

    return result
