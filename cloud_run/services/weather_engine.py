import os
import json
import requests
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DATA_PATH = Path(__file__).parent.parent / "data"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def get_city_for_stadium(stadium_name: str) -> str:
    mapping = {
        "Arena Nationala": "Bucharest",
        "Stadionul Dr. Constantin Radulescu": "Cluj-Napoca",
        "Stadionul Ion Oblemenco": "Craiova",
        "Stadionul Viitorul (Academia Hagi)": "Ovidiu",
        "Superbet Arena - Giulesti": "Bucharest",
        "Sepsi Arena": "Sfantu Gheorghe",
        "Cluj Arena": "Cluj-Napoca",
        "Stadionul Ilie Oana": "Ploiesti",
        "Stadionul Municipal (Sibiu)": "Sibiu",
        "Stadionul Francisc von Neuman": "Arad",
        "Stadionul Arcul de Triumf": "Bucharest",
        "Stadionul Emil Alexandrescu": "Iasi",
        "Stadionul Otelul": "Galati"
    }
    return mapping.get(stadium_name, "Cluj-Napoca")

def get_live_weather(city: str) -> dict:
    if not OPENWEATHER_API_KEY:
        # Fallback de siguranță pentru demo dacă cheia nu este adăugată
        return {
            "temperature": 12,
            "condition": "Rain",
            "humidity": 85,
            "wind_speed": 15.0
        }
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data.get("main", {}).get("temp", 0),
            "condition": data.get("weather", [{}])[0].get("main", "Clear"),
            "humidity": data.get("main", {}).get("humidity", 0),
            "wind_speed": data.get("wind", {}).get("speed", 0)
        }
    except Exception as e:
        # Fallback la condiții de ploaie pentru a declanșa logica demo-ului
        return {
            "temperature": 12,
            "condition": "Rain",
            "humidity": 88,
            "wind_speed": 15.0
        }

def process_weather_tactics(weather_data: dict) -> dict:
    cache_path = BASE_DATA_PATH / "current_weather_tactics.json"
    
    # Răspuns de fallback dacă nu avem cheie
    fallback_response = {
        "pitch_condition": "Slippery",
        "impact_on_stamina": "High",
        "tactical_suggestion": "Favorizează șuturile de la distanță"
    }
    
    if not GOOGLE_API_KEY:
        return fallback_response
        
    prompt = f"""Având vremea {json.dumps(weather_data)}, generează un JSON cu: pitch_condition (Slippery/Normal), impact_on_stamina (High/Low) și tactical_suggestion (ex: "Favorizează șuturile de la distanță" sau "Atenție la alunecări"). Formatul trebuie să fie un obiect JSON pur."""
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Curățare parsare markdown JSON
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        parsed_data = json.loads(text.strip())
        
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            
        return parsed_data
    except Exception as e:
        print(f"Eroare procesare AI: {e}")
        return fallback_response
