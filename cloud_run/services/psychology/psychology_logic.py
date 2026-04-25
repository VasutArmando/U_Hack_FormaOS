import os
import json
import logging
import time
import hashlib
import google.generativeai as genai
from .news_crawler import NewsCrawler

logger = logging.getLogger("forma_os")

def load_env_psychology():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

class PsychologyBrain:
    def __init__(self):
        load_env_psychology()
        self.crawler = NewsCrawler()
        self.system_prompt = """Configurează Gemini să acționeze ca un analist psihologic sportiv care lucrează pentru Ioan Ovidiu Sabău.
Sarcina: Analizează știrile primite și identifică 'Puncția Tactică' (Tactical Puncture Point): unde este echipa adversă cel mai vulnerabilă mental astăzi?

Output-ul trebuie să fie strict un JSON cu următoarele chei:
- vulnerability_index (int 0-100)
- targeted_player (numele jucătorului vulnerabil)
- mental_report (scurt raport tactic - puncția tactică).
"""
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=self.system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.cache_file = os.path.join(os.path.dirname(__file__), 'ai_psychology_cache.json')
        self.last_api_call = 0.0
        self.rate_limit_seconds = 10.0
        # Additional constants for club values and recruitment scoring
        self.HONOR_KEYWORDS = ["onoare", "respect", "muncă"]
        self.DISCIPLINARY_KEYWORDS = ["suspendat", "cartonaș galben", "cartonaș roșu", "disciplină", "încălcare", "exclus", "expulsat"]
        self.base_recruitment_score = 100

    def __init__(self):
        load_env_psychology()
        self.crawler = NewsCrawler()
        self.system_prompt = """Configurează Gemini să acționeze ca un analist psiholog sportiv care lucrează pentru Ioan Ovidiu Sabău.
Sarcina: Analizează știrile primite și identifică 'Puncția Tactică' (Tactical Puncture Point): unde este echipa adversă cel mai vulnerabilă mental astăzi?

Output-ul trebuie să fie strict un JSON cu următoarele chei:
- vulnerability_index (int 0-100)
- targeted_player (numele jucătorului vulnerabil)
- mental_report (scurt raport tactic - puncția tactică)."""

        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
             genai.configure(api_key=self.api_key)
        
        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=self.system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception:
            self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.cache_file = os.path.join(os.path.dirname(__file__), 'ai_psychology_cache.json')
        self.last_api_call = 0.0
        self.rate_limit_seconds = 10.0

    def _get_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _set_cache(self, cache_data: dict):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Eroare scriere cache psychology: {e}")

    def _get_fallback_profile(self) -> dict:
        # Mecanism de 'mock-data' în cazul în care API-ul Gemini este indisponibil
        return {
            "vulnerability_index": 50,
            "targeted_player": "Nespecificat",
            "mental_report": "Date indisponibile, abordăm jocul echilibrat."
        }

    def analyze_team_vulnerabilities(self, news_list: list) -> dict:
        """Analyze news, compute vulnerability, recruitment score, youth plan,
        weak‑link detection and suggest a shadow‑team.

        Returns a dict containing:
            - vulnerability_index, targeted_player, mental_report (Gemini output)
            - recruitment_score (0‑100) respecting club values
            - disciplinary_players (list)
            - development_plan (academy youths)
            - weak_links (detected opponent weak points)
            - shadow_team (3‑4 candidate players per position)
        """
        # -----------------------------------------------------
        # Fallback handling
        # -----------------------------------------------------
        if not news_list:
            return self._get_fallback_profile()
        if not self.api_key:
            return self._get_fallback_profile()

        # -----------------------------------------------------
        # Gemini request (same as before)
        # -----------------------------------------------------
        news_text = "\n".join([f"- {n['title']}" for n in news_list])
        payload_hash = hashlib.md5(news_text.encode('utf-8')).hexdigest()
        cache = self._get_cache()
        if payload_hash in cache:
            logger.info("🧠 PsychologyBrain Cache HIT.")
            result = cache[payload_hash]
        else:
            now = time.time()
            if now - self.last_api_call < self.rate_limit_seconds:
                wait_time = self.rate_limit_seconds - (now - self.last_api_call)
                return {"error": f"Rate limit activ. Așteaptă {wait_time:.1f}s."}
            prompt = f"Analizează aceste știri și generează JSON-ul cerut:\n{news_text}"
            try:
                logger.info("🧠 Apelare Gemini pentru analiza vulnerabilităților...")
                self.last_api_call = time.time()
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3].strip()
                result = json.loads(result_text)
                cache[payload_hash] = result
                self._set_cache(cache)
            except Exception as e:
                logger.error(f"Eroare Gemini Psychology: {e}")
                result = self._get_fallback_profile()
                result["error_encountered"] = str(e)[:100]

        # -----------------------------------------------------
        # 1️⃣ Club‑value scoring (Honor / Respect / Ambition / Tradition / Work)
        # -----------------------------------------------------
        recruitment_score = self.base_recruitment_score
        # Honor / Respect / Work already handled via HONOR_KEYWORDS
        honor_present = any(
            any(k.lower() in (n.get('title') or '').lower() for k in self.HONOR_KEYWORDS)
            for n in news_list
        )
        if not honor_present:
            recruitment_score -= 10
        # Additional values
        respect_present = any(
            any(k.lower() in (n.get('title') or '').lower() for k in self.RESPECT_KEYWORDS)
            for n in news_list
        )
        if not respect_present:
            recruitment_score -= 5
        ambition_present = any(
            any(k.lower() in (n.get('title') or '').lower() for k in self.AMBITION_KEYWORDS)
            for n in news_list
        )
        if not ambition_present:
            recruitment_score -= 5
        tradition_present = any(
            any(k.lower() in (n.get('title') or '').lower() for k in self.TRADITION_KEYWORDS)
            for n in news_list
        )
        if not tradition_present:
            recruitment_score -= 5
        work_present = any(
            any(k.lower() in (n.get('title') or '').lower() for k in self.WORK_KEYWORDS)
            for n in news_list
        )
        if not work_present:
            recruitment_score -= 5

        # -----------------------------------------------------
        # 2️⃣ Disciplinary issues (lower recruitment)
        # -----------------------------------------------------
        penalized_players = set()
        for n in news_list:
            title = (n.get('title') or '').lower()
            for kw in self.DISCIPLINARY_KEYWORDS:
                if kw in title:
                    words = n.get('title', '').split()
                    if len(words) >= 2:
                        possible_name = " ".join(words[:2])
                        penalized_players.add(possible_name)
        recruitment_score -= 15 * len(penalized_players)
        recruitment_score = max(0, min(100, recruitment_score))

        # -----------------------------------------------------
        # 3️⃣ Youth academy development plan (already computed earlier)
        # -----------------------------------------------------
        try:
            from data_manager import DataManager
            dm = DataManager()
            youth_plan = []
            for p in dm.players.values():
                role = (p.role or "").lower()
                if "youth" in role or "academy" in role or getattr(p, "is_academy", False):
                    minutes = getattr(p, "minutes_played", 0)
                    needed_minutes = 1800
                    plan = {
                        "player_id": p.id,
                        "player_name": p.name,
                        "current_minutes": minutes,
                        "target_minutes": needed_minutes,
                        "note": "Crește timpul de joc pentru a atinge 2 promovări/an",
                    }
                    youth_plan.append(plan)
        except Exception as e:
            logger.error(f"Eroare la generarea planului de dezvoltare pentru tineri: {e}")
            youth_plan = []

        # -----------------------------------------------------
        # 4️⃣ Weak‑link detection ("verigi slabe")
        # -----------------------------------------------------
        WEAK_LINK_KEYWORDS = ["presiune", "conflict", "tensiune", "problema", "critic", "criticată", "suspendat"]
        weak_links = []
        for n in news_list:
            title = n.get('title', '')
            lower = title.lower()
            for kw in WEAK_LINK_KEYWORDS:
                if kw in lower:
                    # naive player extraction – first two capitalised words
                    words = title.split()
                    if len(words) >= 2:
                        player_name = " ".join(words[:2])
                        weak_links.append({"player": player_name, "issue": kw})
        # -----------------------------------------------------
        # 5️⃣ Shadow‑team suggestion (3‑4 players per position)
        # -----------------------------------------------------
        shadow_team = []
        try:
            from data_manager import DataManager
            dm = DataManager()
            positions = {
                "Goalkeeper": ["portar"],
                "Defender": ["funda", "defender"],
                "Midfielder": ["mijlocaș", "midfielder"],
                "Forward": ["atacant", "forward"]
            }
            for pos_name, keywords in positions.items():
                candidates = []
                for p in dm.players.values():
                    role_low = (p.role or "").lower()
                    if any(k in role_low for k in keywords):
                        # prioritize academy players
                        score = getattr(p, "is_academy", False)
                        candidates.append({
                            "player_id": p.id,
                            "player_name": p.name,
                            "role": p.role,
                            "minutes_played": getattr(p, "minutes_played", 0),
                            "academy": score,
                        })
                # sort: academy first, then most minutes played
                candidates.sort(key=lambda x: (not x["academy"], -x["minutes_played"]))
                shadow_team.append({
                    "position": pos_name,
                    "candidates": candidates[:4]
                })
        except Exception as e:
            logger.error(f"Eroare la generarea echipei Shadow: {e}")
            shadow_team = []

        # -----------------------------------------------------
        # Append all extra fields to the Gemini result
        # -----------------------------------------------------
        result["recruitment_score"] = recruitment_score
        result["disciplinary_players"] = list(penalized_players)
        result["development_plan"] = youth_plan
        result["weak_links"] = weak_links
        result["shadow_team"] = shadow_team

        # -----------------------------------------------------
        # 6️⃣ Group Morale & Mental Weak Link Detection
        # -----------------------------------------------------
        GROUP_MORALE_KEYWORDS = ["conflict", "salar", "fan", "presiune", "nemulțumire", "tensiune"]
        group_issues = []
        for n in news_list:
            title = (n.get('title') or '').lower()
            for kw in GROUP_MORALE_KEYWORDS:
                if kw in title:
                    group_issues.append(kw)
        result["group_morale_issues"] = group_issues

        # Identify most critiqued player (mental weak link)
        player_critique_counts = {}
        for n in news_list:
            title = n.get('title', '')
            lower = title.lower()
            for kw in WEAK_LINK_KEYWORDS + ["injurie", "recuperare", "accidentare"]:
                if kw in lower:
                    words = title.split()
                    if len(words) >= 2:
                        player_name = " ".join(words[:2])
                        player_critique_counts[player_name] = player_critique_counts.get(player_name, 0) + 1
        if player_critique_counts:
            mental_weak_player = max(player_critique_counts, key=player_critique_counts.get)
            result["mental_weak_link"] = {"player": mental_weak_player, "issue": "high criticism"}
            # Sabău instruction
            result["sabau_instruction"] = f"Presați {mental_weak_player} în primele 15 minute, moralul lui este scăzut."
        else:
            result["mental_weak_link"] = None
            result["sabau_instruction"] = None

        return result

        """Analyze news, compute vulnerability, recruitment score and youth development plan.

        Returns a dictionary containing:
            - vulnerability_index, targeted_player, mental_report (from Gemini)
            - recruitment_score (0-100) reflecting club values
            - development_plan (list) for academy youngsters
        """
        # Load fallback if no news or API unavailable
        if not news_list:
            return self._get_fallback_profile()
        if not self.api_key:
            return self._get_fallback_profile()
        # Prepare raw news text for Gemini
        news_text = "\n".join([f"- {n['title']}" for n in news_list])
        # Compute hash for caching
        payload_hash = hashlib.md5(news_text.encode('utf-8')).hexdigest()
        cache = self._get_cache()
        if payload_hash in cache:
            logger.info("🧠 PsychologyBrain Cache HIT.")
            result = cache[payload_hash]
        else:
            now = time.time()
            if now - self.last_api_call < self.rate_limit_seconds:
                wait_time = self.rate_limit_seconds - (now - self.last_api_call)
                return {"error": f"Rate limit activ. Așteaptă {wait_time:.1f}s."}
            prompt = f"Analizează aceste știri și generează JSON-ul cerut:\n{news_text}"
            try:
                logger.info("🧠 Apelare Gemini pentru analiza vulnerabilităților...")
                self.last_api_call = time.time()
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3].strip()
                result = json.loads(result_text)
                cache[payload_hash] = result
                self._set_cache(cache)
            except Exception as e:
                logger.error(f"Eroare Gemini Psychology: {e}")
                result = self._get_fallback_profile()
                result["error_encountered"] = str(e)[:100]
        # -----------------------------------------------------
        # 1️⃣ Honor/Respect/Work keyword verification
        # -----------------------------------------------------
        honor_present = any(any(k.lower() in (n.get('title') or '').lower() for k in self.HONOR_KEYWORDS) for n in news_list)
        recruitment_score = self.base_recruitment_score
        if not honor_present:
            recruitment_score -= 10  # penalize lack of club values in media
        # -----------------------------------------------------
        # 2️⃣ Disciplinary issues detection (lower recruitment)
        # -----------------------------------------------------
        penalized_players = set()
        for n in news_list:
            title = (n.get('title') or '').lower()
            for kw in self.DISCIPLINARY_KEYWORDS:
                if kw in title:
                    # naive extraction of player name – assume first two words capitalized
                    words = n.get('title', '').split()
                    if len(words) >= 2:
                        possible_name = " ".join(words[:2])
                        penalized_players.add(possible_name)
        recruitment_score -= 15 * len(penalized_players)
        recruitment_score = max(0, min(100, recruitment_score))
        # -----------------------------------------------------
        # 3️⃣ Youth academy development plan
        # -----------------------------------------------------
        try:
            from data_manager import DataManager
            dm = DataManager()
            youth_plan = []
            for p in dm.players.values():
                # Identify academy youngsters – placeholder using role keyword
                role = (p.role or "").lower()
                if "youth" in role or "academy" in role or getattr(p, "is_academy", False):
                    minutes = getattr(p, "minutes_played", 0)
                    # Goal: at least 2 promotions per year – we approximate required minutes
                    needed_minutes = 1800  # e.g., 30 min per match * 60 matches
                    plan = {
                        "player_id": p.id,
                        "player_name": p.name,
                        "current_minutes": minutes,
                        "target_minutes": needed_minutes,
                        "note": "Crește timpul de joc pentru a atinge 2 promovări/an"
                    }
                    youth_plan.append(plan)
        except Exception as e:
            logger.error(f"Eroare la generarea planului de dezvoltare pentru tineri: {e}")
            youth_plan = []
        # Append extra fields to result
        result["recruitment_score"] = recruitment_score
        result["disciplinary_players"] = list(penalized_players)
        result["development_plan"] = youth_plan
        return result
        if not news_list:
            return self._get_fallback_profile()

        if not self.api_key:
            return self._get_fallback_profile()

        news_text = "\n".join([f"- {n['title']}" for n in news_list])
        payload_hash = hashlib.md5(news_text.encode('utf-8')).hexdigest()
        cache = self._get_cache()
        if payload_hash in cache:
            logger.info("🧠 PsychologyBrain Cache HIT.")
            return cache[payload_hash]

        now = time.time()
        if now - self.last_api_call < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - (now - self.last_api_call)
            return {"error": f"Rate limit activ. Așteaptă {wait_time:.1f}s."}
            
        prompt = f"Analizează aceste știri și generează JSON-ul cerut:\n{news_text}"

        try:
            logger.info("🧠 Apelare Gemini pentru analiza vulnerabilităților...")
            self.last_api_call = time.time()
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
                
            result_json = json.loads(result_text)
            
            cache[payload_hash] = result_json
            self._set_cache(cache)
            
            return result_json
        except Exception as e:
            logger.error(f"Eroare Gemini Psychology: {e}")
            fallback = self._get_fallback_profile()
            fallback["error_encountered"] = str(e)[:100]
            return fallback

    def analyze_team(self, team_name: str) -> dict:
        # Wrapper pt a menține compatibilitatea cu main.py
        from .news_crawler import get_superliga_news
        news_list = get_superliga_news(team_name)
        return self.analyze_team_vulnerabilities(news_list)

