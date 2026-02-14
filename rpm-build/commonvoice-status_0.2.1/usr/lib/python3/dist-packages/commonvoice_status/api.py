"""Common Voice API client with local caching."""

import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

API_URL = "https://commonvoice.mozilla.org/api/v1/stats/languages"
CACHE_DIR = Path.home() / ".cache" / "commonvoice-status"
CACHE_FILE = CACHE_DIR / "languages.json"
CACHE_TTL = 3600  # 1 hour

# Milestones in validated hours
MILESTONES = [10, 50, 100, 250, 500, 1000, 2000, 5000, 10000]


def _read_cache():
    """Read cached data if fresh enough."""
    if not CACHE_FILE.exists():
        return None
    try:
        stat = CACHE_FILE.stat()
        if time.time() - stat.st_mtime > CACHE_TTL:
            return None
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(data):
    """Write data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def fetch_languages(force_refresh=False):
    """Fetch language statistics. Returns list of dicts."""
    if not force_refresh:
        cached = _read_cache()
        if cached is not None:
            return cached

    req = urllib.request.Request(API_URL, headers={"User-Agent": "CommonVoiceStatus/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        _write_cache(data)
        return data
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        # Fall back to stale cache
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        raise RuntimeError(f"Failed to fetch data: {e}")


def next_milestone(validated_hours):
    """Return the next milestone and hours remaining."""
    for m in MILESTONES:
        if validated_hours < m:
            return m, m - validated_hours
    return None, 0


def get_language_by_locale(languages, locale_code):
    """Find a language by locale code."""
    for lang in languages:
        if lang.get("locale") == locale_code:
            return lang
    return None
