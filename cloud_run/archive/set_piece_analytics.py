import math
from typing import List, Dict
from data_manager import DataManager

# Simple pitch constants (normalized 0-100 grid)
BOX_X_MAX = 20          # Own defensive box (left side)
BOX_Y_MIN = 30
BOX_Y_MAX = 70
FINISH_X_MIN = 80       # Opponent's finishing zone (right side)
FINISH_Y_MIN = 30
FINISH_Y_MAX = 70

# Offensive critical zones (normalized)
ZONE_BAR_1 = {'name': 'Bar 1', 'x_range': (0, 10), 'y_range': (30, 70)}
ZONE_CENTRAL = {'name': 'Central', 'x_range': (45, 55), 'y_range': (30, 70)}
ZONE_BAR_2 = {'name': 'Bar 2', 'x_range': (90, 100), 'y_range': (30, 70)}
CRITICAL_ZONES = [ZONE_BAR_1, ZONE_CENTRAL, ZONE_BAR_2]

class SetPieceAnalyzer:
    """Analyzes corner set‑pieces (defensive & offensive) using the in‑memory DataManager.

    The logic is intentionally lightweight – it works on the normalized 0‑100 grid
    already stored by ``DataManager`` and on the parsed event list.
    """

    def __init__(self, dm: DataManager | None = None):
        self.dm = dm or DataManager()

    # ---------------------------------------------------------------------
    # Defensive corner (5+1 system)
    # ---------------------------------------------------------------------
    def _players_in_defensive_box(self) -> List[Dict]:
        """Return a list of player dicts whose (x, y) lie inside the defensive box."""
        players = []
        for p in self.dm.players.values():
            if p.x <= BOX_X_MAX and BOX_Y_MIN <= p.y <= BOX_Y_MAX:
                players.append({"id": p.id, "x": p.x, "y": p.y, "role": p.role})
        return players

    def _central_corridor_closed(self) -> bool:
        """Check whether any defender occupies the central corridor (x 30‑40, y 45‑55)."""
        for p in self.dm.players.values():
            if p.x >= 30 and p.x <= 40 and p.y >= 45 and p.y <= 55:
                # Assume a defender if not a forward‑type attacker
                if not p.is_forward:
                    return True
        return False

    def defensive_corner_status(self) -> Dict:
        """Analyse the 5+1 defensive corner system.

        Returns a dict with:
            players_in_box – list of the defending players inside the box
            free_spaces    – count of empty slots (6 – occupied)
            corridor_closed – bool indicating central corridor blockage
            alert          – optional string when the system deviates from 5+1
        """
        box_players = self._players_in_defensive_box()
        occupied = len(box_players)
        free_spaces = max(0, 6 - occupied)
        corridor_closed = self._central_corridor_closed()

        result = {
            "players_in_box": box_players,
            "occupied": occupied,
            "free_spaces": free_spaces,
            "corridor_closed": corridor_closed,
        }
        if occupied < 5 or free_spaces < 1:
            result["alert"] = "Defensive corner deviates from 5+1 system"
        return result

    # ---------------------------------------------------------------------
    # Offensive corner – analyse crosses
    # ---------------------------------------------------------------------
    def _categorise_cross(self, x: float, y: float) -> str | None:
        """Return the name of the critical zone a cross lands in, or None."""
        for zone in CRITICAL_ZONES:
            if zone["x_range"][0] <= x <= zone["x_range"][1] and zone["y_range"][0] <= y <= zone["y_range"][1]:
                return zone["name"]
        return None

    def offensive_corner_analysis(self) -> Dict:
        """Identify which critical zones the offensive corners target.

        Looks at events of type ``cross`` (or ``corner``) and extracts the
        ``position`` coordinates. Returns a dict containing the list of zones
        hit and an optional alert if no critical zone is targeted.
        """
        targeted_zones: List[str] = []
        for ev in self.dm.events:
            ev_type = ev.get("type", "").lower()
            if ev_type in ("cross", "corner"):
                pos = ev.get("position") or ev.get("coordinates")
                if isinstance(pos, list) and len(pos) >= 2:
                    x, y = pos[0], pos[1]
                elif isinstance(pos, dict):
                    x, y = pos.get("x"), pos.get("y")
                else:
                    continue
                zone_name = self._categorise_cross(x, y)
                if zone_name:
                    targeted_zones.append(zone_name)
        unique_zones = list(dict.fromkeys(targeted_zones))  # preserve order
        result = {"targeted_zones": unique_zones}
        if not unique_zones:
            result["alert"] = "No offensive corner crosses hit critical zones"
        return result

    # ---------------------------------------------------------------------
    # Tactical alert – finishing players count
    # ---------------------------------------------------------------------
    def finishing_players_count(self) -> int:
        """Count attacking players (forwards/central attackers) inside the finishing area.
        """
        count = 0
        for p in self.dm.players.values():
            if (p.is_forward or getattr(p, "is_central_attacker", False)) and \
               p.x >= FINISH_X_MIN and FINISH_Y_MIN <= p.y <= FINISH_Y_MAX:
                count += 1
        return count

    def tactical_alert(self) -> str | None:
        """Generate an alert if fewer than 4 finishing players are present.
        """
        cnt = self.finishing_players_count()
        if cnt < 4:
            return f"⚠️ Tactical alert: only {cnt} player(s) in the finishing zone – below club policy (≥4)."
        return None

    # ---------------------------------------------------------------------
    # Public entry point used by API
    # ---------------------------------------------------------------------
    def analyse_set_pieces(self) -> Dict:
        """Aggregate all set‑piece analyses into a single payload.
        """
        defensive = self.defensive_corner_status()
        offensive = self.offensive_corner_analysis()
        alert = self.tactical_alert()
        if alert:
            defensive["alert"] = alert  # merge into defensive payload for simplicity
        return {
            "defensive_corner": defensive,
            "offensive_corner": offensive,
        }
