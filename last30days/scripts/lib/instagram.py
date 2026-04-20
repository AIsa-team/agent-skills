"""Instagram discovery for /last30days using the AISA web proxy."""

import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

try:
    import requests as _requests
except ImportError:
    _requests = None

from . import aisa, dates, http, log

# Depth configurations: how many results to fetch / captions to extract
DEPTH_CONFIG = {
    "quick":   {"results_per_page": 10, "max_captions": 3},
    "default": {"results_per_page": 20, "max_captions": 5},
    "deep":    {"results_per_page": 40, "max_captions": 8},
}

# Max words to keep from each caption
CAPTION_MAX_WORDS = 500

from .relevance import token_overlap_relevance as _compute_relevance

def _search_via_aisa(topic: str, from_date: str, to_date: str, depth: str, token: str) -> Dict[str, Any]:
    """Use the AISA proxy as the preferred Instagram discovery path."""
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    query = f"site:instagram.com/reel OR site:instagram.com/p {topic}"
    result = aisa.search_tavily(token, query, limit=config["results_per_page"])
    web_items, _ = aisa.parse_tavily_response(result, date_range=(from_date, to_date))
    items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(web_items, start=1):
        url = entry.get("url", "")
        if "instagram.com" not in url:
            continue
        date_str = entry.get("date")
        if date_str and not (from_date <= date_str <= to_date):
            continue
        title = entry.get("title") or entry.get("snippet") or topic
        items.append({
            "video_id": f"IG{idx}",
            "text": title,
            "url": url,
            "author_name": "",
            "date": date_str,
            "engagement": {"views": 0, "likes": 0, "comments": 0},
            "hashtags": [],
            "duration": None,
            "relevance": entry.get("relevance", 0.5),
            "why_relevant": "Instagram web result via AISA",
            "caption_snippet": entry.get("snippet", ""),
        })
    return {"items": items[: config["results_per_page"]]}


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for Instagram search."""
    from .query import extract_core_subject
    _INSTAGRAM_NOISE = frozenset({
        'best', 'top', 'good', 'great', 'awesome', 'killer',
        'latest', 'new', 'news', 'update', 'updates',
        'trending', 'hottest', 'popular', 'viral',
        'practices', 'features',
        'recommendations', 'advice',
        'prompt', 'prompts', 'prompting',
        'methods', 'strategies', 'approaches',
    })
    return extract_core_subject(topic, noise=_INSTAGRAM_NOISE)


def _infer_query_intent(topic: str) -> str:
    """Tiny local intent classifier for Instagram query expansion."""
    text = topic.lower().strip()
    if re.search(r"\b(vs|versus|compare|difference between)\b", text):
        return "comparison"
    if re.search(r"\b(how to|tutorial|guide|setup|step by step|deploy|install)\b", text):
        return "how_to"
    if re.search(r"\b(thoughts on|worth it|should i|opinion|review)\b", text):
        return "opinion"
    if re.search(r"\b(pricing|feature|features|best .* for)\b", text):
        return "product"
    return "breaking_news"


def expand_instagram_queries(topic: str, depth: str) -> List[str]:
    """Generate multiple Instagram search queries from a topic.

    Mirrors reddit.py's expand_reddit_queries() pattern:
    1. Extract core subject (strip noise words)
    2. Include original topic if different from core
    3. Add intent-specific OR-joined content-type variants
    4. Cap by depth: 1 for quick, 2 for default, 3 for deep

    Returns 1-3 query strings depending on depth.
    """
    core = _extract_core_subject(topic)
    queries = [core]

    # Include cleaned original topic as variant if different from core
    original_clean = topic.strip().rstrip('?!.')
    if core.lower() != original_clean.lower() and len(original_clean.split()) <= 8:
        queries.append(original_clean)

    qtype = _infer_query_intent(topic)

    # Intent-specific Instagram content-type variants
    if qtype == "breaking_news":
        queries.append(f"{core} reaction OR edit")
    elif qtype == "opinion":
        queries.append(f"{core} reaction OR edit")
    elif qtype == "product":
        queries.append(f"{core} review OR haul")
    elif qtype == "comparison":
        queries.append(f"{core} vs OR compared")
    elif qtype == "how_to":
        queries.append(f"{core} tutorial OR hack")
    else:
        queries.append(f"{core} reaction OR edit")

    # Deep depth: add viral content variant
    if depth == "deep":
        queries.append(f"{core} viral OR trending OR reel")

    # Cap by depth budget
    caps = {"quick": 1, "default": 2, "deep": 3}
    cap = caps.get(depth, 2)
    return queries[:cap]


def _log(msg: str):
    log.source_log("Instagram", msg)


def _parse_date(item: Dict[str, Any]) -> Optional[str]:
    """Parse date from a legacy Instagram item to YYYY-MM-DD.

    Handles taken_at as ISO string (e.g. "2026-02-26T16:00:00.000Z")
    or unix timestamp.
    """
    ts = item.get("taken_at")
    if not ts:
        return None

    # Try ISO string first (legacy reels/search commonly returns this)
    if isinstance(ts, str):
        try:
            # Handle "2026-02-26T16:00:00.000Z" format
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        # Try just the date portion
        if len(ts) >= 10:
            return ts[:10]

    # Fall back to unix timestamp
    try:
        return dates.timestamp_to_date(int(ts))
    except (ValueError, TypeError):
        pass

    return None


def _extract_hashtags(caption_text: str) -> List[str]:
    """Extract hashtags from Instagram caption text."""
    if not caption_text:
        return []
    return re.findall(r'#(\w+)', caption_text)


def _parse_items(raw_items: List[Dict[str, Any]], core_topic: str) -> List[Dict[str, Any]]:
    """Parse raw Instagram items into normalized dicts."""
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        # Extract reel ID and shortcode
        reel_pk = str(raw.get("id", raw.get("pk", "")))
        shortcode = raw.get("shortcode", raw.get("code", ""))

        # Caption text -- can be a string or dict depending on endpoint
        caption_obj = raw.get("caption", "")
        if isinstance(caption_obj, dict):
            text = caption_obj.get("text", "")
        elif isinstance(caption_obj, str):
            text = caption_obj
        else:
            text = raw.get("desc", raw.get("text", ""))

        # Engagement metrics
        play_count = raw.get("video_play_count") or raw.get("video_view_count") or raw.get("play_count") or 0
        like_count = raw.get("like_count") or 0
        comment_count = raw.get("comment_count") or 0

        # Author info -- 'owner' in reels/search, 'user' in user/reels
        owner_raw = raw.get("owner") or raw.get("user")
        if isinstance(owner_raw, dict):
            author_name = owner_raw.get("username", "")
        elif isinstance(owner_raw, str):
            author_name = owner_raw
        else:
            author_name = ""

        # Duration
        duration = raw.get("video_duration")

        # Date
        date_str = _parse_date(raw)

        # Hashtags from caption text
        hashtags = _extract_hashtags(text)

        # Compute relevance with hashtag boost
        relevance = _compute_relevance(core_topic, text, hashtags)

        # Build URL -- prefer API-provided url, fallback to shortcode
        url = raw.get("url", "")
        if not url and shortcode:
            url = f"https://www.instagram.com/reel/{shortcode}"

        items.append({
            "video_id": reel_pk,
            "text": text,
            "url": url,
            "author_name": author_name,
            "date": date_str,
            "engagement": {
                "views": play_count,
                "likes": like_count,
                "comments": comment_count,
            },
            "hashtags": hashtags,
            "duration": duration,
            "relevance": relevance,
            "why_relevant": f"Instagram: {text[:60]}" if text else f"Instagram: {core_topic}",
            "caption_snippet": "",  # populated by fetch_captions
        })
    return items


def _user_reels(
    handle: str,
    token: str,
) -> List[Dict[str, Any]]:
    """Creator reel helper is disabled in the AISA-only runtime.

    Args:
        handle: Instagram username (without @)
        token: Legacy compatibility API key

    Returns:
        List of raw Instagram reel dicts.
    """
    del handle, token
    return []


def search_instagram(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
) -> Dict[str, Any]:
    """Compatibility wrapper around the hosted AISA Instagram discovery path.

    Args:
        topic: Search topic
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'
        token: Legacy compatibility API key

    Returns:
        Dict with 'items' list and optional 'error'.
    """
    return search_and_enrich(topic, from_date, to_date, depth=depth, token=token)


def fetch_captions(
    video_items: List[Dict[str, Any]],
    token: str,
    depth: str = "default",
) -> Dict[str, str]:
    """Caption enrichment beyond AISA web snippets is disabled.

    Strategy:
    1. Use the 'text' field (caption) as baseline
    2. For top N, call /v2/instagram/media/transcript for spoken-word captions

    Args:
        video_items: Items from search_instagram()
        token: Legacy compatibility API key
        depth: Depth level for caption limit

    Returns:
        Dict mapping video_id -> caption text (truncated to 500 words)
    """
    del video_items, token, depth
    return {}


def search_and_enrich(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
    ig_creators: List[str] | None = None,
) -> Dict[str, Any]:
    """Full Instagram search using the hosted AISA discovery path.

    Args:
        topic: Search topic (raw topic, not planner's narrowed query)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'
        token: AISA API key
        ig_creators: Optional list of Instagram creator handles to fetch reels from

    Returns:
        Dict with 'items' list. Each item has a 'caption_snippet' field.
    """
    del ig_creators
    if not token:
        return {"items": [], "error": "AISA_API_KEY not configured"}
    return _search_via_aisa(topic, from_date, to_date, depth, token)


def parse_instagram_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Instagram search response to normalized format.

    Returns:
        List of item dicts ready for normalization.
    """
    return response.get("items", [])
