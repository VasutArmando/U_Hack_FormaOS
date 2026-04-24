import os
import json
import logging
import google.generativeai as genai
from .news_repository import NewsRepository

logger = logging.getLogger("forma_os")

# Funcție helper pentru încărcarea .env local (la fel ca în intelligence_engine.py)
def load_env_psychology():
    # .env este în cloud_run/, așadar cu 2 niveluri mai sus de cloud_run/services/psychology/
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

class PsychologyEngine:
    """
    Analizează știrile folosind Gemini pentru a deduce profilul psihologic al echipei adverse.
    """
    def __init__(self):
        load_env_psychology()
        self.repository = NewsRepository()
        self.system_prompt = """Ești Ioan Ovidiu Sabău, antrenorul principal al FC Universitatea Cluj.
Avem nevoie de analiza psihologică a echipei adverse pe baza știrilor recente apărute în presă.
Analizează nivelul de presiune (pressure_level), fragilitatea mentală (mental_fragility) și potențialul de agresivitate fizică/duritate (aggression_score).
Răspunde DOAR cu un obiect JSON strict, fără markdown, cu următoarea structură:
{
  "mental_fragility": <int 0-100>,
  "pressure_level": <int 0-100>,
  "aggression_score": <int 0-100>,
  "tactical_insight": "<Scurt insight tactic (max 3 propoziții), în stilul tău calm și axat pe disciplină, despre cum putem profita de aceste stări pe teren.>"
}"""
        
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

    def analyze_opponent_psychology(self, opponent_name: str = "Adversar") -> dict:
        news_data = self.repository.get_latest_news(opponent_name)
        
        if not self.api_key:
            logger.warning("No API Key. Using fallback psychology data.")
            return self._get_fallback()

        prompt = f"Analizează următoarele știri despre {opponent_name}:\n" + json.dumps(news_data, indent=2)
        
        if not hasattr(self.model, '_system_instruction'):
            prompt = self.system_prompt + "\n\n" + prompt

        try:
            logger.info("🧠 Analiză Psihologică prin Gemini...")
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Curățare markdown (în caz de fail la response_mime_type)
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
            
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Eroare Gemini Psychology: {e}")
            return self._get_fallback()
            
    def _get_fallback(self) -> dict:
        return {
            "mental_fragility": 85,
            "pressure_level": 90,
            "aggression_score": 75,
            "tactical_insight": "Atenție la agresivitatea lor în primele 15 minute. Având o fragilitate mentală ridicată cauzată de presiunea conducerii, dacă păstrăm posesia calmă și marcăm devreme, vor ceda psihic."
        }
