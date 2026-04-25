"""Spatial analytics for interstice detection.

This module focuses on identifying exploitable gaps (interstices) between the opponent's
lateral defender (FB) and central defender (CB). When a gap exceeds a configurable
threshold, the system recommends a deep‑space attack and, if the team's central attacker
is positioned as a pivot, suggests a pass to him.

The logic re‑uses the same normalisation as :pymod:`cloud_run.spatial_analytics` –
player coordinates are stored on a 0‑100 grid, which we map back to real‑world meters
using the standard pitch dimensions.
"""

import math
from typing import List, Dict

from data_manager import DataManager

# ------------------------------------------------------------
# Pitch dimensions (meters) – must match spatial_analytics constants
# ------------------------------------------------------------
FIELD_WIDTH = 68.0   # typical football pitch width
FIELD_LENGTH = 105.0  # typical football pitch length

# Interstice detection threshold (meters)
INTERSTICE_THRESHOLD = 15.0

# ------------------------------------------------------------
# Helper geometry utilities
# ------------------------------------------------------------
def _euclidean_distance(p1: Dict, p2: Dict) -> float:
    """Return Euclidean distance in metres between two players.

    ``p1`` and ``p2`` are dictionaries containing the normalised ``x`` and ``y``
    coordinates (0‑100). The conversion mirrors the one used in
    :pymod:`cloud_run.spatial_analytics`.
    """
    x1 = p1["x"] * (FIELD_WIDTH / 100.0)
    y1 = p1["y"] * (FIELD_LENGTH / 100.0)
    x2 = p2["x"] * (FIELD_WIDTH / 100.0)
    y2 = p2["y"] * (FIELD_LENGTH / 100.0)
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# ------------------------------------------------------------
# Core algorithm
# ------------------------------------------------------------
def detect_interstices(dm: DataManager) -> List[Dict]:
    """Detect exploitable interstices and generate tactical recommendations.

    The function performs three steps:
        1. Collect opponent defenders and split them into *lateral* (FB) and *central* (CB).
        2. For each lateral‑central pair compute the Euclidean distance. When the distance
           exceeds :data:`INTERSTICE_THRESHOLD` an ``interstice`` record is created.
        3. If the team's central attacker (flag ``is_central_attacker`` from the DNA mapping)
           is present and currently acting as a pivot (i.e. he has a recent ``dribble``
           event), the recommendation also includes a pass suggestion to that attacker.

    Returns a list of dictionaries, each containing:
        * ``lateral_id`` / ``lateral_name`` – the opponent FB.
        * ``central_id`` / ``central_name`` – the opponent CB.
        * ``distance_m`` – gap size in metres.
        * ``recommendation`` – tactical hint for deep‑space attack.
        * ``pivot_suggestion`` (optional) – pass to our central attacker.
    """
    # -----------------------------------------------------------------
    # 1. Gather opponent defenders – simple role heuristic
    # -----------------------------------------------------------------
    opponents = []
    for player in dm.players.values():
        role = (player.role or "").lower()
        if "funda" in role:  # matches fundaș, fundaș central, etc.
            opponents.append({
                "id": player.id,
                "name": player.name,
                "role": role,
                "x": player.x,
                "y": player.y,
                "is_central": "central" in role,
                "is_lateral": "lateral" in role or "left" in role or "right" in role,
            })

    lateral_defs = [p for p in opponents if p["is_lateral"]]
    central_defs = [p for p in opponents if p["is_central"]]

    if not lateral_defs or not central_defs:
        # No meaningful gap can be evaluated.
        return []

    # -----------------------------------------------------------------
    # 2. Find the nearest central defender for each lateral defender
    # -----------------------------------------------------------------
    recommendations: List[Dict] = []
    for lat in lateral_defs:
        # Identify the closest central defender (simple nearest‑neighbor)
        nearest_central = min(
            central_defs,
            key=lambda cen: _euclidean_distance(lat, cen),
        )
        dist = _euclidean_distance(lat, nearest_central)
        if dist <= INTERSTICE_THRESHOLD:
            # Gap not large enough – skip.
            continue

        rec: Dict = {
            "lateral_id": lat["id"],
            "lateral_name": lat["name"],
            "central_id": nearest_central["id"],
            "central_name": nearest_central["name"],
            "distance_m": round(dist, 1),
            "recommendation": "Attack deep space through the detected interstice",
        }

        # -----------------------------------------------------------------
        # 3. Correlate with our central attacker (pivot logic)
        # -----------------------------------------------------------------
        central_attacker = next(
            (p for p in dm.players.values() if getattr(p, "is_central_attacker", False)),
            None,
        )
        if central_attacker:
            # Determine if the attacker is acting as a pivot – we look for a recent
            # dribble event involving him (within the loaded events list).
            pivot_active = any(
                ev.get("type") == "dribble" and ev.get("player_id") == central_attacker.id
                for ev in dm.events
            )
            if pivot_active:
                rec["pivot_suggestion"] = {
                    "target_player_id": central_attacker.id,
                    "target_player_name": central_attacker.name,
                    "action": "Pass to central attacker to hold the ball",
                }

        recommendations.append(rec)

    return recommendations
