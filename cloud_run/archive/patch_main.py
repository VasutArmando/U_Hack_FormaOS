import sys

with open("d:\\U_Hack\\U_Hack_FormaOS\\cloud_run\\main.py", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find('@app.get("/api/v1/intel/psychology/{team_name}")')
end_idx = content.find('if __name__ == "__main__":')

new_route = """@app.get("/api/v1/intel/psychology/{team_name}")
@limiter.limit("10/minute")
def api_v1_intel_psychology(request: Request, team_name: str):
    \"\"\"
    Contract JSON pentru Frontend (Modulul 8):
    {
      "team": "CFR Cluj",
      "vulnerability_index": 75,
      "targeted_player": "Mario Camora",
      "mental_report": "Echipa este demoralizata.",
      "news_sources": ["http://link1"]
    }
    \"\"\"
    now = time.time()
    
    if team_name in psychology_cache:
        cached_timestamp, cached_report = psychology_cache[team_name]
        if now - cached_timestamp < 1800:
            logger.info(f"⚡ API Cache Hit pentru echipa: {team_name} (Economisire tokeni Gemini)")
            return cached_report
            
    try:
        logger.info(f"🔍 Nu există cache valid. Pornim Crawler-ul RSS pentru {team_name}...")
        news_list = get_superliga_news(team_name)
    except Exception as e:
        logger.error(f"Eroare externă la Google News Crawler: {e}")
        news_list = []
    
    try:
        logger.info(f"🧠 Trimitem știrile curățate către Gemini PsychologyBrain...")
        report = psychology_brain.analyze_team_vulnerabilities(news_list)
    except Exception as e:
        logger.error(f"Eroare critică la apelul Gemini (sau fallback): {e}")
        report = {
            "vulnerability_index": 50,
            "targeted_player": "Nespecificat",
            "mental_report": "Sistem Intel Indisponibil"
        }
    
    final_response = {
        "team": team_name,
        "vulnerability_index": report.get("vulnerability_index", 50),
        "targeted_player": report.get("targeted_player", "Nespecificat"),
        "mental_report": report.get("mental_report", "Eroare extracție"),
        "news_sources": [n["link"] for n in news_list] if isinstance(news_list, list) else []
    }
    
    # Salvăm rezultatul în memoria cache
    psychology_cache[team_name] = (now, final_response)
    
    return final_response

"""

new_content = content[:start_idx] + new_route + content[end_idx:]

with open("d:\\U_Hack\\U_Hack_FormaOS\\cloud_run\\main.py", "w", encoding="utf-8") as f:
    f.write(new_content)
