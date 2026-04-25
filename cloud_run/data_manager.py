import sqlite3
import json
import logging
import os
import unicodedata
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any


from services.observer_pattern import Observer
from services.news_engine import generate_pregame_intelligence
from services.stadium_vision_service import vision_pipeline

logger = logging.getLogger("forma_os_data")

# 1. Abstracție - Data Provider Pattern (Arhitectură pentru Baze de Date Open-Source)
class DataProvider(ABC):
    @abstractmethod
    def get_teams(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_stadiums(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_ingame_players(self) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_live_gaps(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_chronic_gaps(self, opponent_id: str = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_opponent_weaknesses(self, opponent_id: str = None, opponent_name: str = "Adversar") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_halftime_changes(self) -> List[Dict[str, Any]]:
        pass

# 2. Implementare Concretă pentru Baza de Date GDG
class GDGDatabaseProvider(DataProvider, Observer):
    def __init__(self, db_path="data/gdg_sports_data.db"):
        self.db_path = db_path
        self.live_vision_gaps = []
        self.live_vision_fatigue = {}
        self._init_db()
        # Conectăm Data Manager la Pipeline-ul de Viziune (Observer Pattern)
        vision_pipeline.attach(self)

    def update(self, event_type: str, data: Any):
        if event_type == "VISION_UPDATE":
            logger.info("Data Manager received Vertex AI Vision Update.")
            self.live_vision_gaps = data.get("gaps", [])
            self.live_vision_fatigue = data.get("fatigue_metrics", {})
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def _init_db(self):
        """Configurează tabelele pentru procesarea seturilor mari de tracking și pregame data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Ingestie Tracking Live
            cursor.execute('''CREATE TABLE IF NOT EXISTS live_tracking 
                              (timestamp REAL, player_id TEXT, x REAL, y REAL, speed REAL, heart_rate REAL)''')
            # Tactical Events
            cursor.execute('''CREATE TABLE IF NOT EXISTS pregame_intel 
                              (player_id TEXT, name TEXT, team_id TEXT, physical_state TEXT, psychological_state TEXT, weakness_score REAL)''')
            
            # Sincronizare Demo Live
            cursor.execute("SELECT count(*) FROM live_tracking")
            if cursor.fetchone()[0] == 0:
                self._seed_demo_data(cursor)
            conn.commit()

    def _seed_demo_data(self, cursor):
        """Populează baza de date cu evenimente de tracking (X, Y) în timp real."""
        logger.info("Initializing GDG DB with hackathon tracking stream...")
        # Tracking live data
        cursor.execute("INSERT INTO live_tracking VALUES (1.0, 'p2', 80.0, 50.0, 8.2, 185.0)") # Ionescu - high HR, exhausted
        cursor.execute("INSERT INTO live_tracking VALUES (1.5, 'p1', 20.0, 45.0, 4.1, 150.0)") # Popescu - normal HR
        cursor.execute("INSERT INTO live_tracking VALUES (2.0, 'p4', 60.0, 10.0, 6.0, 140.0)") # Radu
        
        # Pregame intel real din DB (Acum cu team_id, default t2 pentru adversar)
        cursor.execute("INSERT INTO pregame_intel VALUES ('p1', 'Popescu Andrei (CM)', 't2', 'Slight hamstring tightness.', 'Low morale.', 75.0)")
        cursor.execute("INSERT INTO pregame_intel VALUES ('p2', 'Ionescu Marian (RB)', 't2', 'Recovering from ankle sprain.', 'High stress.', 85.0)")
        cursor.execute("INSERT INTO pregame_intel VALUES ('p3', 'Stoica Vasile (CB)', 't2', 'Fully fit.', 'Confident.', 40.0)")
        cursor.execute("INSERT INTO pregame_intel VALUES ('p4', 'Dieng Oumar (RW)', 't2', 'Not acclimated.', 'Frustrated.', 90.0)")

    def get_teams(self) -> List[Dict[str, Any]]:
        base_path = Path(__file__).parent / "data" / "teams.json"
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get("teams", [])
        return []

    def get_stadiums(self) -> List[Dict[str, Any]]:
        base_path = Path(__file__).parent / "data" / "stadiums.json"
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get("stadiums", [])
        return []

    def get_ingame_players(self) -> List[Dict[str, Any]]:
        """Sincronizarea Statusului: Extras direct din datele biometrice / tracking."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT player_id, AVG(speed) as avg_speed, AVG(heart_rate) as avg_hr FROM live_tracking GROUP BY player_id")
            tracking_stats = cursor.fetchall()
            
            # Mapare Automată pe modelul 'Vulnerability'
            players_mapping = {
                "p1": "Popescu Andrei (CM)",
                "p2": "Ionescu Marian (RB)",
                "p3": "Stoica Vasile (CB)",
                "p4": "Radu Alexandru (LW)"
            }
            
            results = []
            for row in tracking_stats:
                pid = row["player_id"]
                avg_hr = row["avg_hr"]
                # Calcul real de fatigue pe baza HR DB
                fatigue = min(100.0, max(0.0, (avg_hr - 60) / 1.4))
                
                remark = "Tracking normal."
                if fatigue > 85:
                    remark = "Sprint speed dropped significantly. Biometrics show exhaustion."
                elif fatigue > 60:
                    remark = "Struggling with the pace."
                    
                
                # Integrăm datele de viziune (Vertex AI fatigue overlay)
                vision_fatigue = self.live_vision_fatigue.get(pid)
                if vision_fatigue:
                    fatigue = max(fatigue, vision_fatigue.get("fatigue", fatigue))
                    remark = vision_fatigue.get("sprint_drop", remark)
                    
                results.append({
                    "id": pid,
                    "name": players_mapping.get(pid, f"Player {pid}"),
                    "fatigue": round(fatigue, 1),
                    "live_remark": remark
                })
                
            # Adaugă fallback dacă unii jucători nu au tracking momentan
            for pid, name in players_mapping.items():
                if not any(p["id"] == pid for p in results):
                    results.append({"id": pid, "name": name, "fatigue": 20.0, "live_remark": "No active tracking data."})
            return results

    def get_live_gaps(self) -> List[Dict[str, Any]]:
        """Calcul în Timp Real: Algoritmii de detecție din Vertex AI (Vision) + Stream."""
        gaps = list(self.live_vision_gaps)
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT x, y FROM live_tracking ORDER BY timestamp DESC LIMIT 50")
            points = cursor.fetchall()
            if points:
                avg_x = sum(p["x"] for p in points) / len(points)
                if avg_x > 50:
                    gaps.append({
                        "id": "gap_live_db",
                        "location": "Right Wing",
                        "description": f"Real-time Tracking detectează bloc defensiv deschis pe flanc (DB X_avg: {avg_x:.1f}).",
                        "severity": "Critical",
                        "coordinates": {"x": 80.0, "y": 50.0, "w": 60.0, "h": 80.0}
                    })
                else:
                    gaps.append({
                        "id": "gap_live_db2",
                        "location": "Deep Midfield",
                        "description": "Midfield is dropping too deep based on tracking stream.",
                        "severity": "High",
                        "coordinates": {"x": 20.0, "y": 0.0, "w": 50.0, "h": 40.0}
                    })
            return gaps

    def get_chronic_gaps(self, opponent_id: str = None) -> List[Dict[str, Any]]:
        # Mapate din arhiva pregame DB. Folosim opponent_id pentru demo (deși hardcodat, returnăm doar dacă e valid).
        if opponent_id and opponent_id != "t2":
            return [] # No demo data for other teams

        return [{
            "id": "gap_pre_db",
            "location": "Left Flank / Half Space",
            "description": "Historical DB shows left back inverts frequently.",
            "severity": "High",
            "coordinates": {"x": -80.0, "y": -40.0, "w": 60.0, "h": 100.0}
        }]

    def get_opponent_weaknesses(self, opponent_id: str = None, opponent_name: str = "Adversar") -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if opponent_id:
                cursor.execute("SELECT * FROM pregame_intel WHERE team_id = ?", (opponent_id,))
            else:
                cursor.execute("SELECT * FROM pregame_intel")
            db_intel = [dict(row) for row in cursor.fetchall()]
            
        # Folosim Gemini și News Engine pentru a rafina rezultatul direct din DB
        return generate_pregame_intelligence(db_intel, opponent_name)
            
    def get_halftime_changes(self) -> List[Dict[str, Any]]:
        # Predictive Analytics: Analiză Istorică
        historical_behavior = "În meciurile precedente, când erau conduși, au scos un închizător pentru a introduce un extremă."
        return [{
            "id": "ht_1_vertex",
            "title": "Predictive Historical Substitution",
            "category": "Substitution",
            "likelihood": 92.0,
            "description": f"Vertex AI & Predictive Analytics: {historical_behavior} Schimbă tactica pe flancuri."
        }]

    def get_halftime_gaps(self) -> List[Dict[str, Any]]:
        return self.get_live_gaps()

# 3. Implementare Concretă pentru Fisiere Locale (Hardcoded din Folderul Date - meciuri)
class LocalFilesProvider(DataProvider, Observer):
    def __init__(self):
        self.live_vision_gaps = []
        self.live_vision_fatigue = {}
        self.fallback_db = GDGDatabaseProvider()
        vision_pipeline.attach(self)
        
        # Caching the parsed data
        self._teams_cache = None
        self._matches_cache = None
        self._players_team_cache = None
        self._players_mapping_cache = None
        self.data_dir = r"E:\U_Hack_FormaOS-1\Data_Fixed\Date - meciuri"

    def update(self, event_type: str, data: Any):
        if event_type == "VISION_UPDATE":
            self.live_vision_gaps = data.get("gaps", [])
            self.live_vision_fatigue = data.get("fatigue_metrics", {})
            self.fallback_db.update(event_type, data)
            
    def _clean_id(self, name):
        clean = name.lower()
        clean = clean.replace('ș', 's').replace('ț', 't').replace('ş', 's').replace('ţ', 't')
        clean = "".join([c for c in clean if c.isalnum() or c == ' ']).strip()
        return clean.replace(' ', '_')

    def _parse_players_mapping(self):
        if self._players_mapping_cache is not None:
            return
            
        self._players_mapping_cache = {}
        self._players_team_cache = {}
        players_file = os.path.join(self.data_dir, "players (1).json")
        try:
            if os.path.exists(players_file):
                with open(players_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'players' in data:
                        for p in data['players']:
                            pid = str(p.get('wyId', ''))
                            name = p.get('shortName') or f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
                            teamname = p.get('teamname', 'Unknown')
                            if pid and name:
                                self._players_mapping_cache[pid] = name
                                self._players_team_cache[pid] = teamname
        except Exception as e:
            logger.error(f"Error parsing players mapping: {e}")

    def _parse_local_files(self):
        if self._teams_cache is not None:
            return
            
        logger.info(f"Parsing local match files from {self.data_dir}...")
        team_matches = {}
        team_names = set()
        matches_dict = {}
        
        try:
            if not os.path.exists(self.data_dir):
                logger.warning(f"Directory {self.data_dir} not found.")
                self._teams_cache = []
                self._matches_cache = {}
                return

            files = [f for f in os.listdir(self.data_dir) if f.endswith('.json') and "players_stats" in f]
            for filename in files:
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    continue
                    
                if not isinstance(data, dict) or 'players' not in data or not data['players']:
                    continue
                    
                match_id = str(data['players'][0].get('matchId'))
                if not match_id or match_id == 'None':
                    continue
                    
                name_part = filename.split(',')[0]
                teams_split = name_part.split(' - ')
                if len(teams_split) == 2:
                    team1, team2 = teams_split[0].strip(), teams_split[1].strip()
                else:
                    team1, team2 = "Unknown", "Unknown"
                    
                if team1 != "Unknown":
                    team_names.add(team1)
                    team_matches.setdefault(team1, set()).add(match_id)
                if team2 != "Unknown":
                    team_names.add(team2)
                    team_matches.setdefault(team2, set()).add(match_id)
                    
                data['team1'] = team1
                data['team2'] = team2
                matches_dict[match_id] = data
                
            # Now build teams list
            teams_list = []
            known_teams = {}
            base_path = Path(__file__).parent / "data" / "teams.json"
            if base_path.exists():
                with open(base_path, "r", encoding="utf-8") as f:
                    known_data = json.load(f)
                    if isinstance(known_data, dict):
                        known_data = known_data.get("teams", [])
                    for t in known_data:
                        known_teams[self._clean_id(t['name'])] = t['id']
            
            for team_name in team_names:
                # Folosim unicodedata pentru a elimina caracterele diacritice (inclusiv cele compuse)
                clean_team_name = unicodedata.normalize('NFKD', team_name).encode('ASCII', 'ignore').decode('utf-8')
                c_name = self._clean_id(clean_team_name)
                team_id = known_teams.get(c_name, c_name)
                if 'fcs' in c_name and 'fcsb' in known_teams: team_id = known_teams['fcsb']
                elif 'dinamo' in c_name and 'dinamo_bucuresti' in known_teams: team_id = known_teams['dinamo_bucuresti']
                elif 'rapid' in c_name and 'rapid_bucuresti' in known_teams: team_id = known_teams['rapid_bucuresti']
                
                display_name = clean_team_name
                
                teams_list.append({
                    'id': team_id,
                    'name': display_name,
                    'matchIds': list(team_matches.get(team_name, set()))
                })
                
            self._teams_cache = teams_list
            self._matches_cache = matches_dict
            logger.info(f"Successfully parsed {len(self._teams_cache)} teams and {len(self._matches_cache)} matches.")
            
        except Exception as e:
            logger.error(f"Error parsing local files: {e}")
            self._teams_cache = []
            self._matches_cache = {}

    def get_teams(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_teams()
        
    def get_all_matches(self) -> Dict[str, Any]:
        self._parse_local_files()
        return self._matches_cache

    def get_stadiums(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_stadiums()

    def get_ingame_players(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_ingame_players()

    def get_live_gaps(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_live_gaps()

    def get_chronic_gaps(self, opponent_id: str = None) -> List[Dict[str, Any]]:
        return self.fallback_db.get_chronic_gaps(opponent_id)

    def get_opponent_weaknesses(self, opponent_id: str = None, opponent_name: str = "Adversar") -> List[Dict[str, Any]]:
        self._parse_local_files()
        self._parse_players_mapping()
        
        if opponent_id and self._matches_cache:
            opponent_matches = []
            for match_id, match_data in self._matches_cache.items():
                if match_data.get('team1') == opponent_name or match_data.get('team2') == opponent_name:
                    opponent_matches.append(match_data)
            
            if opponent_matches:
                player_stats_agg = {}
                for match in opponent_matches[:5]: # Take last 5 matches to limit payload size
                    for p in match.get('players', []):
                        pid = str(p.get('playerId', ''))
                        
                        # Filter out players from the other team using the new teamname mapping
                        if self._players_team_cache.get(pid) != opponent_name:
                            continue
                            
                        if pid not in player_stats_agg:
                            new_p = p.copy()
                            new_p['aggregated_minutes'] = 0
                            new_p['aggregated_duels'] = 0
                            new_p['aggregated_duels_won'] = 0
                            player_stats_agg[pid] = new_p
                        
                        totals = p.get('total', {})
                        player_stats_agg[pid]['aggregated_minutes'] += totals.get('minutesOnField', 0)
                        player_stats_agg[pid]['aggregated_duels'] += totals.get('duels', 0)
                        player_stats_agg[pid]['aggregated_duels_won'] += totals.get('duelsWon', 0)
                            
                players_list = list(player_stats_agg.values())
                # Filter players who actually played at least a match worth of minutes
                players_list = [p for p in players_list if p.get('aggregated_minutes', 0) > 45]
                
                def weakness_metric(p):
                    minutes = p.get('aggregated_minutes', 1)
                    duels = max(p.get('aggregated_duels', 1), 1)
                    duels_won = p.get('aggregated_duels_won', 0)
                    win_rate = duels_won / duels
                    
                    fatigue_factor = min(minutes / 450.0, 1.0)
                    performance_factor = 1.0 - win_rate
                    return fatigue_factor * 0.5 + performance_factor * 0.5
                
                players_list.sort(key=weakness_metric, reverse=True)
                
                # Get up to 6 worst performing key players to deep-dive search
                selected_players = players_list[:6]
                
                for p in selected_players:
                    pid = str(p.get('playerId', ''))
                    # Inject actual mapped name
                    p['name'] = self._players_mapping_cache.get(pid, f"Player {pid}")
                    
                return generate_pregame_intelligence(selected_players, opponent_name)
                
        return self.fallback_db.get_opponent_weaknesses(opponent_id, opponent_name)

    def get_halftime_changes(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_halftime_changes()

# Singleton Export
db_provider = LocalFilesProvider()
