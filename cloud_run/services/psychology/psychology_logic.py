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
        self.system_prompt = """Ești Ioan Ovidiu Sabău. Analizează aceste titluri de știri despre echipa adversă.
Identifică "Veriga Slabă" (un jucător contestat, accidentat sau nervos).
Evaluează "Nivelul de Haos" în vestiar (0-100).
Oferă o recomandare tactică: Cum profităm de starea lor mentală? (ex: "Portarul lor a greșit în ultima etapă și e criticat de fani, trebuie să șutăm mult de la distanță").
Returnează rezultatul strict sub formă de JSON cu cheile: "veriga_slaba", "nivel_haos", "recomandare_tactica"."""

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

    def analyze_team(self, team_name: str) -> dict:
        # Crawl for real news
        news_items = self.crawler.fetch_latest_news(team_name)
        
        if not news_items:
            return {
                "veriga_slaba": "Niciun jucător vizat recent de presă",
                "nivel_haos": 20,
                "recomandare_tactica": "Situația lor este stabilă și liniștită. Ne vom concentra pe propriul joc, posesie sigură.",
                "news_analyzed": 0
            }

        titles = [n['title'] for n in news_items]
        
        if not self.api_key:
            return {
                "veriga_slaba": "Lipsă API Key - MOCK",
                "nivel_haos": 50,
                "recomandare_tactica": "Joacă ofensiv.",
                "news_analyzed": len(titles)
            }

        payload_str = json.dumps({"team": team_name, "titles": titles}, sort_keys=True)
        payload_hash = hashlib.md5(payload_str.encode('utf-8')).hexdigest()
        
        cache = self._get_cache()
        if payload_hash in cache:
            logger.info("🧠 PsychologyBrain Cache HIT.")
            return cache[payload_hash]

        now = time.time()
        if now - self.last_api_call < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - (now - self.last_api_call)
            return {"error": f"Rate limit activ. Așteaptă {wait_time:.1f}s."}
            
        prompt = f"Titluri de știri din ultimele 48h despre echipa '{team_name}':\n" + "\n".join(titles)
        if not hasattr(self.model, '_system_instruction'):
            prompt = self.system_prompt + "\n\n" + prompt

        try:
            logger.info(f"🧠 Apelare Gemini pentru Psihologia echipei {team_name}...")
            self.last_api_call = time.time()
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
                
            result_json = json.loads(result_text)
            result_json["news_analyzed"] = len(titles)
            
            cache[payload_hash] = result_json
            self._set_cache(cache)
            
            return result_json
        except Exception as e:
            logger.error(f"Eroare Gemini Psychology Crawler: {e}")
            return {
                "veriga_slaba": "Date limitate / Lipsă acces API",
                "nivel_haos": 40,
                "recomandare_tactica": "Datorită limitărilor la procesarea de știri live, ne vom concentra pe menținerea posesiei și evitarea duelurilor la mijloc.",
                "news_analyzed": len(titles),
                "error_encountered": str(e)[:100]
            }

