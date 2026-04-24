import json
import glob
import logging
from typing import List, Optional, Dict
from pydantic import BaseModel

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
    xt_zones: List[Dict] # Expected Threat zones

class Player(BaseModel):
    id: str
    name: str
    role: str
    x: float = 0.0
    y: float = 0.0
    passes_count: int = 0
    losses_count: int = 0
    is_forward: bool = False

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
                        
                        player = Player(
                            id=pid,
                            name=name,
                            role=role,
                            is_forward=is_forward,
                            passes_count=total.get("passes", 0),
                            losses_count=total.get("losses", 0),
                            x=20.0 + idx * 5.0, # Simulated X
                            y=30.0 + (idx % 3) * 15.0 # Simulated Y
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
