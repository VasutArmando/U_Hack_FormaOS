import json
import os
import logging
from typing import Dict, List

# Assuming Gemini client is configured similarly to PsychologyBrain
# Reuse the same model via environment variables
from google.generativeai import GenerativeModel

logger = logging.getLogger("strategic_brain")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)

class StrategicBrain:
    """Provides AI‑driven contextual intelligence and predictive analytics.

    1️⃣ **Contextual Intelligence** – compares live match frame data with the
    "Ideal Player Profile" extracted from the U Cluj PDF (pages 14‑19). The PDF
    content is expected to be pre‑processed into a JSON file `ideal_profiles.json`
    located in the project root.

    2️⃣ **Predictive Analytics** – predicts the probability of a formation
    change in the next 5 minutes based on recent events (passes, positions,
    possession speed, defensive density, etc.).

    3️⃣ **Justification** – every recommendation includes a logical explanation
    derived from the raw JSON metrics.
    """

    def __init__(self):
        # Initialise Gemini model; fallback to a mock if API key missing
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            self.model = GenerativeModel("gemini-1.5-pro", system_instruction="You are a tactical analyst for U Cluj. Provide concise JSON output.")
        else:
            logger.warning("Gemini API key missing – using dummy model.")
            self.model = None
        # Load ideal player profiles once
        self.ideal_profiles = self._load_ideal_profiles()

    def _load_ideal_profiles(self) -> Dict:
        """Load the pre‑processed ideal player profiles.
        Expected format:
        {
            "position": {"attributes": {...}},
            ...
        }
        """
        path = os.path.join(os.path.dirname(__file__), "..", "..", "ideal_profiles.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info("Ideal player profiles loaded.")
                return data
        except Exception as e:
            logger.error(f"Failed to load ideal profiles: {e}")
            return {}

    # ---------------------------------------------------------------------
    # 1️⃣ Contextual Intelligence
    # ---------------------------------------------------------------------
    def contextual_intelligence(self, live_frame: Dict) -> Dict:
        """Compare live frame data with ideal profiles.
        Returns a dict with similarity scores per position and a short narrative.
        """
        if not self.model:
            return {"error": "Gemini model unavailable"}
        prompt = self._build_contextual_prompt(live_frame)
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Gemini contextual failure: {e}")
            return {"error": str(e)}

    def _build_contextual_prompt(self, live_frame: Dict) -> str:
        """Create a Gemini prompt that injects live JSON and ideal profiles.
        The prompt asks Gemini to:
        * compute similarity (0‑100) for each position
        * highlight deviations (e.g., speed, defensive density)
        * output a JSON structure:
          {"similarities": {...}, "insights": "..."}
        """
        ideal_json = json.dumps(self.ideal_profiles, ensure_ascii=False, indent=2)
        live_json = json.dumps(live_frame, ensure_ascii=False, indent=2)
        return (
            "Analizează următoarele date live ale meciului și compară-le cu profilul ideal al jucătorului descris în PDF (pagini 14‑19). "
            "Folosește JSON‑ul ideal și JSON‑ul live furnizat. Pentru fiecare poziție, calculează un scor de similaritate (0‑100) și indică factorii cei mai critici care diferă. "
            "Răspunde strict în format JSON cu câmpurile:\n"
            "  \"similarities\": {position: score},\n"
            "  \"insights\": \"text explicativ concis\".\n"
            f"Ideal Profile JSON:\n{ideal_json}\n"
            f"Live Frame JSON:\n{live_json}\n"
        )

    # ---------------------------------------------------------------------
    # 2️⃣ Predictive Analytics
    # ---------------------------------------------------------------------
    def predict_formation_change(self, recent_events: List[Dict]) -> Dict:
        """Predict probability of formation change using last 5 minutes of events.
        Returns {"probability": <0‑1>, "recommended_formation": "...", "justification": "..."}
        """
        if not self.model:
            return {"error": "Gemini model unavailable"}
        prompt = self._build_predictive_prompt(recent_events)
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Gemini predictive failure: {e}")
            return {"error": str(e)}

    def _build_predictive_prompt(self, recent_events: List[Dict]) -> str:
        events_json = json.dumps(recent_events, ensure_ascii=False, indent=2)
        return (
            "Pe baza ultimelor 5 minute de joc (evenimente, poziții, viteza de posesie, densitatea defensivă) "
            "estimează probabilitatea ca adversarul să schimbe sistemul de joc (ex. din 1‑4‑2‑3‑1 în 1‑4‑4‑2). "
            "Furnizează rezultatul în JSON cu câmpurile:\n"
            "  \"probability\": float între 0 şi 1,\n"
            "  \"recommended_formation\": string,\n"
            "  \"justification\": text scurt bazat pe datele furnizate.\n"
            f"Evenimentele JSON (ultimele 5 minute):\n{events_json}\n"
        )

    # ---------------------------------------------------------------------
    # 3️⃣ Helper – calculate possession speed & defensive density (used in prompts)
    # ---------------------------------------------------------------------
    @staticmethod
    def compute_possession_speed(events: List[Dict]) -> float:
        """Simple heuristic: total distance covered by ball carriers / total time (seconds)."""
        total_dist = 0.0
        total_time = 0.0
        for ev in events:
            if ev.get("type") == "possession":
                total_dist += ev.get("distance_m", 0)
                total_time += ev.get("duration_s", 0)
        return total_dist / total_time if total_time else 0.0

    @staticmethod
    def compute_defensive_density(players: List[Dict]) -> float:
        """Calculate average pair‑wise distance between defending players (lower = higher density)."""
        if len(players) < 2:
            return 0.0
        distances = []
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                p1, p2 = players[i], players[j]
                dx = p1["x"] - p2["x"]
                dy = p1["y"] - p2["y"]
                distances.append((dx ** 2 + dy ** 2) ** 0.5)
        return sum(distances) / len(distances)
