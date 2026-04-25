import os
import json
import asyncio
import random
import google.generativeai as genai
from typing import Dict, Any, List
from .observer_pattern import Subject

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class StadiumVisionService(Subject):
    """
    Simulează integrarea cu camerele de pe stadion.
    Folosește Vertex AI (Gemini Pro Vision simulat) pentru a detecta așezarea tactică și oboseala.
    """
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.latest_vision_data = {
            "gaps": [],
            "fatigue_metrics": {}
        }
        
    async def start_camera_stream(self):
        self.is_running = True
        while self.is_running:
            # Simulează preluarea unui frame la fiecare 10 secunde
            await asyncio.sleep(10)
            self._process_frame_with_vertex_ai()

    def stop_camera_stream(self):
        self.is_running = False

    def _process_frame_with_vertex_ai(self):
        """Simularea unui apel către Vertex AI (Gemini 1.5 Pro Vision) pe marginea unui frame."""
        # Aici s-ar trimite imaginea base64. În hackathon trimitem context text.
        prompt = """Analizează acest cadru vizual (simulat). Identifică interstițiile (găurile) din apărarea adversă 
care ar favoriza stilul nostru de contraatac (U Cluj Relevance). Estimează de asemenea rata de sprint pentru a calcula oboseala (lateralului).
Returnează un JSON cu:
- gaps: listă de găuri (id, location, description, severity, coordinates {x, y, w, h})
- fatigue_metrics: dict cu id jucător și valoare oboseală (0-100) și sprint_drop.
Prioritizează interstițiile pentru contraatac."""

        if not GOOGLE_API_KEY:
            self._apply_fallback_vision()
            return
            
        try:
            model = genai.GenerativeModel("gemini-2.5-flash") # Folosim flash ca placeholder pt vision în hackathon
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith("```json"): text = text[7:]
            elif text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            vision_insight = json.loads(text.strip())
            self.latest_vision_data = vision_insight
            self.notify("VISION_UPDATE", self.latest_vision_data)
        except Exception as e:
            print(f"Vertex AI Vision Error: {e}")
            self._apply_fallback_vision()
            
    def _apply_fallback_vision(self):
        # Fallback Vision Data
        self.latest_vision_data = {
            "gaps": [
                {
                    "id": "v_gap_1",
                    "location": "Right Flank",
                    "description": "Vertex AI: Apărarea adversă a lăsat un spațiu masiv pe contraatac.",
                    "severity": "Critical",
                    "coordinates": {"x": 75.0, "y": 10.0, "w": 40.0, "h": 60.0}
                }
            ],
            "fatigue_metrics": {
                "p2": {"fatigue": 92.0, "sprint_drop": "Sprint speed dropped by 28% in the last 10 minutes (Visual AI)."} # Lateralul Ionescu
            }
        }
        self.notify("VISION_UPDATE", self.latest_vision_data)

# Singleton Instance
vision_pipeline = StadiumVisionService()
