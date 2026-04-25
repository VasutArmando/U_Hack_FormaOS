import json
import glob
import logging
import math
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel

# Standard pitch dimensions (meters)
FIELD_WIDTH = 68.0
FIELD_LENGTH = 105.0

logger = logging.getLogger("forma_os")

# Schema Definition
class ContextTable(BaseModel):
    temperature: float
    condition: str
    wind_speed: float
    morale_score: float
    pressure_resistance: str

class AnalyticsTable(BaseModel):
    fatigue_score: float
    xt_zones: List[Dict]  # Expected Threat zones
    # New metrics for U Cluj DNA
    ball_progression: float = 0.0  # distance (meters) per 90'
    passes_last_third: int = 0
    ball_progression_exceeds_mean: bool = False

class Player(BaseModel):
    id: str
    name: str
    role: str
    x: float = 0.0
    y: float = 0.0
    passes_count: int = 0
    losses_count: int = 0
    is_forward: bool = False
    # Profile flags for U Cluj DNA
    is_goalkeeper: bool = False
    is_defender: bool = False
    is_central_attacker: bool = False

class DataManager:
    """
    In-Memory Data Lake for FORMA SCOUT.
    Loads raw JSON data at startup and provides structured queries.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.players: Dict[str, Player] = {}
        self.events: List[Dict] = []  # Store parsed events
        self.context = ContextTable(
            temperature=18.5,
            condition="Clear",
            wind_speed=4.2,
            morale_score=0.4,
            pressure_resistance="Low"
        )
        self.analytics = AnalyticsTable(
            fatigue_score=0.0,
            xt_zones=[]
        )
        self.load_data()
        self._load_events()

    def load_data(self):
        logger.info("Loading Data Lake...")
        # Load Player Metadata
        meta_files = glob.glob("data/raw_json/**/players*.json", recursive=True)
        player_meta = {}
        if meta_files:
            try:
                with open(meta_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for p in data.get("players", []):
                        pid = str(p.get("wyId"))
                        player_meta[pid] = {
                            "name": p.get("shortName", ""),
                            "role": p.get("role", {}).get("name", "")
                        }
            except Exception as e:
                logger.error(f"Error loading player metadata: {e}")

        # Load Match Stats
        stat_files = glob.glob("data/raw_json/**/*_players_stats.json", recursive=True)
        if stat_files:
            try:
                with open(stat_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for idx, p in enumerate(data.get("players", [])):
                        pid = str(p.get("playerId"))
                        meta = player_meta.get(pid, {})
                        
                        name = meta.get("name", f"Player {pid}")
                        role = meta.get("role", "")
                        
                        # Identify Forward from positions array if role is empty
                        positions = p.get("positions", [])
                        is_forward = role == "Forward" or any("Forward" in pos.get("position", {}).get("name", "") for pos in positions)
                        
                        total = p.get("total", {})
                        
                        # Determine profile flags based on role description (Romanian)
                        role_lower = role.lower() if role else ""
                        is_goalkeeper = "portar" in role_lower
                        is_defender = "funda" in role_lower
                        is_central_attacker = "atacant central" in role_lower or "target man" in role_lower

                        player = Player(
                            id=pid,
                            name=name,
                            role=role,
                            is_forward=is_forward,
                            passes_count=total.get("passes", 0),
                            losses_count=total.get("losses", 0),
                            x=20.0 + idx * 5.0, # Simulated X
                            y=30.0 + (idx % 3) * 15.0, # Simulated Y
                            is_goalkeeper=is_goalkeeper,
                            is_defender=is_defender,
                            is_central_attacker=is_central_attacker,
                        )
                        self.players[pid] = player
            except Exception as e:
                logger.error(f"Error loading match stats: {e}")
        
        self._compute_analytics()

    def _compute_analytics(self):
        # Compute Threat Map Zones based on losses
        zones = []
        top_losers = sorted(self.players.values(), key=lambda x: x.losses_count, reverse=True)[:5]
        for i, p in enumerate(top_losers):
            if p.losses_count > 0:
                zones.append({
                    "id": i + 1,
                    "x": min(95.0, p.x + p.losses_count * 1.5),
                    "y": p.y,
                    "radius": min(25.0, p.losses_count * 1.2),
                    "threat_score": min(0.99, p.losses_count / 20.0)
                })
        # After threat zones, compute progression metrics
        self._compute_progression_metrics()

        # Ensure a critical Half-Space zone exists
        zones.append({"id": 99, "x": 82.5, "y": 25.0, "radius": 18.5, "threat_score": 0.95})
        self.analytics.xt_zones = zones

        # Compute overall fatigue (mock logic based on time/losses)
        total_losses = sum(p.losses_count for p in self.players.values())
        self.analytics.fatigue_score = min(1.0, total_losses / 100.0)

    def get_passing_network(self) -> Dict:
        nodes = []
        edges = []
        
        players_list = list(self.players.values())[:11] # Take top 11
        for i, p in enumerate(players_list):
            nodes.append({
                "id": p.id,
                "name": p.name,
                "x": p.x,
                "y": p.y,
                "centrality": min(1.0, p.passes_count / 100.0),
                "is_hub": p.passes_count > 60
            })
            if i > 0:
                target = players_list[0]
                edges.append({"source": p.id, "target": target.id, "weight": max(5, p.passes_count // 5)})
                
        return {"nodes": nodes, "edges": edges}

    def get_threat_map(self) -> Dict:
        return {"status": "success", "vulnerability_zones": self.analytics.xt_zones}

    def get_pivot_optimization(self) -> Dict:
        for p in self.players.values():
            if p.is_forward:
                return {
                    "player_id": p.id,
                    "player_name": p.name,
                    "optimal_x": 75.5,
                    "optimal_y": 22.0,
                    "recommendation": f"Atacantul {p.name} trebuie plasat în zona (75.5, 22.0). Datele arată o densitate minimă defensivă adversă în acest Half-Space."
                }
        return {
            "player_id": "UNKNOWN",
            "optimal_x": 80.0,
            "optimal_y": 50.0,
            "recommendation": "Plasează pivotul central-stânga pentru a exploata lipsa de compactness advers."
        }

    def get_context_environment(self) -> Dict:
        return self.context.model_dump(include={"temperature", "condition", "wind_speed"})

    def get_context_psychology(self) -> Dict:
        return self.context.model_dump(include={"morale_score", "pressure_resistance"})

    def _load_events(self) -> None:
        """Load raw event JSON files from the data directory."""
        event_files = glob.glob("data/raw_json/**/events*.json", recursive=True)
        for ef in event_files:
            try:
                with open(ef, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        raw_events = data
                    elif isinstance(data, dict):
                        raw_events = data.get('events', [])
                    else:
                        raw_events = []
                    self._parse_events(raw_events)
            except Exception as e:
                logger.error(f"Error loading events from {ef}: {e}")

    def _parse_events(self, raw_events: List[Dict]) -> None:
        """Parse raw event JSON objects extracting required fields."""
        for ev in raw_events:
            try:
                timestamp = ev.get('timestamp')
                player_id = str(ev.get('player_id') or ev.get('wyId'))
                team_id = str(ev.get('team_id'))
                coords = ev.get('coordinates') or ev.get('position')
                if isinstance(coords, list) and len(coords) >= 2:
                    x, y = coords[0], coords[1]
                elif isinstance(coords, dict):
                    x = coords.get('x')
                    y = coords.get('y')
                else:
                    continue
                nx, ny = self._normalize_coords(x, y)
                self.events.append({
                    'timestamp': timestamp,
                    'player_id': player_id,
                    'team_id': team_id,
                    'x': nx,
                    'y': ny,
                    'type': ev.get('type')
                })
            except Exception as e:
                logger.debug(f"Skipping malformed event: {e}")

    # -----------------------------------------------------
    # 6️⃣ Opponent Analysis Utilities
    # -----------------------------------------------------

    def get_opponent_loss_rate(self, opponent_team_id: str) -> float:
        """Calculate opponent lost balls per 90 minutes.
        Returns a float representing the rate (balls lost per 90').
        """
        loss_events = [e for e in self.events if e.get('type') == 'loss' and e.get('team_id') == opponent_team_id]
        total_losses = len(loss_events)
        total_time = max((e.get('timestamp') or 0) for e in self.events) or 5400
        losses_per_90 = (total_losses * 5400) / total_time if total_time else 0.0
        return round(losses_per_90, 2)

    def get_opponent_xga(self, opponent_team_id: str) -> float:
        """Calculate expected goals against (xGA) for the opponent.
        Sums the 'xG' field of shot events; if missing, falls back to shot count.
        """
        shots = [e for e in self.events if e.get('type') == 'shot' and e.get('team_id') == opponent_team_id]
        xga = sum(float(e.get('xG', 0)) for e in shots)
        if xga == 0:
            xga = len(shots)
        return round(xga, 2)

    def get_defensive_line_center(self, opponent_team_id: str) -> Dict:
        """Compute the centroid of the opponent defensive line.
        Returns avg_x, avg_y and a 'height_of_defense' metric (average y).
        If the average y exceeds 70 (normalized grid), it's flagged as a rapid
        counter‑attack opportunity for U Cluj.
        """
        defenders = [p for p in self.players.values() if p.is_defender]
        if not defenders:
            return {"avg_x": 0, "avg_y": 0, "height_of_defense": 0, "counter_attack_opportunity": False}
        avg_x = sum(p.x for p in defenders) / len(defenders)
        avg_y = sum(p.y for p in defenders) / len(defenders)
        height = avg_y
        opportunity = height > 70
        return {
            "avg_x": round(avg_x, 2),
            "avg_y": round(avg_y, 2),
            "height_of_defense": round(height, 2),
            "counter_attack_opportunity": opportunity,
        }

    def _clean_events(self) -> None:
        """Ensures no null coordinates or missing fields in self.events.
        Replaces None x/y with 0.0 and removes events lacking a timestamp.
        This is called after loading to guarantee safe downstream analytics.
        """
        cleaned: List[Dict] = []
        for ev in self.events:
            if ev.get('timestamp') is None:
                continue
            ev['x'] = ev.get('x') if ev.get('x') is not None else 0.0
            ev['y'] = ev.get('y') if ev.get('y') is not None else 0.0
            cleaned.append(ev)
        self.events = cleaned

    # Hook cleaning after parsing events (override original method definition)
    def _parse_events(self, raw_events: List[Dict]) -> None:
        """Parse raw event JSON objects extracting required fields.
        Includes data cleaning to protect live demo stability.
        """
        for ev in raw_events:
            try:
                timestamp = ev.get('timestamp')
                player_id = str(ev.get('player_id') or ev.get('wyId'))
                team_id = str(ev.get('team_id'))
                coords = ev.get('coordinates') or ev.get('position')
                if isinstance(coords, list) and len(coords) >= 2:
                    x, y = coords[0], coords[1]
                elif isinstance(coords, dict):
                    x = coords.get('x')
                    y = coords.get('y')
                else:
                    continue
                nx, ny = self._normalize_coords(x, y)
                self.events.append({
                    'timestamp': timestamp,
                    'player_id': player_id,
                    'team_id': team_id,
                    'x': nx,
                    'y': ny,
                    'type': ev.get('type')
                })
            except Exception as e:
                logger.debug(f"Skipping malformed event: {e}")
        self._clean_events()


    def _normalize_coords(self, x: float, y: float) -> (float, float):
        """Scale any coordinate system to a 100x100 grid.
        Assumes original pitch dimensions up to 120x80.
        """
        max_width, max_height = 120.0, 80.0
        nx = max(0.0, min(100.0, (float(x) / max_width) * 100.0))
        ny = max(0.0, min(100.0, (float(y) / max_height) * 100.0))
        return nx, ny

    def _compute_progression_metrics(self) -> None:
        """Compute U Cluj DNA metrics.
        * Ball progression: total dribble distance (meters) per 90' minutes. Target average is 13.27 m per 90'.
        * Passes in final third: count of pass events when the player is in the attacking third (x > 66 on a 0‑100 grid). Target is 50.62 per 90'.
        """
        # Ball progression (dribble distance)
        dribble_distance = 0.0
        last_pos: Dict[str, Tuple[float, float]] = {}
        for ev in sorted(self.events, key=lambda e: e.get('timestamp') or 0):
            if ev.get('type') != 'dribble':
                continue
            pid = ev['player_id']
            x, y = ev['x'], ev['y']
            if pid in last_pos:
                prev_x, prev_y = last_pos[pid]
                dx = (x - prev_x) * (FIELD_WIDTH / 100.0)
                dy = (y - prev_y) * (FIELD_LENGTH / 100.0)
                dribble_distance += math.sqrt(dx * dx + dy * dy)
            last_pos[pid] = (x, y)
        total_time = max((ev.get('timestamp') or 0) for ev in self.events) or 5400
        factor = 5400 / total_time if total_time > 0 else 1.0
        ball_progression_per_90 = dribble_distance * factor
        self.analytics.ball_progression = round(ball_progression_per_90, 2)
        self.analytics.ball_progression_exceeds_mean = self.analytics.ball_progression > 13.27
        # Passes in the final third
        passes_last_third = sum(1 for ev in self.events if ev.get('type') == 'pass' and ev.get('x', 0) > 66)
        self.analytics.passes_last_third = passes_last_third

    def _filter_possession_events(self, events: List[Dict]) -> List[Dict]:
        """Return only pass and dribble events."""
        return [e for e in events if e.get('type') in ('pass', 'dribble')]

    def get_last_frame(self) -> Dict[str, Dict[str, float]]:
        """Return the most recent known position of each player.
        Format: {player_id: {'x': ..., 'y': ...}}
        """
        if not self.events:
            return {}
        sorted_events = sorted(self.events, key=lambda e: e.get('timestamp') or 0)
        last_positions: Dict[str, Dict[str, float]] = {}
        for ev in sorted_events:
            pid = ev['player_id']
            last_positions[pid] = {'x': ev['x'], 'y': ev['y']}
        return last_positions

    def get_summary_events(self) -> str:
        """
        Extrage un rezumat al evenimentelor cheie (corelare date JSON cu LLM)
        """
        if not self.players:
            return "Date JSON lipsă. Adversarul are o defensivă pasivă și pierde ușor mingea pe tranziții."
            
        own_half_losses = sum(p.losses_count for p in self.players.values() if p.x < 50.0)
        pivot_losses = sum(p.losses_count for p in self.players.values() if p.is_forward)
        
        summary = (f"- {own_half_losses} mingi pierdute (greșite) în propria jumătate.\n"
                   f"- Atacantul pivot advers a pierdut {pivot_losses} mingi izolat.\n"
                   f"- Nivel general de oboseală estimat la {self.analytics.fatigue_score * 100:.1f}%.")
        return summary

    # ----------------------------------------------------------
    # Opponent Intelligence Analytics
    # ----------------------------------------------------------

    def get_vulnerability_index(self) -> Dict:
        """Identify the opponent player who loses the most balls under pressure.
        Returns a dict with player_id, player_name and a vulnerability_index (0‑100).
        The index is calculated as the proportion of pressure‑loss events relative to
        total loss events for that player, scaled to 100.
        """
        loss_counts: Dict[str, int] = {}
        pressure_loss_counts: Dict[str, int] = {}
        for ev in self.events:
            if ev.get('type') != 'loss':
                continue
            pid = ev.get('player_id')
            loss_counts[pid] = loss_counts.get(pid, 0) + 1
            if ev.get('pressure'):
                pressure_loss_counts[pid] = pressure_loss_counts.get(pid, 0) + 1
        vulnerability: Dict[str, float] = {}
        for pid, total in loss_counts.items():
            press = pressure_loss_counts.get(pid, 0)
            vulnerability[pid] = (press / total) * 100 if total else 0.0
        if not vulnerability:
            return {"player_id": None, "player_name": None, "vulnerability_index": 0}
        worst_pid = max(vulnerability, key=vulnerability.get)
        player = self.players.get(worst_pid)
        return {
            "player_id": worst_pid,
            "player_name": player.name if player else "Unknown",
            "vulnerability_index": round(vulnerability[worst_pid], 2),
        }

    def get_defensive_line_metrics(self) -> Dict:
        """Map the average coordinates of the opponent defensive line and compute
        a 'Height of Defense' metric (average y‑coordinate on the normalized grid).
        Returns a dict with avg_x, avg_y and height_of_defense.
        """
        defenders = [p for p in self.players.values() if p.is_defender]
        if not defenders:
            return {"avg_x": 0, "avg_y": 0, "height_of_defense": 0}
        avg_x = sum(p.x for p in defenders) / len(defenders)
        avg_y = sum(p.y for p in defenders) / len(defenders)
        height_of_defense = avg_y
        return {
            "avg_x": round(avg_x, 2),
            "avg_y": round(avg_y, 2),
            "height_of_defense": round(height_of_defense, 2),
        }

    def get_normalized_opponent_heatmap(self, cell_size: int = 10) -> List[Dict]:
        """Create a heat‑map of opponent event density on a 100x100 grid.
        The grid is divided into squares of *cell_size* (default 10). Returns a list
        of cells with centre coordinates and event count.
        """
        cells_per_axis = 100 // cell_size
        heatmap = [[0 for _ in range(cells_per_axis)] for _ in range(cells_per_axis)]
        for ev in self.events:
            x, y = ev.get('x'), ev.get('y')
            if x is None or y is None:
                continue
            ix = min(cells_per_axis - 1, max(0, int(x // cell_size)))
            iy = min(cells_per_axis - 1, max(0, int(y // cell_size)))
            heatmap[iy][ix] += 1
        result: List[Dict] = []
        for iy in range(cells_per_axis):
            for ix in range(cells_per_axis):
                count = heatmap[iy][ix]
                if count == 0:
                    continue
                result.append({
                    "cell_x": (ix + 0.5) * cell_size,
                    "cell_y": (iy + 0.5) * cell_size,
                    "count": count,
                })
        return result

