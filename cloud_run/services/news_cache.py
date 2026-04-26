"""
news_cache.py — Simple file-based cache for scraped news results.
Prevents hammering external sites on every API call.
TTL: 1 hour by default.
Cache keys are date-aware so changing the match date triggers fresh Gemini analysis.
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("forma_os_cache")

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_TTL_SECONDS = 3600  # 1 hour


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _slug(name: str) -> str:
    """Convert a team/player name to a safe filename slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:80]


def _cache_key(team_key: str, game_date: Optional[str] = None) -> str:
    """Build a cache key that incorporates the match date when provided."""
    base = _slug(team_key)
    if game_date:
        # Use only the date portion (YYYY-MM-DD) so time changes don't bust cache
        date_part = _slug(game_date[:10])
        return f"{base}__{date_part}"
    return base


def get_cached_news(key: str, game_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Return cached scrape result if fresh.
    game_date makes the key unique per match day.
    """
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_cache_key(key, game_date)}.json"

    if not cache_file.exists():
        return None

    age = time.time() - cache_file.stat().st_mtime
    if age > CACHE_TTL_SECONDS:
        logger.info(f"Cache expired for '{key}' ({age:.0f}s old)")
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Cache HIT for '{key}' date={game_date} ({age:.0f}s old)")
        return data
    except Exception as e:
        logger.warning(f"Cache read error for '{key}': {e}")
        return None


def set_cached_news(key: str, data: Dict[str, Any], game_date: Optional[str] = None) -> None:
    """Write scrape results to cache."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_cache_key(key, game_date)}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache SET for '{key}' date={game_date} → {cache_file}")
    except Exception as e:
        logger.warning(f"Cache write error for '{key}': {e}")


def invalidate_cache(key: str, game_date: Optional[str] = None) -> bool:
    """Manually invalidate a cached entry. Returns True if deleted."""
    cache_file = CACHE_DIR / f"{_cache_key(key, game_date)}.json"
    if cache_file.exists():
        cache_file.unlink()
        logger.info(f"Cache INVALIDATED for '{key}' date={game_date}")
        return True
    return False


def invalidate_all_for_team(team_key: str) -> int:
    """Invalidate ALL cache entries for a team (all dates). Returns count deleted."""
    _ensure_cache_dir()
    base = _slug(team_key)
    deleted = 0
    for f in CACHE_DIR.glob(f"{base}*.json"):
        f.unlink()
        deleted += 1
    logger.info(f"Invalidated {deleted} cache entries for team '{team_key}'")
    return deleted


def get_or_fetch(
    key: str,
    fetch_fn,
    *args,
    game_date: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Try cache first; on miss call fetch_fn(*args, **kwargs) and store result.
    game_date makes the cache key date-specific.
    """
    cached = get_cached_news(key, game_date=game_date)
    if cached is not None:
        return cached

    logger.info(f"Cache MISS for '{key}' date={game_date}, fetching fresh data...")
    result = fetch_fn(*args, **kwargs)
    if result:
        set_cached_news(key, result, game_date=game_date)
    return result or {}


# ---------------------------------------------------------------------------
# AI Profiles Cache (final Gemini-generated player weakness reports)
# ---------------------------------------------------------------------------

PROFILES_TTL_SECONDS = 86400  # 24 hours — profiles are expensive to regenerate


def _profiles_key(team_key: str, game_date: Optional[str] = None) -> str:
    """Build a cache key with 'profiles_' prefix."""
    return f"profiles_{_cache_key(team_key, game_date)}"


def get_cached_profiles(team_key: str, game_date: Optional[str] = None) -> Optional[list]:
    """Return cached AI profiles if they exist and are fresh."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_profiles_key(team_key, game_date)}.json"

    if not cache_file.exists():
        return None

    age = time.time() - cache_file.stat().st_mtime
    if age > PROFILES_TTL_SECONDS:
        logger.info(f"Profiles cache expired for '{team_key}' ({age:.0f}s old)")
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Profiles cache HIT for '{team_key}' date={game_date} ({age:.0f}s old)")
        return data
    except Exception as e:
        logger.warning(f"Profiles cache read error for '{team_key}': {e}")
        return None


def set_cached_profiles(team_key: str, profiles: list, game_date: Optional[str] = None) -> None:
    """Write final AI profiles to cache."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_profiles_key(team_key, game_date)}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        logger.info(f"Profiles cache SET for '{team_key}' date={game_date} → {cache_file} ({len(profiles)} players)")
    except Exception as e:
        logger.warning(f"Profiles cache write error for '{team_key}': {e}")


# ---------------------------------------------------------------------------
# Chronic Gaps Cache
# ---------------------------------------------------------------------------

GAPS_TTL_SECONDS = 86400  # 24 hours

def _gaps_key(team_key: str, game_date: Optional[str] = None) -> str:
    """Build a cache key with 'gaps_' prefix."""
    return f"gaps_{_cache_key(team_key, game_date)}"


def get_cached_gaps(team_key: str, game_date: Optional[str] = None) -> Optional[list]:
    """Return cached chronic gaps if they exist and are fresh."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_gaps_key(team_key, game_date)}.json"

    if not cache_file.exists():
        return None

    age = time.time() - cache_file.stat().st_mtime
    if age > GAPS_TTL_SECONDS:
        logger.info(f"Gaps cache expired for '{team_key}' ({age:.0f}s old)")
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Gaps cache HIT for '{team_key}' date={game_date} ({age:.0f}s old)")
        return data
    except Exception as e:
        logger.warning(f"Gaps cache read error for '{team_key}': {e}")
        return None


def set_cached_gaps(team_key: str, gaps: list, game_date: Optional[str] = None) -> None:
    """Write chronic gaps to cache."""
    _ensure_cache_dir()
    cache_file = CACHE_DIR / f"{_gaps_key(team_key, game_date)}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(gaps, f, ensure_ascii=False, indent=2)
        logger.info(f"Gaps cache SET for '{team_key}' date={game_date} → {cache_file} ({len(gaps)} gaps)")
    except Exception as e:
        logger.warning(f"Gaps cache write error for '{team_key}': {e}")

