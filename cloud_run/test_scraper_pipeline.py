# Quick smoke test for the full web scraping -> Gemini pipeline.
# Run from the cloud_run directory:  python test_scraper_pipeline.py
import sys
import os
import logging

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO)

from services.scraper import scrape_opponent_news, summarize_for_prompt
from services.news_engine import generate_pregame_intelligence_v2

OPPONENT = "CFR Cluj"
PLAYERS = ["Cristian Manea", "Dan Petrescu", "Lacina Traore"]

print("=" * 60)
print(f"[1] Scraping news for: {OPPONENT}")
print("=" * 60)

result = scrape_opponent_news(
    OPPONENT,
    PLAYERS,
    max_team_articles=3,
    max_player_articles=2,
    fetch_full_bodies=False,  # faster for test
)

print(f"Team articles: {len(result['team_articles'])}")
print(f"Player articles: {list(result['player_articles'].keys())}")
print(f"Sources used: {result['sources_used']}")

for art in result["team_articles"][:2]:
    print(f"  [{art['source']}] {art['title'][:80]}")

print()
summary = summarize_for_prompt(result, max_chars_per_section=1000)
print("[2] Prompt summary (first 800 chars):")
print(summary[:800])
print()

# Stage 2: pass through Gemini (only if API key set)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    print("[3] Running Gemini intelligence extraction...")
    fake_stats = [
        {"playerId": "123", "name": "Cristian Manea", "total": {"duels": 10, "duelsWon": 3}},
        {"playerId": "456", "name": "Dan Petrescu", "total": {"duels": 5, "duelsWon": 2}},
    ]
    intel = generate_pregame_intelligence_v2(fake_stats, OPPONENT, result)
    for player_intel in intel:
        print(f"\n  --- {player_intel.get('name', '?')} ---")
        print(f"  Physical: {player_intel.get('physical_state', '')[:120]}")
        print(f"  Exploit: {player_intel.get('exploit_recommendation', '')[:120]}")
        print(f"  Score: {player_intel.get('overall_weakness_score', '?')}")
else:
    print("[3] Skipping Gemini stage — GOOGLE_API_KEY not set in environment.")

print()
print("DONE.")
