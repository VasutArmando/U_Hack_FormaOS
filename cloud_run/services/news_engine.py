import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import google.generativeai as genai
from typing import List, Dict, Any

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def fetch_news(query_term: str, is_player: bool = False, max_results: int = 5) -> List[str]:
    """Extrage titluri recente din Google News despre un termen (echipa sau jucator)."""
    if is_player:
        query_str = f'"{query_term}" fotbal (accidentare OR transfer OR criticat)'
    else:
        query_str = f'"{query_term}" fotbal (antrenor OR meci OR transfer)'
    
    query = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={query}&hl=ro&gl=RO&ceid=RO:ro"
    titles = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.find('title')
                if title is not None and title.text:
                    titles.append(title.text)
                if len(titles) >= max_results:
                    break
    except Exception as e:
        print(f"Error fetching news for {query_term}: {e}")
    return titles

def generate_pregame_intelligence(db_data: List[Dict[str, Any]], opponent_name: str = "Adversar") -> List[Dict[str, Any]]:
    """Integrează GDG DB + News pentru a identifica 'veriga slabă' cu Gemini."""
    
    # 1. Extrage nume jucatori si cauta stiri pt fiecare
    player_news_context = {}
    for p in db_data:
        p_name = p.get('name', 'Unknown')
        if p_name != 'Unknown' and not p_name.startswith('Player'):
            player_news_context[p_name] = fetch_news(p_name, is_player=True, max_results=2)
            
    # Stiri generale despre echipa
    team_news = fetch_news(opponent_name, is_player=False, max_results=5)
    
    if not GOOGLE_API_KEY:
        for p in db_data:
            p["overall_weakness_score"] = float(p.get("weakness_score", 50))
        return db_data

    prompt = f"""Ești Principal AI Architect la echipa de fotbal U Cluj. 
Ai primit DATELE BRUTE de performanță (match stats) pentru anumiți jucători ai adversarului {opponent_name}:
{json.dumps(db_data)}

Știrile recente specifice pentru acești jucători:
{json.dumps(player_news_context)}

Știrile generale despre echipa adversă:
{json.dumps(team_news)}

SARCINĂ:
1. Analizează statisticile brute (ex: total_minutes ridicat = oboseală).
2. Integrează știrile individuale ale fiecărui jucător (dacă se menționează accidentări, formă slabă).
3. Analizează tiparele de joc.
4. Generează o analiză tactică în ROMÂNĂ pentru fiecare jucător.
5. Calculează 'overall_weakness_score' (0-100).

Returnează un obiect JSON pur (listă) cu formatul exact:
[
  {{
    "id": "player_id",
    "name": "Nume Jucător (din datele brute)",
    "physical_state": "Analiză stare fizică în română",
    "psychological_state": "Analiză stare mentală în română",
    "tactical_tendencies": "Tendințe tactice",
    "overall_weakness_score": numeric_value
  }}
]"""
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash") # Use 1.5 Flash
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"Pregame Gemini Error: {e}")
        for p in db_data:
            p["overall_weakness_score"] = float(p.get("weakness_score", 0))
        return db_data
