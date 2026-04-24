import feedparser
import urllib.parse
from datetime import datetime, timedelta, timezone

class NewsCrawler:
    def __init__(self):
        self.keywords = ['scandal', 'accidentat', 'conferinta', 'demisie', 'tensiune', 'bataie', 'transfer', 'exclus', 'accidentare', 'criticat', 'nervos', 'greseala']

    def fetch_latest_news(self, team_name: str) -> list:
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
            # Căutăm cuvintele cheie
            if any(kw in title_lower for kw in self.keywords):
                recent_news.append({
                    "title": entry.title,
                    "link": entry.link
                })
        
        return recent_news
