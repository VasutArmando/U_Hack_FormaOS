import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ==============================================================================
# DOCUMENTEZ STRUCTURA JSON-URILOR EXAMINATE:
# 
# 1. În arhiva ZIP extrasă am găsit fișiere masive de tip "*_players_stats.json" 
#    și "players (1).json" care corespund formatului de provideri mari (Hudl/Wyscout).
# 
# 2. STRUCTURA FIȘIERELOR DE STATISTICI:
#    Aceste fișiere conțin o listă `"players"`, fiecare obiect având:
#    - "playerId", "matchId"
#    - "total": (ex: "passes", "goals", "duels", "defensiveDuels")
#    - "average" și "percent": rate de conversie și medii
#    - "positions": listă de roluri tactice jucate în meci (ex: "Right Wing Forward")
#
# 3. STRUCTURA EVENIMENTELOR PENTRU EXTRAGERE:
#    Pentru extragerea *coordonatelor* și *timpului* exacte (Pase, Șuturi), 
#    parserul implementează standardul de telemetrie de evenimente care conține:
#    - "eventName": "Pass" / "Shot" / "Duel" / "Interception"
#    - "matchPeriod": "1H" / "2H"
#    - "eventSec": (secunda exactă a evenimentului pe teren)
#    - "positions": [{"x": <start_x>, "y": <start_y>}, {"x": <end_x>, "y": <end_y>}]
# ==============================================================================

class MatchDataParser:
    """
    Motorul de ingestie și parsare pentru fișierele JSON din analiza video (Hudl/StatsBomb).
    Pregătește seturile de date brute pentru a fi consumate de ORACLE și X-RAY.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        """Încarcă și returnează fișierul JSON."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Eroare la deschiderea fișierului {self.file_path}: {e}")
            return {}

    def extract_passes(self) -> List[Dict[str, Any]]:
        """
        Extrage coordonatele tuturor paselor (pentru modulul ORACLE).
        Se folosește array-ul "positions" care la pase conține [start, end].
        """
        passes = []
        # Căutăm lista de evenimente
        events = self.raw_data.get('events', [])
        
        for event in events:
            if event.get('eventName') == 'Pass':
                positions = event.get('positions', [])
                if len(positions) >= 2:
                    passes.append({
                        'player_id': event.get('playerId'),
                        'time_sec': event.get('eventSec'),
                        'period': event.get('matchPeriod'),
                        'start_x': positions[0].get('x'),
                        'start_y': positions[0].get('y'),
                        'end_x': positions[1].get('x'),
                        'end_y': positions[1].get('y'),
                        'success': 'Accurate' in [tag.get('id') for tag in event.get('tags', [])]
                    })
        return passes

    def extract_defensive_and_shots(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extrage locațiile șuturilor și evenimentelor defensive (pentru harta vulnerabilităților X-RAY).
        """
        xray_data = {'shots': [], 'defensive_actions': []}
        events = self.raw_data.get('events', [])

        for event in events:
            event_name = event.get('eventName')
            positions = event.get('positions', [])
            
            if not positions:
                continue

            event_info = {
                'player_id': event.get('playerId'),
                'time_sec': event.get('eventSec'),
                'period': event.get('matchPeriod'),
                'x': positions[0].get('x'),
                'y': positions[0].get('y'),
            }

            if event_name == 'Shot':
                xray_data['shots'].append(event_info)
            elif event_name in ['Duel', 'Interception', 'Clearance']:
                # Extragem evenimentele care ne indică unde intervine apărarea (unde e testată sub presiune)
                xray_data['defensive_actions'].append(event_info)

        return xray_data

    def extract_timeline(self) -> List[Dict[str, Any]]:
        """
        Extrage timpul fiecărui eveniment pentru a putea genera raportul de Half-Time.
        """
        timeline = []
        events = self.raw_data.get('events', [])
        
        for event in events:
            timeline.append({
                'event_id': event.get('id'),
                'event_name': event.get('eventName'),
                'period': event.get('matchPeriod'),
                'time_sec': event.get('eventSec'),
                'player_id': event.get('playerId')
            })
            
        # Asigurăm sortarea cronologică
        return sorted(timeline, key=lambda x: (x['period'], x['time_sec']))

# Bloc de test (Run local)
if __name__ == "__main__":
    # Test path:
    parser = MatchDataParser("data/raw_json/Date - meciuri/Argeș - Universitatea Cluj, 1-0_players_stats.json")
    print(f"Inițializare Data Parser... Extragere cronologie: {len(parser.extract_timeline())} evenimente.")
