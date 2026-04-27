import sqlite3
import json
import logging
import os
import unicodedata
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any


from services.observer_pattern import Observer
from services.news_engine import generate_pregame_intelligence, generate_pregame_intelligence_v2
from services.scraper import scrape_opponent_news
from services.news_cache import get_or_fetch
from services.stadium_vision_service import vision_pipeline

logger = logging.getLogger("uvicorn")

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
        self._players_role_cache = None
        self._players_birth_cache = None
        self.data_dir = str(Path(__file__).parent.parent / "Data_Fixed" / "Date - meciuri")

    def update(self, event_type: str, data: Any):
        if event_type == "VISION_UPDATE":
            self.live_vision_gaps = data.get("gaps", [])
            self.live_vision_fatigue = data.get("fatigue_metrics", {})
            self.fallback_db.update(event_type, data)
            
    def _super_clean(self, name):
        if not name: return ""
        if not isinstance(name, str): name = str(name)
        # 1. Fix possible double encoding (common in hackathon datasets)
        # If string contains double-encoded UTF-8 chars seen as Latin-1
        if any(c in name for c in ["Ì", "¦", "§", "©", "ª"]):
            try:
                # Attempt to recover from double-encoding
                name = name.encode('latin-1').decode('utf-8')
            except Exception:
                pass
        
        # 2. Normalize and strip diacritics
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
        
        # 3. Final cleaning
        clean = name.lower()
        clean = "".join([c for c in clean if c.isalnum() or c == ' ']).strip()
        return clean.replace(' ', '_')

    @staticmethod
    def _nfc(s: str) -> str:
        """NFC-normalize a string so composed and decomposed Unicode chars compare equal."""
        return unicodedata.normalize('NFC', s) if s else s

    def _parse_players_mapping(self):
        if self._players_mapping_cache is not None:
            return
            
        self._players_mapping_cache = {}
        self._players_team_cache = {}
        self._players_role_cache = {}
        self._players_birth_cache = {}
        players_file = os.path.join(self.data_dir, "players (1).json")
        try:
            if os.path.exists(players_file):
                with open(players_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'players' in data:
                        for p in data['players']:
                            pid = str(p.get('wyId', ''))
                            name = p.get('shortName') or f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
                            # Use super_clean to avoid encoding/diacritic mismatches
                            teamname = self._super_clean(p.get('teamname', 'Unknown'))
                            role = p.get('role', {}).get('name', '') if isinstance(p.get('role'), dict) else ''
                            birth_country = p.get('birthArea', {}).get('name', 'Unknown') if isinstance(p.get('birthArea'), dict) else 'Unknown'
                            if pid and name:
                                self._players_mapping_cache[pid] = name
                                self._players_team_cache[pid] = teamname
                                self._players_role_cache[pid] = role
                                self._players_birth_cache[pid] = birth_country
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
                    
                # Robust parsing: remove suffix first
                name_part = filename.replace('_players_stats.json', '')
                # name_part is e.g. "Argeș - FCS Bucures,ti, 1-0"
                # Split by the LAST comma to separate teams from the score
                if ',' in name_part:
                    teams_part = name_part.rsplit(',', 1)[0] # "Argeș - FCS Bucures,ti"
                else:
                    teams_part = name_part
                    
                teams_split = teams_part.split(' - ')
                if len(teams_split) == 2:
                    # Use super_clean for filenames as well
                    team1 = self._super_clean(teams_split[0].strip())
                    team2 = self._super_clean(teams_split[1].strip())
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
                        known_teams[self._super_clean(t['name'])] = t['id']
            
            for team_name in team_names:
                c_name = self._super_clean(team_name)
                team_id = known_teams.get(c_name, c_name)
                if 'fcs' in c_name and 'fcsb' in known_teams: team_id = known_teams['fcsb']
                elif 'dinamo' in c_name and 'dinamo_bucuresti' in known_teams: team_id = known_teams['dinamo_bucuresti']
                elif 'rapid' in c_name and 'rapid_bucuresti' in known_teams: team_id = known_teams['rapid_bucuresti']
                
                display_name = team_name
                
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
        from services.news_cache import get_cached_gaps, set_cached_gaps, get_cached_profiles
        from services.news_engine import generate_chronic_gaps

        if not opponent_id:
            return self.fallback_db.get_chronic_gaps(opponent_id)

        self._parse_local_files()
        
        # Get opponent name
        opponent_name = "Adversar"
        for team in (self._teams_cache or []):
            if team.get("id") == opponent_id:
                opponent_name = team.get("name", "Adversar")
                break
                
        opponent_name_clean = self._super_clean(opponent_name)

        # 1. Check if we have cached gaps
        cached_gaps = get_cached_gaps(opponent_name_clean)
        if cached_gaps is not None:
            logger.info(f"Returning cached chronic gaps for {opponent_name_clean}")
            return cached_gaps

        # 2. Get weakness data (cached profiles)
        weakness_data = get_cached_profiles(opponent_name) or []
        
        # 3. Build match summary
        matches_summary = ""
        if self._matches_cache:
            opponent_matches = []
            for match_id, match_data in self._matches_cache.items():
                if match_data.get('team1') == opponent_name_clean or match_data.get('team2') == opponent_name_clean:
                    opponent_matches.append(match_data)
            
            if opponent_matches:
                matches_summary = f"Am analizat {len(opponent_matches)} meciuri istorice. Adversarul {opponent_name} este predispus la dezechilibre in functie de performanta jucatorilor semnalati."
            else:
                matches_summary = "Nu există istoric de meciuri suficient."
        else:
            matches_summary = "Datele despre meciuri nu sunt disponibile."

        # 4. Generate gaps
        logger.info(f"Generating chronic gaps via Gemini for {opponent_name_clean}...")
        gaps = generate_chronic_gaps(opponent_name, weakness_data, matches_summary)
        
        # 5. Cache and return
        if gaps:
            set_cached_gaps(opponent_name_clean, gaps)
        
        return gaps

    def get_opponent_weaknesses(self, opponent_id: str = None, opponent_name: str = "Adversar",
                                stadium_id: str = None, game_date: str = None) -> List[Dict[str, Any]]:
        self._parse_local_files()
        self._parse_players_mapping()
        
        # Use super_clean to ensure matching regardless of diacritics or encoding
        opponent_name_clean = self._super_clean(opponent_name)
        
        # Fetch match-day weather (if stadium + date provided)
        match_weather = None
        if stadium_id and game_date:
            match_weather = self.get_match_weather(stadium_id, game_date)
            logger.info(f"Match weather for {game_date} @ {stadium_id}: {match_weather}")
        
        if opponent_id and self._matches_cache:
            opponent_matches = []
            for match_id, match_data in self._matches_cache.items():
                if match_data.get('team1') == opponent_name_clean or match_data.get('team2') == opponent_name_clean:
                    opponent_matches.append(match_data)
            
            logger.info(f"Found {len(opponent_matches)} matches for opponent '{opponent_name_clean}'")
            
            if opponent_matches:
                player_stats_agg = {}
                # Use ALL matches to capture the full squad, not just 5
                for match in opponent_matches:
                    for p in match.get('players', []):
                        pid = str(p.get('playerId', ''))
                        
                        # Filter: only keep players from the opponent team
                        if self._players_team_cache.get(pid) != opponent_name_clean:
                            continue
                            
                        if pid not in player_stats_agg:
                            new_p = p.copy()
                            new_p['aggregated_minutes'] = 0
                            new_p['aggregated_duels'] = 0
                            new_p['aggregated_duels_won'] = 0
                            new_p['aggregated_matches'] = 0
                            player_stats_agg[pid] = new_p
                        
                        totals = p.get('total', {})
                        player_stats_agg[pid]['aggregated_minutes'] += totals.get('minutesOnField', 0)
                        player_stats_agg[pid]['aggregated_duels'] += totals.get('duels', 0)
                        player_stats_agg[pid]['aggregated_duels_won'] += totals.get('duelsWon', 0)
                        player_stats_agg[pid]['aggregated_matches'] += 1
                            
                players_list = list(player_stats_agg.values())
                # Show ALL players who appeared in at least 1 match
                players_list = [p for p in players_list if p.get('aggregated_matches', 0) >= 1]

                def weakness_metric(p):
                    minutes = max(p.get('aggregated_minutes', 1), 1)
                    duels = max(p.get('aggregated_duels', 1), 1)
                    duels_won = p.get('aggregated_duels_won', 0)
                    win_rate = duels_won / duels
                    fatigue_factor = min(minutes / 900.0, 1.0)
                    performance_factor = 1.0 - win_rate
                    return fatigue_factor * 0.5 + performance_factor * 0.5

                players_list.sort(key=weakness_metric, reverse=True)

                # Inject names, roles, and birth countries from players mapping
                for p in players_list:
                    pid = str(p.get('playerId', ''))
                    p['name'] = self._players_mapping_cache.get(pid, f"Player {pid}")
                    p['player_role'] = self._players_role_cache.get(pid, '')
                    p['birth_country'] = self._players_birth_cache.get(pid, 'Unknown')

                # --- Scraping pipeline (Layer 1 + 2) ---
                player_names = [
                    p['name'] for p in players_list
                    if p.get('name') and not p['name'].startswith('Player ')
                ]
                logger.info(
                    f"Starting news scrape for '{opponent_name}' — "
                    f"{len(players_list)} total players, "
                    f"{len(player_names)} named."
                )

                # Check if a valid cache exists (has actual player articles, not just RSS headlines)
                from services.news_cache import get_cached_news, set_cached_news
                cached_news = get_cached_news(opponent_name, game_date=game_date)
                
                # Determine if cache is usable: needs real player articles with body text
                cache_is_usable = False
                if cached_news:
                    player_articles = cached_news.get("player_articles", {})
                    total_with_body = sum(
                        1 for articles in player_articles.values()
                        for a in articles if len(a.get("body", "")) > 100
                    )
                    sources = cached_news.get("sources_used", [])
                    # Only trust cache if it came from a full scrape (gsp/prosport), not just RSS headlines
                    has_real_source = "gsp.ro" in sources or "prosport.ro" in sources
                    cache_is_usable = has_real_source and total_with_body > 0
                    if not cache_is_usable:
                        logger.info(f"Cache for '{opponent_name}' exists but has no real player articles (sources={sources}, bodies={total_with_body}). Re-scraping fresh.")

                if cache_is_usable:
                    scraped_news = cached_news
                    logger.info(f"Using valid cache for '{opponent_name}' with player articles.")
                else:
                    # Fresh scrape — always fetch full bodies
                    logger.info(f"Fetching fresh news for '{opponent_name}' with {len(player_names)} players...")
                    scraped_news = scrape_opponent_news(
                        opponent_name,
                        player_names,
                        fetch_full_bodies=True,
                    )
                    if scraped_news:
                        set_cached_news(opponent_name, scraped_news, game_date=game_date)
                        total_player_arts = sum(len(v) for v in scraped_news.get("player_articles", {}).values())
                        logger.info(
                            f"Scrape complete for '{opponent_name}': "
                            f"{len(scraped_news.get('team_articles', []))} team articles, "
                            f"{total_player_arts} player articles across "
                            f"{len(scraped_news.get('player_articles', {}))} players."
                        )

                return generate_pregame_intelligence_v2(
                    players_list, opponent_name, scraped_news,
                    match_weather=match_weather,
                )
                
        return self.fallback_db.get_opponent_weaknesses(opponent_id, opponent_name)

    def get_match_weather(self, stadium_id: str, game_date: str) -> dict:
        """Fetch match-day forecast using stadium lat/lng + game date ISO string."""
        from services.weather_engine import get_stadium_coords, get_forecast_for_match, get_live_weather
        from datetime import datetime, timezone

        coords = get_stadium_coords(stadium_id)
        lat, lng = coords.get('lat'), coords.get('lng')

        if lat is None or lng is None:
            logger.warning(f"No coords for stadium {stadium_id}, using live weather fallback")
            return get_live_weather()

        try:
            # Parse ISO date; support with or without timezone
            dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return get_forecast_for_match(lat, lng, dt)
        except Exception as e:
            logger.warning(f"get_match_weather parse error: {e}")
            return get_live_weather(lat=lat, lng=lng)

    def get_halftime_changes(self) -> List[Dict[str, Any]]:
        return self.fallback_db.get_halftime_changes()

# Singleton Export
db_provider = LocalFilesProvider()
