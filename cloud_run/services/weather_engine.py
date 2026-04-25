"""
weather_engine.py — Match-Day Weather Intelligence
Fetches current OR forecasted conditions from OpenWeatherMap using
stadium lat/lng coordinates stored in stadiums.json.
"""

import os
import json
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("forma_os_weather")

BASE_DATA_PATH = Path(__file__).parent.parent / "data"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_snapshot(temp: float, condition: str, humidity: int, wind_speed: float, note: str = "") -> dict:
    return {
        "temperature": round(temp, 1),
        "condition": condition,
        "humidity": humidity,
        "wind_speed": round(wind_speed, 1),
        "forecast_note": note,
    }


def _fallback(note: str = "Fallback: API unavailable") -> dict:
    return _build_snapshot(12.0, "Rain", 85, 15.0, note)


# ---------------------------------------------------------------------------
# Current weather (used when no match date is set, or forecast window exceeded)
# ---------------------------------------------------------------------------

def get_live_weather(lat: float = None, lng: float = None, city: str = None) -> dict:
    """Fetch current weather. Accepts lat/lng (preferred) or city name (legacy)."""
    if not OPENWEATHER_API_KEY:
        return _fallback("Fallback: OPENWEATHER_API_KEY not set")

    if lat is not None and lng is not None:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
    elif city:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
    else:
        return _fallback("Fallback: no location specified")

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        d = r.json()
        return _build_snapshot(
            temp=d["main"]["temp"],
            condition=d["weather"][0]["main"],
            humidity=d["main"]["humidity"],
            wind_speed=d["wind"]["speed"],
            note="Current conditions",
        )
    except Exception as e:
        logger.warning(f"get_live_weather error: {e}")
        return _fallback("Fallback: current weather fetch failed")


# ---------------------------------------------------------------------------
# Forecast weather (for match-day prediction, up to 5 days ahead)
# ---------------------------------------------------------------------------

def get_forecast_for_match(lat: float, lng: float, match_datetime: datetime) -> dict:
    """
    Return the OpenWeatherMap 3-hour forecast slot closest to match_datetime.
    Falls back to current weather if the date is beyond the 5-day window.
    """
    if not OPENWEATHER_API_KEY:
        return _fallback("Fallback: OPENWEATHER_API_KEY not set")

    # OWM /forecast gives up to ~40 slots (5 days × 8 per day)
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        slots = data.get("list", [])

        if not slots:
            return get_live_weather(lat=lat, lng=lng)

        # Make match_datetime timezone-aware (UTC) for comparison
        if match_datetime.tzinfo is None:
            match_datetime = match_datetime.replace(tzinfo=timezone.utc)

        best_slot = None
        best_diff = float("inf")

        for slot in slots:
            slot_dt = datetime.fromtimestamp(slot["dt"], tz=timezone.utc)
            diff = abs((slot_dt - match_datetime).total_seconds())
            if diff < best_diff:
                best_diff = diff
                best_slot = slot

        if best_slot is None:
            return get_live_weather(lat=lat, lng=lng)

        match_local = match_datetime.strftime("%Y-%m-%d %H:%M UTC")
        return _build_snapshot(
            temp=best_slot["main"]["temp"],
            condition=best_slot["weather"][0]["main"],
            humidity=best_slot["main"]["humidity"],
            wind_speed=best_slot["wind"]["speed"],
            note=f"Forecast for match day ({match_local})",
        )

    except Exception as e:
        logger.warning(f"get_forecast_for_match error: {e}")
        return get_live_weather(lat=lat, lng=lng)


# ---------------------------------------------------------------------------
# Stadium helper — reads lat/lng from stadiums.json
# ---------------------------------------------------------------------------

def get_stadium_coords(stadium_id: str) -> dict:
    """Return {'lat': float, 'lng': float, 'city': str} for a given stadium id."""
    stadiums_path = BASE_DATA_PATH / "stadiums.json"
    try:
        with open(stadiums_path, "r", encoding="utf-8") as f:
            stadiums = json.load(f)
        for s in stadiums:
            if s.get("id") == stadium_id:
                return {
                    "lat": s.get("lat"),
                    "lng": s.get("lng"),
                    "city": s.get("city", ""),
                    "name": s.get("name", ""),
                }
    except Exception as e:
        logger.error(f"get_stadium_coords error: {e}")
    return {"lat": None, "lng": None, "city": "", "name": ""}


# ---------------------------------------------------------------------------
# Legacy name-based helper (kept so main.py assistant endpoint still works)
# ---------------------------------------------------------------------------

def get_city_for_stadium(stadium_name: str) -> str:
    """Legacy fallback: name → city string. Prefer get_stadium_coords() for new code."""
    stadiums_path = BASE_DATA_PATH / "stadiums.json"
    try:
        with open(stadiums_path, "r", encoding="utf-8") as f:
            stadiums = json.load(f)
        for s in stadiums:
            if s.get("name", "").lower() in stadium_name.lower() or stadium_name.lower() in s.get("name", "").lower():
                return s.get("city", "Cluj-Napoca")
    except Exception:
        pass
    return "Cluj-Napoca"


# ---------------------------------------------------------------------------
# Tactical processing (unchanged)
# ---------------------------------------------------------------------------

def process_weather_tactics(weather_data: dict) -> dict:
    """Generate AI tactical suggestions from weather (cached to disk)."""
    cache_path = BASE_DATA_PATH / "current_weather_tactics.json"
    fallback = {
        "pitch_condition": "Slippery" if "rain" in weather_data.get("condition", "").lower() else "Normal",
        "impact_on_stamina": "High" if weather_data.get("humidity", 0) > 80 else "Low",
        "tactical_suggestion": "Favorizează șuturile de la distanță" if "rain" in weather_data.get("condition", "").lower() else "Menține posesia.",
    }

    import google.genai as genai2
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    if not GOOGLE_API_KEY:
        return fallback

    prompt = (
        f"Având vremea {json.dumps(weather_data)}, generează un JSON cu: "
        f"pitch_condition (Slippery/Normal), impact_on_stamina (High/Low) și "
        f"tactical_suggestion. Răspunde EXCLUSIV cu JSON pur."
    )
    try:
        client = genai2.Client(api_key=GOOGLE_API_KEY)
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(text)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)
        return parsed
    except Exception as e:
        logger.warning(f"process_weather_tactics AI error: {e}")
        return fallback
