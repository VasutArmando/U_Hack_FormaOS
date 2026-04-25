import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone
from data_manager import DataManager

class NewsCrawler:
    def __init__(self):
        self.keywords = ['scandal', 'accidentat', 'conferinta', 'demisie', 'tensiune', 'bataie', 'transfer', 'exclus', 'accidentare', 'criticat', 'nervos', 'greseala']
        self.data_manager = DataManager()

    def fetch_superliga_news(self, team_name: str) -> list:
        # Codare URL pentru Google News RSS
        query = urllib.parse.quote(f"{team_name} superliga romania")
        url = f"https://news.google.com/rss/search?q={query}&hl=ro&gl=RO&ceid=RO:ro"
        
        feed = feedparser.parse(url)
        recent_news = []
        
        now = datetime.now(timezone.utc)
        time_limit = now - timedelta(hours=48)
        
        for entry in feed.entries:
            try:
                # Din experiența cu feedparser, published_parsed poate fi folosit, sau parsăm manual
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                    if dt < time_limit:
                        continue
            except Exception:
                pass # Dacă nu se poate parsa, păstrăm știrea
                
            title_lower = entry.title.lower()
            
            # Punctul 7: Filtrare High Relevance dupa numele jucatorului din baza de date
            is_high_relevance = False
            for player in self.data_manager.players.values():
                if player.name and len(player.name) > 3 and player.name.lower() in title_lower:
                    is_high_relevance = True
                    break

            # Căutăm cuvintele cheie
            if any(kw in title_lower for kw in self.keywords) or is_high_relevance:
                recent_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "relevance": "High Relevance" if is_high_relevance else "Normal"
                })
        # After processing all entries, sort by relevance (High first) and limit to 5 items
        recent_news.sort(key=lambda x: 0 if x["relevance"] == "High Relevance" else 1)
        return recent_news[:5]

def get_superliga_news(team_name: str) -> list:
    """
    Funcție standalone cerută pentru Modulul Psihologic.
    Citește RSS, curăță textul de caractere speciale, 
    filtrează pe ultimele 48h și returnează o listă curată de dicționare.
    """
    from bs4 import BeautifulSoup
    import urllib.parse
    import time
    from datetime import datetime, timedelta, timezone
    import feedparser
    import re
    
    query = urllib.parse.quote(f"{team_name} superliga romania")
    url = f"https://news.google.com/rss/search?q={query}&hl=ro&gl=RO&ceid=RO:ro"
    
    feed = feedparser.parse(url)
    keywords = ['accidentat', 'scandal', 'conferinta', 'suspendat', 'nervos']
    
    now = datetime.now(timezone.utc)
    time_limit = now - timedelta(hours=48)
    
    processed_news = []
    
    for entry in feed.entries:
        pub_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
            
        if pub_date and pub_date < time_limit:
            continue
            
        title = entry.title
        # Curățăm eventualele tag-uri HTML cu BeautifulSoup
        clean_title = BeautifulSoup(title, "html.parser").get_text()
        # Eliminăm caracterele speciale conform cerinței Data Scientist (păstrăm alfanumerice și punctuație bază)
        clean_title = re.sub(r'[^\w\s\.\,\!\?-]', '', clean_title)
        
        link = entry.link
        
        is_priority = any(kw in clean_title.lower() for kw in keywords)
        timestamp = pub_date.timestamp() if pub_date else 0
        
        processed_news.append({
            "is_priority": is_priority,
            "timestamp": timestamp,
            "title": clean_title,
            "link": link
        })
        
    # Sortăm: prioritare primele, apoi cronologic cele mai recente
    processed_news.sort(key=lambda x: (not x["is_priority"], -x["timestamp"]))
    
    # Returnăm sub formă de listă curată (dict format)
    return [{"title": item["title"], "link": item["link"]} for item in processed_news]
