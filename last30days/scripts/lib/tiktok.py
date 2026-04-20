"""TikTok discovery for /last30days using the AISA web proxy."""

import re
import sys
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


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for TikTok search."""
    from .query import extract_core_subject
    _TIKTOK_NOISE = frozenset({
        'best', 'top', 'good', 'great', 'awesome', 'killer',
        'latest', 'new', 'news', 'update', 'updates',
        'trending', 'hottest', 'popular', 'viral',
        'practices', 'features',
        'recommendations', 'advice',
        'prompt', 'prompts', 'prompting',
        'methods', 'strategies', 'approaches',
    })
    return extract_core_subject(topic, noise=_TIKTOK_NOISE)


def _infer_query_intent(topic: str) -> str:
    """Tiny local intent classifier for TikTok query expansion."""
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


def expand_tiktok_queries(topic: str, depth: str) -> List[str]:
    """Generate multiple TikTok search queries from a topic.

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

    # Intent-specific TikTok content-type variants
    if qtype in ("breaking_news", "opinion"):
        queries.append(f"{core} edit OR reaction OR trend")
    elif qtype == "product":
        queries.append(f"{core} review OR haul OR unboxing")
    elif qtype == "comparison":
        queries.append(f"{core} vs OR compared OR which is better")
    elif qtype == "how_to":
        queries.append(f"{core} tutorial OR hack OR tip")
    else:
        queries.append(f"{core} edit OR reaction OR trend")

    # Deep depth: add viral content variant
    if depth == "deep":
        queries.append(f"{core} viral OR fyp OR trending")

    # Cap by depth budget
    caps = {"quick": 1, "default": 2, "deep": 3}
    cap = caps.get(depth, 2)
    return queries[:cap]


def _log(msg: str):
    log.source_log("TikTok", msg)


def _search_via_aisa(topic: str, from_date: str, to_date: str, depth: str, token: str) -> Dict[str, Any]:
    """Use AISA Tavily proxy as the preferred TikTok discovery path."""
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    query = f"site:tiktok.com {topic}"
    result = aisa.search_tavily(token, query, limit=config["results_per_page"])
    web_items, _ = aisa.parse_tavily_response(result, date_range=(from_date, to_date))
    items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(web_items, start=1):
        url = entry.get("url", "")
        if "tiktok.com" not in url:
            continue
        date_str = entry.get("date")
        if date_str and not (from_date <= date_str <= to_date):
            continue
        title = entry.get("title") or entry.get("snippet") or topic
        items.append({
            "video_id": f"TT{idx}",
            "text": title,
            "url": url,
            "author_name": "",
            "date": date_str,
            "engagement": {"views": 0, "likes": 0, "comments": 0, "shares": 0},
            "hashtags": [],
            "duration": None,
            "relevance": entry.get("relevance", 0.5),
            "why_relevant": "TikTok web result via AISA",
            "caption_snippet": entry.get("snippet", ""),
        })
    return {"items": items[: config["results_per_page"]]}


def _parse_date(item: Dict[str, Any]) -> Optional[str]:
    """Parse date from a legacy TikTok item to YYYY-MM-DD."""
    ts = item.get("create_time")
    if ts:
        try:
            return dates.timestamp_to_date(int(ts))
        except (ValueError, TypeError):
            pass
    return None


def _clean_webvtt(text: str) -> str:
    """Strip WebVTT timestamps and headers from transcript text."""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('WEBVTT'):
            continue
        if re.match(r'^\d{2}:\d{2}', line):
            continue
        if '-->' in line:
            continue
        cleaned.append(line)
    return ' '.join(cleaned)


def _parse_items(raw_items: List[Dict[str, Any]], core_topic: str) -> List[Dict[str, Any]]:
    """Parse raw TikTok items into normalized dicts."""
    items = []
    for raw in raw_items:
        video_id = str(raw.get("aweme_id", ""))
        text = raw.get("desc", "")

        stats = raw.get("statistics") if isinstance(raw.get("statistics"), dict) else {}
        play_count = stats.get("play_count") if stats.get("play_count") is not None else 0
        digg_count = stats.get("digg_count") if stats.get("digg_count") is not None else 0
        comment_count = stats.get("comment_count") if stats.get("comment_count") is not None else 0
        share_count = stats.get("share_count") if stats.get("share_count") is not None else 0

        author_raw = raw.get("author")
        if isinstance(author_raw, dict):
            author_name = author_raw.get("unique_id", "")
        elif isinstance(author_raw, str):
            author_name = author_raw
        else:
            author_name = ""

        share_url = raw.get("share_url", "")
        text_extra = raw.get("text_extra") or []
        hashtag_names = [t.get("hashtag_name", "") for t in text_extra
                         if isinstance(t, dict) and t.get("hashtag_name")]

        video_raw = raw.get("video")
        duration = video_raw.get("duration") if isinstance(video_raw, dict) else None

        date_str = _parse_date(raw)

        # Compute relevance with hashtag boost
        relevance = _compute_relevance(core_topic, text, hashtag_names)

        # Build URL: prefer share_url, fallback to constructed URL
        url = share_url.split("?")[0] if share_url else ""
        if not url and author_name and video_id:
            url = f"https://www.tiktok.com/@{author_name}/video/{video_id}"

        items.append({
            "video_id": video_id,
            "text": text,
            "url": url,
            "author_name": author_name,
            "date": date_str,
            "engagement": {
                "views": play_count,
                "likes": digg_count,
                "comments": comment_count,
                "shares": share_count,
            },
            "hashtags": hashtag_names,
            "duration": duration,
            "relevance": relevance,
            "why_relevant": f"TikTok: {text[:60]}" if text else f"TikTok: {core_topic}",
            "caption_snippet": "",  # populated by fetch_captions
        })
    return items


def _hashtag_search(
    hashtag: str,
    token: str,
) -> List[Dict[str, Any]]:
    """Hashtag helper is disabled in the AISA-only runtime.

    Args:
        hashtag: Hashtag name (without #)
        token: Legacy compatibility API key

    Returns:
        List of raw TikTok item dicts (aweme_info format).
    """
    del hashtag, token
    return []


def _profile_videos(
    handle: str,
    token: str,
    count: int = 10,
) -> List[Dict[str, Any]]:
    """Creator fetch helper is disabled in the AISA-only runtime.

    Args:
        handle: TikTok username (without @)
        token: Legacy compatibility API key
        count: Max videos to return

    Returns:
        List of raw TikTok item dicts (aweme_info format).
    """
    del handle, token, count
    return []


def search_tiktok(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
) -> Dict[str, Any]:
    """Compatibility wrapper around the hosted AISA TikTok discovery path.

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
    1. Use the 'text' field (video description) as baseline caption
    2. For top N, call /video/transcript for spoken-word captions

    Args:
        video_items: Items from search_tiktok()
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
    hashtags: List[str] | None = None,
    creators: List[str] | None = None,
) -> Dict[str, Any]:
    """Full TikTok search using the hosted AISA discovery path.

    Args:
        topic: Search topic (raw topic, not planner's narrowed query)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'
        token: AISA API key
        hashtags: Optional list of TikTok hashtags to search (without #)
        creators: Optional list of TikTok creator handles to fetch videos from

    Returns:
        Dict with 'items' list. Each item has a 'caption_snippet' field.
    """
    del hashtags, creators
    if not token:
        return {"items": [], "error": "AISA_API_KEY not configured"}
    return _search_via_aisa(topic, from_date, to_date, depth, token)


def parse_tiktok_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse TikTok search response to normalized format.

    Returns:
        List of item dicts ready for normalization.
    """
    return response.get("items", [])
