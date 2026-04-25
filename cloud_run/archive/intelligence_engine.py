import os
import json
import logging
import hashlib
import time
import google.generativeai as genai

logger = logging.getLogger("forma_os")

# Parse .env manually to avoid extra dependencies like python-dotenv
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

load_env()

API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)

class TacticalBrain:
    def __init__(self):
        # System Prompt defining the persona of Ioan Ovidiu Sabău
        self.system_prompt = """Ești Ioan Ovidiu Sabău, antrenorul principal al FC Universitatea Cluj.
Personalitatea ta: Analitic, calm, respectuos dar exigent, axat pe disciplină tactică.
Filosofia ta: Posesie progresivă și exploatarea spațiilor libere (half-spaces).
Regula ta de Aur: Fii extrem de concis. Răspunde cu MAXIM 150 de cuvinte per total. Timpul este critic pe bancă.
Toate răspunsurile tale TREBUIE să fie în format JSON strict (fără block-uri de markdown)."""
        
        # Folosim gemini-1.5-flash conform cerințelor de arhitectură pentru eficiență cost/viteză
        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=self.system_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception:
            self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.cache_file = os.path.join(os.path.dirname(__file__), 'ai_cache.json')
        self.last_api_call = 0.0
        self.rate_limit_seconds = 10.0

    def _get_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _set_cache(self, cache_data: dict):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Eroare scriere cache AI: {e}")

    def _truncate_data(self, data: dict) -> dict:
        """ Truncate data to avoid massive token consumption """
        data_str = json.dumps(data)
        if len(data_str) > 1500:
            return {"truncated_data": data_str[:1500] + "... [TRUNCATED FOR TOKEN LIMIT]"}
        return data

    def generate_report(self, context_data: dict, report_type: str) -> dict:
        if not API_KEY:
            logger.warning("No GOOGLE_API_KEY found, using mock intelligence.")
            return self._get_mock_response(report_type)

        # Truncate context to save input tokens
        truncated_context = self._truncate_data(context_data)
        
        # Create a unique hash for this payload
        payload_str = json.dumps({"type": report_type, "data": truncated_context}, sort_keys=True)
        payload_hash = hashlib.md5(payload_str.encode('utf-8')).hexdigest()

        # Caching logic
        cache = self._get_cache()
        if payload_hash in cache:
            logger.info("🧠 AI Cache HIT! Evităm un apel API costisitor către Gemini.")
            return cache[payload_hash]

        # Rate Limiting Logic
        now = time.time()
        time_since_last_call = now - self.last_api_call
        if time_since_last_call < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - time_since_last_call
            logger.warning(f"⏳ Rate Limit activ. Se cere așteptarea a {wait_time:.1f} secunde.")
            return {"error": f"Rate limit activ. Te rog așteaptă {wait_time:.1f} sec.", "status": "rate_limited"}

        # Perform the actual generation
        try:
            self.last_api_call = time.time()
            prompt = self._build_prompt(truncated_context, report_type)
            
            if not hasattr(self.model, '_system_instruction'):
                 prompt = self.system_prompt + "\n\n" + prompt

            logger.info(f"🧠 Apelare Gemini (gemini-1.5-flash) pentru raportul: {report_type}...")
            response = self.model.generate_content(prompt)
            
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
                
            result_json = json.loads(result_text)
            
            # Save to Cache
            cache[payload_hash] = result_json
            self._set_cache(cache)
            
            return result_json
            
        except Exception as e:
            logger.error(f"Eroare Generative AI: {e}")
            return self._get_mock_response(report_type)

    def _build_prompt(self, context_data: dict, report_type: str) -> str:
        data_str = json.dumps(context_data, indent=2)
        
        if report_type == 'pre-game':
            return f"""Analizează următoarele date pre-meci limitate: {data_str}.
Creează un 'Starting Plan' și instrucțiuni pentru atacantul pivot. Răspunde Scurt (max 150 cuvinte).
Structura JSON cerută:
{{
  "title": "Plan Tactic Pre-Meci",
  "key_objectives": ["obiectiv 1", "obiectiv 2", "obiectiv 3"],
  "pivot_instructions": "Instrucțiuni scurte pentru atacant",
  "intensity": "High/Medium/Low"
}}"""
        elif report_type == 'half-time':
            return f"""Analizează statisticile trunchiate din prima repriză: {data_str}.
Identifică 3 puncte slabe ale adversarului și propune o schimbare tactică necesară (max 150 cuvinte).
Structura JSON cerută:
{{
  "title": "Analiză la Pauză",
  "opponent_weaknesses": ["Punct 1", "Punct 2", "Punct 3"],
  "tactical_adjustment": "Schimbare scurtă și la obiect"
}}"""
        elif report_type == 'real-time':
            return f"""Avem următorul eveniment LIVE din tracking: {data_str}.
Generează o alertă tactică ultra-scurtă de pe bancă.
Structura JSON cerută:
{{
  "alert_type": "URGENT | INFO | TACTICAL",
  "message": "ATACĂ ACUM: [mesaj ultra-scurt de 1-2 propoziții]",
  "target_zone": "Ex: Flancul drept"
}}"""
        else:
            return '{"error": "Unknown report type"}'

    def _get_mock_response(self, report_type: str) -> dict:
        if report_type == 'pre-game':
            return {
                "title": "Plan Tactic Pre-Meci (MOCK)",
                "key_objectives": ["Presing avansat", "Construcție mijloc", "Extrema dreaptă"],
                "pivot_instructions": "Coboară între linii.",
                "intensity": "High"
            }
        elif report_type == 'half-time':
            return {
                "title": "Analiză la Pauză (MOCK)",
                "opponent_weaknesses": ["Fundaș stânga spațiu", "Închizător vulnerabil", "Tranziție lentă"],
                "tactical_adjustment": "Mutați atacurile pe flancul stâng."
            }
        elif report_type == 'real-time':
            return {
                "alert_type": "URGENT",
                "message": "ATACĂ ACUM: Fundașul lor stânga e complet obosit!",
                "target_zone": "Flancul stâng ofensiv"
            }
        return {"error": "Invalid report_type"}
