import os
import logging
import google.generativeai as genai
from data_manager import DataManager

logger = logging.getLogger("forma_os")

class TacticalIntelligence:
    def __init__(self):
        self.data_manager = DataManager()
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                self.model = None
        else:
            self.model = None

    def generate_half_time_report(self, team_name: str) -> dict:
        summary_events = self.data_manager.get_summary_events()
        
        prompt = (f"Pe baza acestor date din meci: {summary_events}, care sunt cele 3 mari probleme tactice ale adversarului? "
                  f"Corelează asta cu profilul lor psihologic (dacă e disponibil) și generează un raport de pauză (Half-Time Report) de maxim 100 de cuvinte.")

        if not self.model:
            return {
                "report": "Sistem AI indisponibil. Datele arată mingi pierdute în zona proprie. Recomandăm pressing avansat și dublarea marcajului la pivot, adversarul pare destabilizat emoțional."
            }

        try:
            response = self.model.generate_content(prompt)
            return {"report": response.text}
        except Exception as e:
            logger.error(f"Gemini Tactical Error: {e}")
            return {
                "report": "Eroare la generarea raportului tactic. Jucați agresiv pe flancul stâng, adversarul dă semne de epuizare."
            }

    def generate_pre_game_plan(self, team_name: str) -> dict:
        context_env = self.data_manager.get_context_environment()
        context_psy = self.data_manager.get_context_psychology()
        
        prompt = (f"Analizează adversarul {team_name}. Pe baza istoricului general din baza de date și a contextului: Vreme {context_env}, Profil psihologic {context_psy}. "
                  "Generează un plan de meci (Pre-Game Plan) scurt de maxim 100 de cuvinte, dictând abordarea tactică generală.")

        if not self.model:
            return {
                "report": "Plan generic: Formați o linie compactă de 4 la mijloc, condițiile meteo dictează un joc bazat pe posesie lungă și siguranță."
            }

        try:
            response = self.model.generate_content(prompt)
            return {"report": response.text}
        except Exception as e:
            logger.error(f"Gemini Tactical Error: {e}")
            return {
                "report": "Eroare la generare. Plan de siguranță: Abordați meciul cu o defensivă joasă."
            }
