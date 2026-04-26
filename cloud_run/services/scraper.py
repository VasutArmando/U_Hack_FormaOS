"""
scraper.py — Romanian Football News Intelligence Scraper
Sources: GSP.ro (primary), Prosport.ro (secondary), Google News RSS (fallback)

Usage:
    from services.scraper import scrape_opponent_news
    result = scrape_opponent_news("CFR Cluj", ["Cristian Manea", "Dan Petrescu"])
"""

import time
import re
import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

try:
    import requests
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger("forma_os_scraper")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 6  # seconds per HTTP request
INTER_REQUEST_DELAY = 1.0  # seconds between requests (politeness)
MAX_ARTICLE_BODY_LEN = 3000  # characters — enough for Gemini, not too much


# ---------------------------------------------------------------------------
# GSP.ro Scraper
# ---------------------------------------------------------------------------

def _gsp_search_url(query: str) -> str:
    """Primary GSP.ro search URL — /?s= pattern returns 200 with real article listings."""
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.gsp.ro/?s={encoded}"


def _gsp_search_url_v2(query: str) -> str:
    """Alternative GSP.ro search endpoint."""
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.gsp.ro/search?q={encoded}"


def _gsp_tag_url(slug: str) -> str:
    """Fallback tag-based URL for known team names."""
    return f"https://www.gsp.ro/stiri-tag/{slug}.html"


def _team_to_gsp_slug(team_name: str) -> Optional[str]:
    """Map known Romanian team names to their GSP tag slugs."""
    import unicodedata
    
    def _to_ascii(s):
        if not s: return ""
        return "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

    mapping = {
        "CFR Cluj": "cfr-cluj-11098",
        "Universitatea Cluj": "universitatea-cluj-27218",
        "Rapid Bucuresti": "rapid-bucuresti-11099",
        "Dinamo Bucuresti": "dinamo-bucuresti-11097",
        "Farul Constanta": "farul-constanta-11104",
        "Hermannstadt": "hermannstadt-sibiu-31617",
        "Petrolul 52": "petrolul-52-ploiesti-27219",
        "UTA Arad": "uta-arad-11106",
        "Universitatea Craiova": "universitatea-craiova-11102",
        "Otelul": "otelul-galati-11107",
        "Metaloglobus": "metaloglobus-bucuresti-35418",
        "Botosani": "fc-botosani-22014",
        "Csikszereda Miercurea Ciuc": "csikszereda-miercurea-ciuc-32156",
        "Unirea Slobozia": "unirea-slobozia-22015",
        "FCS Bucuresti": "fcsb-11103",
        "Sepsi OSK": "sepsi-osk-sfantu-gheorghe-30335",
        "Poli Iasi": "politehnica-iasi-11105",
        "FC Voluntari": "fc-voluntari-22012",
        "FCU 1948 Craiova": "fc-u-craiova-34444",
        "Gloria Buzau": "gloria-buzau-11101",
        "Chindia Targoviste": "chindia-targoviste-27221",
        "CS Mioveni": "cs-mioveni-11111",
        "FC Arges": "fc-arges-22013",
        "FC Bihor": "fc-bihor-oradea-11112",
        "Concordia Chiajna": "concordia-chiajna-22011"
    }
    
    clean_target = _to_ascii(team_name)
    
    # Try exact match (normalized)
    for key, slug in mapping.items():
        clean_key = _to_ascii(key)
        if clean_key == clean_target:
            return slug
            
    # Try partial match (normalized)
    for key, slug in mapping.items():
        clean_key = _to_ascii(key)
        if clean_key in clean_target or clean_target in clean_key:
            return slug
            
    return None


def _fetch_html(url: str) -> Optional[str]:
    """Fetch raw HTML with retries and politeness."""
    try:
        if BS4_AVAILABLE:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"HTTP {resp.status_code} for {url}")
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
    return None


