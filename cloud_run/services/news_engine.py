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

def fetch_opponent_news(opponent_name: str = "Adversar U Cluj") -> List[str]:
    """Extrage titluri recente din Google News despre adversar."""
    query = urllib.parse.quote(f"{opponent_name} fotbal accidentare OR transfer OR antrenor")
    url = f"https://news.google.com/rss/search?q={query}&hl=ro&gl=RO&ceid=RO:ro"
    titles = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            for item in root.findall('.//item'):
                title = item.find('title')
                if title is not None and title.text:
                    titles.append(title.text)
                if len(titles) >= 10:
                    break
    except Exception as e:
        print(f"Error fetching news: {e}")
        # Fallback news for hackathon demonstration
        titles = [
            "Probleme de lot pentru adversari, Popescu a ratat ultimul antrenament acuzând dureri",
            "Scandal în vestiar după ultima înfrângere, moralul echipei la pământ",
            "Ionescu Marian ezită în apărare, criticat de antrenor"
        ]
    return titles

def generate_pregame_intelligence(db_data: List[Dict[str, Any]], opponent_name: str = "Adversar") -> List[Dict[str, Any]]:
    """Integrează GDG DB + News pentru a identifica 'veriga slabă' cu Gemini."""
    news_titles = fetch_opponent_news(opponent_name)
    
    if not GOOGLE_API_KEY:
        # Fallback dacă nu e cheia adăugată, mapăm direct db_data
        for p in db_data:
            p["overall_weakness_score"] = float(p.get("weakness_score", 0))
        return db_data

    prompt = f"""Ești Principal AI Architect la U Cluj. Ai datele biometrice pregame {json.dumps(db_data)} și știrile recente: {json.dumps(news_titles)}.
Identifică 'veriga slabă' din echipa adversă pe baza moralului și a accidentărilor. Mărește 'overall_weakness_score' pentru jucătorul cel mai afectat emoțional sau fizic din știri.
Returnează o listă pură JSON de jucători, fiecare cu câmpurile: id, name, physical_state, psychological_state, overall_weakness_score."""
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
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
