import json
import logging
from typing import List, Dict, Any
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forma_os_unifier")

class UnifiedMatchEvent:
    """
    Modelul de date unificat care consolidează evenimentele Hudl 
    cu tracking-ul 360° Open-Source de la StatsBomb.
    """
    def __init__(self, match_id: str, timestamp: str, event_type: str, 
                 player_id: str, team_id: str, x: float, y: float, 
                 is_under_pressure: bool, tracking_360: List[Dict] = None):
        self.match_id = match_id
        self.timestamp = timestamp
        self.event_type = event_type
        self.player_id = player_id
        self.team_id = team_id
        self.x = x
        self.y = y
        self.is_under_pressure = is_under_pressure
        self.tracking_360 = tracking_360 or []

    def to_dict(self):
        return {
            "match_id": self.match_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "x": self.x,
            "y": self.y,
            "is_under_pressure": self.is_under_pressure,
            "tracking_360": json.dumps(self.tracking_360) # BigQuery STRING sau JSON
        }

class DataUnifier:
    """
    Stratul de ingestie de date la nivel de FAANG.
    """
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        # Inițializăm clientul de BigQuery
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"

    def unify_events(self, hudl_events: List[Dict], statsbomb_360: List[Dict]) -> List[UnifiedMatchEvent]:
        """
        Mapează JSON-urile Hudl (ca evenimente primare) și datele StatsBomb 
        (pentru tracking 360°) într-o structură unică.
        """
        logger.info(f"🔗 Unifying {len(hudl_events)} Hudl events with {len(statsbomb_360)} StatsBomb 360 frames...")
        
        # Mapează telemetria StatsBomb 360 folosind un ID comun de eveniment (event_uuid)
        sb_map = {frame.get('event_uuid'): frame for frame in statsbomb_360 if 'event_uuid' in frame}
        
        unified_events = []
        for h_event in hudl_events:
            event_id = h_event.get("id")
            sb_tracking = sb_map.get(event_id, {})
            
            # Calculăm presiunea. Dacă Hudl nu o raportează clar, folosim senzorii 360° StatsBomb
            is_pressured = h_event.get("under_pressure", False)
            freeze_frame = sb_tracking.get("freeze_frame", [])
            
            if not is_pressured and freeze_frame:
                # Verificăm inamicii din raza de 2 metri
                opponents_near = sum(1 for p in freeze_frame if not p.get("teammate") and p.get("distance_to_ball", 99) < 2.0)
                if opponents_near > 0:
                    is_pressured = True

            # Extragem locația, de obicei un vector [X, Y]
            location = h_event.get("location", [0.0, 0.0])
            
            unified = UnifiedMatchEvent(
                match_id=str(h_event.get("match_id")),
                timestamp=str(h_event.get("timestamp")),
                event_type=h_event.get("type", {}).get("name", "Unknown"),
                player_id=str(h_event.get("player", {}).get("id")),
                team_id=str(h_event.get("team", {}).get("id")),
                x=location[0] if len(location) > 0 else 0.0,
                y=location[1] if len(location) > 1 else 0.0,
                is_under_pressure=is_pressured,
                tracking_360=freeze_frame
            )
            unified_events.append(unified)
            
        return unified_events

    def load_to_bigquery(self, events: List[UnifiedMatchEvent]):
        """
        Logica de încărcare masivă (Bulk Insert) în BigQuery.
        """
        logger.info(f"🚀 Începem inserția masivă în BigQuery pentru {len(events)} evenimente...")
        
        rows_to_insert = [ev.to_dict() for ev in events]
        
        # Insert Streaming in BigQuery
        errors = self.client.insert_rows_json(self.table_ref, rows_to_insert)
        
        if not errors:
            logger.info("✅ Încărcare BigQuery completă cu succes!")
        else:
            logger.error(f"❌ Erori la încărcarea în BigQuery: {errors}")

# === EXEMPLU DE UTILIZARE ===
if __name__ == "__main__":
    import uuid
    # Mocking data pentru verificare locală
    mock_hudl = [{
        "id": "event_123", "match_id": 99, "timestamp": "00:14:32.100",
        "type": {"name": "Dispossessed"}, "player": {"id": 10}, "team": {"id": "CFR"},
        "location": [35.2, 20.1], "under_pressure": False
    }]
    mock_sb = [{
        "event_uuid": "event_123",
        "freeze_frame": [{"teammate": False, "distance_to_ball": 1.2}]
    }]
    
    # Notă: Această bucată va crăpa local dacă nu aveți contul de servicii GCP activ
    unifier = DataUnifier(project_id="forma-os", dataset_id="analytics", table_id="unified_events")
    unified = unifier.unify_events(mock_hudl, mock_sb)
    # unifier.load_to_bigquery(unified)
