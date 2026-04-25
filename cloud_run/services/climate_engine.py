"""
climate_engine.py — Player Nationality × Match Weather Climate Disadvantage Engine

Maps each player's birth country (from players.json birthArea) to a Köppen macro
climate zone, then evaluates physiological disadvantage against match-day weather.
No AI needed here — pure deterministic rules. Results are passed to Gemini as context.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Country → Köppen macro-zone mapping
# Covers all nationalities present in the SuperLiga dataset.
# Zones: Tropical, Subtropical, Temperate, Cold/Continental, Arid, Nordic
# ---------------------------------------------------------------------------

COUNTRY_CLIMATE_MAP: Dict[str, str] = {
    # Romania and near-neighbours → Temperate/Continental
    "Romania": "Temperate",
    "Moldova": "Temperate",
    "Ukraine": "Cold/Continental",
    "Hungary": "Temperate",
    "Slovakia": "Temperate",
    "Czech Republic": "Temperate",
    "Poland": "Temperate",
    "Bulgaria": "Temperate",
    "Serbia": "Temperate",
    "Croatia": "Temperate",
    "Bosnia-Herzegovina": "Temperate",
    "Bosnia and Herzegovina": "Temperate",
    "Slovenia": "Temperate",
    "North Macedonia": "Temperate",
    "Albania": "Temperate",
    "Kosovo": "Temperate",
    "Montenegro": "Temperate",
    "Greece": "Subtropical",
    "Turkey": "Subtropical",
    "Cyprus": "Subtropical",

    # Western Europe → Temperate / Subtropical
    "France": "Temperate",
    "Germany": "Temperate",
    "Austria": "Temperate",
    "Switzerland": "Temperate",
    "Belgium": "Temperate",
    "Netherlands": "Temperate",
    "Luxembourg": "Temperate",
    "United Kingdom": "Temperate",
    "Ireland": "Temperate",
    "Portugal": "Subtropical",
    "Spain": "Subtropical",
    "Italy": "Subtropical",
    "Malta": "Subtropical",

    # Nordic → Nordic
    "Norway": "Nordic",
    "Sweden": "Nordic",
    "Finland": "Nordic",
    "Denmark": "Nordic",
    "Iceland": "Nordic",

    # Eastern Europe / Caucasus
    "Russia": "Cold/Continental",
    "Belarus": "Cold/Continental",
    "Lithuania": "Cold/Continental",
    "Latvia": "Cold/Continental",
    "Estonia": "Cold/Continental",
    "Georgia": "Temperate",
    "Armenia": "Cold/Continental",
    "Azerbaijan": "Cold/Continental",
    "Kazakhstan": "Arid",

    # Sub-Saharan Africa → Tropical
    "Nigeria": "Tropical",
    "Ghana": "Tropical",
    "Senegal": "Tropical",
    "Ivory Coast": "Tropical",
    "Côte d'Ivoire": "Tropical",
    "Cameroon": "Tropical",
    "Mali": "Tropical",
    "Guinea": "Tropical",
    "Guinea-Bissau": "Tropical",
    "Burkina Faso": "Tropical",
    "Togo": "Tropical",
    "Benin": "Tropical",
    "Sierra Leone": "Tropical",
    "Liberia": "Tropical",
    "Congo": "Tropical",
    "DR Congo": "Tropical",
    "Angola": "Tropical",
    "Mozambique": "Tropical",
    "Tanzania": "Tropical",
    "Kenya": "Tropical",
    "Uganda": "Tropical",
    "Ethiopia": "Tropical",
    "Rwanda": "Tropical",
    "Zambia": "Tropical",
    "Zimbabwe": "Tropical",
    "Gabon": "Tropical",

    # North Africa → Arid / Subtropical
    "Morocco": "Subtropical",
    "Algeria": "Arid",
    "Tunisia": "Subtropical",
    "Egypt": "Arid",
    "Libya": "Arid",

    # Middle East → Arid
    "Saudi Arabia": "Arid",
    "Iraq": "Arid",
    "Iran": "Arid",
    "Jordan": "Arid",
    "Lebanon": "Subtropical",
    "Syria": "Arid",
    "Israel": "Subtropical",

    # South America → Tropical / Subtropical
    "Brazil": "Tropical",
    "Colombia": "Tropical",
    "Venezuela": "Tropical",
    "Ecuador": "Tropical",
    "Peru": "Tropical",
    "Bolivia": "Tropical",
    "Paraguay": "Subtropical",
    "Argentina": "Subtropical",
    "Uruguay": "Subtropical",
    "Chile": "Subtropical",

    # Central America & Caribbean → Tropical
    "Mexico": "Tropical",
    "Cuba": "Tropical",
    "Jamaica": "Tropical",
    "Haiti": "Tropical",
    "Dominican Republic": "Tropical",
    "Costa Rica": "Tropical",

    # North America
    "United States": "Temperate",
    "Canada": "Cold/Continental",

    # Asia
    "Japan": "Subtropical",
    "South Korea": "Temperate",
    "China": "Temperate",
    "India": "Tropical",
    "Pakistan": "Arid",
    "Bangladesh": "Tropical",

    # Cape Verde / Island nations
    "Cape Verde": "Arid",
    "Cape Verdean": "Arid",
}

# Default for unmapped countries (Romania is host → assume Temperate is fine)
DEFAULT_ZONE = "Temperate"


def get_player_climate_zone(birth_country: str) -> str:
    """Return the Köppen macro-zone for a birth country."""
    if not birth_country or birth_country in ("Unknown", ""):
        return DEFAULT_ZONE
    return COUNTRY_CLIMATE_MAP.get(birth_country, DEFAULT_ZONE)


# ---------------------------------------------------------------------------
# Disadvantage assessment rules
# ---------------------------------------------------------------------------

def assess_climate_disadvantage(player_zone: str, match_weather: dict) -> dict:
    """
    Deterministic rule engine — no AI.
    Returns: { "disadvantaged": bool, "severity": str, "reason": str }
    """
    temp = match_weather.get("temperature", 15.0)
    condition = match_weather.get("condition", "Clear").lower()
    humidity = match_weather.get("humidity", 50)
    wind = match_weather.get("wind_speed", 5.0)

    is_rain = "rain" in condition or "drizzle" in condition
    is_snow = "snow" in condition
    is_cold = temp < 10.0
    is_very_cold = temp < 5.0
    is_hot = temp > 28.0
    is_very_hot = temp > 33.0
    is_humid = humidity > 80
    is_windy = wind > 12.0

    # --- Tropical players in cold/wet conditions ---
    if player_zone == "Tropical":
        if is_very_cold or is_snow:
            return {
                "disadvantaged": True,
                "severity": "High",
                "reason": f"Jucător din climă tropicală expus la {temp:.0f}°C{' și ninsoare' if is_snow else ''}. Risc ridicat de reactivitate musculară scăzută și rigiditate.",
            }
        if is_cold and (is_rain or is_windy):
            return {
                "disadvantaged": True,
                "severity": "High",
                "reason": f"Jucător tropical la {temp:.0f}°C cu {'ploaie' if is_rain else 'vânt puternic'} ({wind:.0f} m/s). Dificultăți de adaptare la umiditate și frig.",
            }
        if is_cold:
            return {
                "disadvantaged": True,
                "severity": "Medium",
                "reason": f"Climă natală tropicală vs {temp:.0f}°C la meci. Posibilă reducere a performanței musculare.",
            }

    # --- Nordic players in hot/humid conditions ---
    if player_zone == "Nordic":
        if is_very_hot and is_humid:
            return {
                "disadvantaged": True,
                "severity": "High",
                "reason": f"Jucător nordic expus la {temp:.0f}°C și umiditate {humidity}%. Risc de supraîncălzire și oboseală prematură.",
            }
        if is_hot:
            return {
                "disadvantaged": True,
                "severity": "Medium",
                "reason": f"Jucător din climă nordică la {temp:.0f}°C — temperatură neobișnuită față de climatul natal.",
            }

    # --- Arid-zone players in cold/wet conditions ---
    if player_zone == "Arid":
        if is_rain and is_cold:
            return {
                "disadvantaged": True,
                "severity": "Medium",
                "reason": f"Jucător din climă aridă expus la ploaie și {temp:.0f}°C. Dificultăți de adaptare la umiditate ridicată.",
            }
        if is_rain:
            return {
                "disadvantaged": True,
                "severity": "Low",
                "reason": f"Climă natală aridă vs condiții ploioase. Teren alunecos poate fi mai dificil de gestionat.",
            }

    # --- Cold/Continental players in extreme heat ---
    if player_zone == "Cold/Continental":
        if is_very_hot and is_humid:
            return {
                "disadvantaged": True,
                "severity": "Medium",
                "reason": f"Jucător din climă continentală rece la {temp:.0f}°C cu umiditate {humidity}%.",
            }

    # --- No significant disadvantage ---
    return {
        "disadvantaged": False,
        "severity": "None",
        "reason": "",
    }


# ---------------------------------------------------------------------------
# Context builder for Gemini prompt
# ---------------------------------------------------------------------------

def build_climate_context_for_prompt(players_with_climate: List[Dict]) -> str:
    """
    Returns a compact string summarising climate disadvantages for the Gemini prompt.
    Only includes players with severity != 'None' to keep the prompt tight.
    """
    lines = []
    for p in players_with_climate:
        assessment = p.get("_climate_assessment", {})
        if assessment.get("severity", "None") == "None":
            continue
        name = p.get("name", "Unknown")
        country = p.get("birth_country", "Unknown")
        zone = p.get("_climate_zone", "Unknown")
        severity = assessment.get("severity", "None")
        reason = assessment.get("reason", "")
        lines.append(f"- {name} (din {country}, zonă {zone}): [{severity}] {reason}")

    if not lines:
        return "Nu există dezavantaje climatice semnificative pentru jucătorii adversarului în condițiile meteo ale meciului."

    header = f"DEZAVANTAJE CLIMATICE IDENTIFICATE ({len(lines)} jucători):\n"
    return header + "\n".join(lines)