def _parse_gsp_listing(html: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Parse a GSP.ro search/listing page → list of {title, url, excerpt, date}.
    
    GSP.ro renders article links as plain <a href="...html"> tags throughout the page.
    We collect all unique article links, skip nav/category pages, and return top N.
    """
    if not BS4_AVAILABLE:
        return []

    soup = BeautifulSoup(html, "lxml")
    
    # Remove nav/header/footer noise first
    for noise in soup.find_all(["nav", "header", "footer", "aside"]):
        noise.decompose()

    articles = []
    seen_urls = set()

    # Strategy 1: find <a> tags whose href ends with .html and has a real title
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue
        # Normalise URL
        if href.startswith("/"):
            href = "https://www.gsp.ro" + href
        # Only real article URLs: must have a path segment beyond the domain
        if "gsp.ro" not in href:
            continue
        # Skip pure category/section pages (no article slug)
        url_path = href.replace("https://www.gsp.ro", "").strip("/")
        path_parts = url_path.split("/")
        # Articles usually have 3+ path segments and end in .html
        if not href.endswith(".html") or len(path_parts) < 2:
            continue
        # Skip already seen URLs
        if href in seen_urls:
            continue

        title = a.get_text(strip=True)
        # Strip leading numbering like "2035" that GSP prepends to titles
        title = re.sub(r"^\d{1,4}", "", title).strip()
        if len(title) < 15:
            continue

        seen_urls.add(href)

        # Try to find a date nearby
        date_str = ""
        parent = a.parent
        if parent:
            time_tag = parent.find("time")
            if time_tag:
                date_str = time_tag.get("datetime", "") or time_tag.get_text(strip=True)

        articles.append({
            "title": title,
            "url": href,
            "excerpt": title,   # excerpt = title for listing pages
            "date": date_str,
            "source": "gsp.ro",
        })

        if len(articles) >= max_results:
            break

    return articles


def _parse_article_body(html: str, source: str = "gsp.ro") -> str:
    """Extract clean article body text from a full article page."""
    if not BS4_AVAILABLE:
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "header",
                               "figure", "figcaption", ".ad", ".advertisement"]):
        tag.decompose()

    # Try known selectors first
    selectors = [
        "div.article-content",
        "div.article-body",
        "section.article-body",
        "div.entry-content",
        "div#article-body",
        "div.stire-content",
        "main article",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(separator=" ", strip=True)
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text)
            return text[:MAX_ARTICLE_BODY_LEN]

    # Fallback: largest <div> with text
    best, best_len = "", 0
    for div in soup.find_all("div"):
        t = div.get_text(separator=" ", strip=True)
        if len(t) > best_len and len(t) < 15000:
            best_len = len(t)
            best = t
    return re.sub(r"\s+", " ", best)[:MAX_ARTICLE_BODY_LEN]


def search_gsp(query: str, max_articles: int = 5, fetch_bodies: bool = True) -> List[Dict]:
    """
    Search GSP.ro for news about `query` (team or player name).
    Returns articles with optional full body text.
    """
    if not BS4_AVAILABLE:
        logger.warning("beautifulsoup4 not installed — GSP scraping disabled.")
        return []

    articles = []
    tried_urls = []

    # 1. Try search URL first
    search_url = _gsp_search_url(query)
    tried_urls.append(search_url)
    html = _fetch_html(search_url)
    if html:
        articles = _parse_gsp_listing(html, max_results=max_articles)

    # 2. If no results from search, try tag URL
    if not articles:
        slug = _team_to_gsp_slug(query)
        if slug:
            tag_url = _gsp_tag_url(slug)
            tried_urls.append(tag_url)
            time.sleep(INTER_REQUEST_DELAY)
            html = _fetch_html(tag_url)
            if html:
                articles = _parse_gsp_listing(html, max_results=max_articles)

    logger.info(f"GSP search '{query}': found {len(articles)} articles from {tried_urls}")

    # 3. Fetch article bodies
    if fetch_bodies and articles:
        for article in articles:
            time.sleep(INTER_REQUEST_DELAY)
            body_html = _fetch_html(article["url"])
            if body_html:
                article["body"] = _parse_article_body(body_html, source="gsp.ro")
            else:
                article["body"] = article.get("excerpt", "")

    return articles


# ---------------------------------------------------------------------------
# Prosport.ro Scraper
# ---------------------------------------------------------------------------

def search_prosport(query: str, max_articles: int = 3) -> List[Dict]:
    """Search prosport.ro for news — returns titles + excerpts (no body fetch)."""
    if not BS4_AVAILABLE:
        return []

    url = f"https://www.prosport.ro/?s={urllib.parse.quote(query)}"
    html = _fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    for tag in soup.find_all(["article", "h2"], limit=30):
        link_tag = tag.find("a", href=True)
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)
        if len(title) < 10 or "prosport.ro" not in href:
            continue

        excerpt = ""
        p = tag.find("p")
        if p:
            excerpt = p.get_text(strip=True)[:300]

        articles.append({
            "title": title,
            "url": href,
            "excerpt": excerpt,
            "body": excerpt,  # no full body fetch for prosport — keeps it fast
            "date": "",
            "source": "prosport.ro",
        })

        if len(articles) >= max_articles:
            break

    logger.info(f"Prosport search '{query}': found {len(articles)} articles")
    return articles


# ---------------------------------------------------------------------------
# Google News RSS Fallback
# ---------------------------------------------------------------------------

def search_google_news_rss(query: str, is_player: bool = False, max_results: int = 5) -> List[Dict]:
    """
    Fallback: Google News RSS — returns title-only articles.
    Used when BS4 is unavailable or both scrapers fail.
    """
    if is_player:
        query_str = f'"{query}" fotbal (accidentare OR transfer OR criticat OR suspendat)'
    else:
        query_str = f'"{query}" fotbal (meci OR accidentare OR antrenor OR transfer)'

    encoded = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=ro&gl=RO&ceid=RO:ro"

    articles = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is not None and title_el.text:
                articles.append({
                    "title": title_el.text,
                    "url": link_el.text if link_el is not None else "",
                    "excerpt": title_el.text,
                    "body": title_el.text,  # only headlines available
                    "date": pub_el.text if pub_el is not None else "",
                    "source": "google_news_rss",
                })
            if len(articles) >= max_results:
                break
    except Exception as e:
        logger.warning(f"Google News RSS failed for '{query}': {e}")

    return articles


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def scrape_opponent_news(
    opponent_name: str,
    player_names: List[str],
    max_team_articles: int = 5,
    max_player_articles: int = 2,
    fetch_full_bodies: bool = True,
) -> Dict[str, Any]:
    """
    Scrape news for an opponent team and its key players.

    Returns:
    {
        "team_articles": [{"title": ..., "body": ..., "url": ..., "source": ...}],
        "player_articles": {
            "Player Name": [{"title": ..., "body": ..., ...}]
        },
        "scraped_at": "ISO timestamp",
        "sources_used": ["gsp.ro", "prosport.ro"],
    }
    """
    result: Dict[str, Any] = {
        "team_articles": [],
        "player_articles": {},
        "scraped_at": datetime.utcnow().isoformat(),
        "sources_used": [],
    }

    # --- Team-level news ---
    logger.info(f"Scraping team news for: {opponent_name}")

    team_articles = search_gsp(opponent_name, max_articles=max_team_articles, fetch_bodies=fetch_full_bodies)
    if team_articles:
        result["sources_used"].append("gsp.ro")

    # Supplement with Prosport if we got fewer than 3 articles
    if len(team_articles) < 3:
        time.sleep(INTER_REQUEST_DELAY)
        prosport_articles = search_prosport(opponent_name, max_articles=max_team_articles - len(team_articles))
        if prosport_articles:
            team_articles.extend(prosport_articles)
            result["sources_used"].append("prosport.ro")

    # Fallback to RSS if still empty
    if not team_articles:
        rss = search_google_news_rss(opponent_name, is_player=False, max_results=max_team_articles)
        team_articles = rss
        if rss:
            result["sources_used"].append("google_news_rss")

    result["team_articles"] = team_articles

    # --- Per-player news ---
    for player_name in player_names:
        if not player_name or player_name.startswith("Player "):
            continue  # Skip unmapped IDs

        logger.info(f"  Scraping player news: {player_name}")
        time.sleep(INTER_REQUEST_DELAY)

        player_articles = search_gsp(
            player_name,
            max_articles=max_player_articles,
            fetch_bodies=fetch_full_bodies,
        )

        if not player_articles:
            # Fallback: RSS
            player_articles = search_google_news_rss(
                player_name, is_player=True, max_results=max_player_articles
            )

        result["player_articles"][player_name] = player_articles

    logger.info(
        f"Scrape complete for '{opponent_name}': "
        f"{len(result['team_articles'])} team articles, "
        f"{len(result['player_articles'])} players covered"
    )
    return result


# ---------------------------------------------------------------------------
# Utility: summarize scraped news for use in prompts
# ---------------------------------------------------------------------------

def summarize_for_prompt(scraped: Dict[str, Any], max_chars_per_section: int = 2000) -> str:
    """Convert scraped news dict to a concise string for inclusion in a Gemini prompt."""
    parts = []

    team_texts = []
    for art in scraped.get("team_articles", []):
        body = art.get("body") or art.get("excerpt") or art.get("title", "")
        team_texts.append(f"[{art.get('source','?')}] {art.get('title','')}: {body[:400]}")
    if team_texts:
        parts.append("=== ȘTIRI ECHIPĂ ===\n" + "\n---\n".join(team_texts))

    player_section = []
    for pname, arts in scraped.get("player_articles", {}).items():
        p_texts = []
        for art in arts:
            body = art.get("body") or art.get("excerpt") or art.get("title", "")
            p_texts.append(f"  [{art.get('source','?')}] {art.get('title','')}: {body[:300]}")
        if p_texts:
            player_section.append(f"[{pname}]\n" + "\n".join(p_texts))
    if player_section:
        parts.append("=== ȘTIRI JUCĂTORI ===\n" + "\n\n".join(player_section))

    result = "\n\n".join(parts)
    return result[:max_chars_per_section * 2]  # hard cap
