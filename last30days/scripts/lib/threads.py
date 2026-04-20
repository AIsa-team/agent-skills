"""Threads discovery for /last30days using the AISA web proxy."""

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import aisa, log
from .relevance import token_overlap_relevance as _compute_relevance

# Depth configurations: how many results to fetch
DEPTH_CONFIG = {
    "quick":   {"results": 10},
    "default": {"results": 20},
    "deep":    {"results": 40},
}


def _log(msg: str):
    log.source_log("Threads", msg)

def _search_via_aisa(topic: str, from_date: str, to_date: str, depth: str, token: str) -> Dict[str, Any]:
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    result = aisa.search_tavily(token, f"site:threads.net {topic}", limit=config["results"])
    web_items, _ = aisa.parse_tavily_response(result, date_range=(from_date, to_date))
    items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(web_items, start=1):
        url = entry.get("url", "")
        if "threads.net" not in url:
            continue
        date_str = entry.get("date")
        if date_str and not (from_date <= date_str <= to_date):
            continue
        text = entry.get("title") or entry.get("snippet") or topic
        items.append({
            "id": f"TH{idx}",
            "handle": "",
            "display_name": "",
            "text": text,
            "url": url,
            "date": date_str,
            "engagement": {"likes": 0, "replies": 0, "reposts": 0, "quotes": 0},
            "relevance": entry.get("relevance", 0.5),
            "why_relevant": "Threads web result via AISA",
        })
    return {"items": items[: config["results"]]}


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for Threads search."""
    from .query import extract_core_subject
    _THREADS_NOISE = frozenset({
        'best', 'top', 'good', 'great', 'awesome',
        'latest', 'new', 'news', 'update', 'updates',
        'trending', 'hottest', 'popular', 'viral',
        'practices', 'features', 'recommendations', 'advice',
    })
    return extract_core_subject(topic, noise=_THREADS_NOISE)


def _parse_date(item: Dict[str, Any]) -> Optional[str]:
    """Parse date from Threads item to YYYY-MM-DD.

    Tries common timestamp fields: taken_at (unix), created_at (ISO),
    and falls back to any date-like string field.
    """
    # Unix timestamp (taken_at is common in Meta APIs)
    for key in ("taken_at", "create_time"):
        ts = item.get(key)
        if ts:
            try:
                from . import dates
                return dates.timestamp_to_date(int(ts))
            except (ValueError, TypeError):
                pass

    # ISO 8601 string
    for key in ("created_at", "published_at", "date"):
        val = item.get(key)
        if val and isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

    return None


def _parse_items(raw_items: List[Dict[str, Any]], core_topic: str) -> List[Dict[str, Any]]:
    """Parse raw Threads items into normalized dicts."""
    items = []
    for i, raw in enumerate(raw_items):
        post_id = str(
            raw.get("id")
            or raw.get("pk")
            or raw.get("code")
            or f"TH{i + 1}"
        )
        text = raw.get("text") or raw.get("caption") or raw.get("content") or ""
        if isinstance(text, dict):
            text = text.get("text", "")

        # Author extraction
        user = raw.get("user") or raw.get("author") or {}
        if isinstance(user, dict):
            handle = user.get("username") or user.get("handle") or ""
            display_name = user.get("full_name") or user.get("displayName") or handle
        elif isinstance(user, str):
            handle = user
            display_name = user
        else:
            handle = ""
            display_name = ""

        # Engagement metrics
        likes = raw.get("like_count") or raw.get("likes") or 0
        replies = raw.get("reply_count") or raw.get("replies") or 0
        reposts = raw.get("repost_count") or raw.get("reposts") or 0
        quotes = raw.get("quote_count") or raw.get("quotes") or 0

        date_str = _parse_date(raw)

        # Build URL
        code = raw.get("code") or raw.get("shortcode") or ""
        url = raw.get("url") or raw.get("share_url") or ""
        if not url and code:
            url = f"https://www.threads.net/post/{code}"
        elif not url and handle and post_id:
            url = f"https://www.threads.net/@{handle}/post/{post_id}"

        # Relevance: position-based plus engagement boost for short social posts.
        rank_score = max(0.3, 1.0 - (i * 0.02))
        engagement_boost = min(0.2, math.log1p(likes + reposts) / 40)
        text_relevance = _compute_relevance(core_topic, text)
        relevance = min(1.0, text_relevance * 0.5 + rank_score * 0.3 + engagement_boost + 0.1)

        items.append({
            "id": post_id,
            "handle": handle,
            "display_name": display_name,
            "text": text,
            "url": url,
            "date": date_str,
            "engagement": {
                "likes": likes,
                "replies": replies,
                "reposts": reposts,
                "quotes": quotes,
            },
            "relevance": round(relevance, 2),
            "why_relevant": f"Threads: @{handle}: {text[:60]}" if text else f"Threads: {handle}",
        })
    return items


def search_threads(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
) -> Dict[str, Any]:
    """Search Threads using the hosted AISA discovery path.

    Args:
        topic: Search topic
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'
        token: AISA API key

    Returns:
        Dict with 'items' list and optional 'error'.
    """
    if not token:
        return {"items": [], "error": "AISA_API_KEY not configured"}
    return _search_via_aisa(topic, from_date, to_date, depth, token)


def parse_threads_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Threads search response to normalized format.

    Returns:
        List of item dicts ready for normalization.
    """
    return response.get("items", [])
