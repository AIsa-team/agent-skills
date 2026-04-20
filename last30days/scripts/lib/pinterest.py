"""Pinterest discovery for /last30days using the AISA web proxy."""

import re
import sys
from typing import Any, Dict, List, Optional, Set

try:
    import requests as _requests
except ImportError:
    _requests = None

from . import aisa, dates, http, log

# Depth configurations: how many results to fetch
DEPTH_CONFIG = {
    "quick":   {"results_per_page": 10},
    "default": {"results_per_page": 20},
    "deep":    {"results_per_page": 40},
}

from .relevance import token_overlap_relevance as _compute_relevance


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for Pinterest search."""
    from .query import extract_core_subject
    _PINTEREST_NOISE = frozenset({
        'best', 'top', 'good', 'great', 'awesome', 'killer',
        'latest', 'new', 'news', 'update', 'updates',
        'trending', 'hottest', 'popular', 'viral',
        'practices', 'features',
        'recommendations', 'advice',
        'prompt', 'prompts', 'prompting',
        'methods', 'strategies', 'approaches',
    })
    return extract_core_subject(topic, noise=_PINTEREST_NOISE)


def _log(msg: str):
    log.source_log("Pinterest", msg)

def _search_via_aisa(topic: str, from_date: str, to_date: str, depth: str, token: str) -> Dict[str, Any]:
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])
    result = aisa.search_tavily(token, f"site:pinterest.com {topic}", limit=config["results_per_page"])
    web_items, _ = aisa.parse_tavily_response(result, date_range=(from_date, to_date))
    items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(web_items, start=1):
        url = entry.get("url", "")
        if "pinterest." not in url:
            continue
        date_str = entry.get("date")
        if date_str and not (from_date <= date_str <= to_date):
            continue
        description = entry.get("title") or entry.get("snippet") or topic
        items.append({
            "id": f"PIN{idx}",
            "title": description,
            "description": entry.get("snippet", ""),
            "url": url,
            "date": date_str,
            "engagement": {"saves": 0, "comments": 0},
            "relevance": entry.get("relevance", 0.5),
            "why_relevant": "Pinterest web result via AISA",
        })
    return {"items": items[: config["results_per_page"]]}


def _parse_items(raw_items: List[Dict[str, Any]], core_topic: str) -> List[Dict[str, Any]]:
    """Parse raw Pinterest items into normalized dicts.

    Pinterest pins are visual content with descriptions. Saves are the
    primary engagement signal (analogous to upvotes/likes on other platforms).
    """
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue

        pin_id = str(raw.get("id", raw.get("pin_id", "")))
        description = str(raw.get("description") or raw.get("title") or "")

        # Engagement metrics - saves are the primary signal
        save_count = raw.get("save_count") or raw.get("saves") or raw.get("repin_count") or 0
        comment_count = raw.get("comment_count") or raw.get("comments") or 0

        # Author info
        pinner = raw.get("pinner") or raw.get("creator") or raw.get("user") or {}
        if isinstance(pinner, dict):
            author_name = pinner.get("username") or pinner.get("full_name") or ""
        elif isinstance(pinner, str):
            author_name = pinner
        else:
            author_name = ""

        # URL
        url = raw.get("link") or raw.get("url") or ""
        if not url and pin_id:
            url = f"https://www.pinterest.com/pin/{pin_id}/"

        # Board info (container for pins)
        board = raw.get("board") or {}
        board_name = board.get("name", "") if isinstance(board, dict) else ""

        # Compute relevance
        relevance = _compute_relevance(core_topic, description, [])

        items.append({
            "pin_id": pin_id,
            "description": description,
            "url": url,
            "author": author_name,
            "board": board_name,
            "engagement": {
                "saves": save_count,
                "comments": comment_count,
            },
            "relevance": relevance,
            "why_relevant": f"Pinterest: {description[:60]}" if description else f"Pinterest: {core_topic}",
        })
    return items


def parse_pinterest_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Pinterest search response to normalized format.

    Returns:
        List of item dicts ready for normalization.
    """
    return response.get("items", [])


def search_pinterest(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
) -> Dict[str, Any]:
    """Search Pinterest using the hosted AISA discovery path.

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
