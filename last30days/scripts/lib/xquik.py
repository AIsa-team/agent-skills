"""AISA-backed compatibility wrapper for legacy Xquik call sites."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import aisa, http

DEPTH_CONFIG = {
    "quick": {"limit": 10, "queries": 1},
    "default": {"limit": 20, "queries": 2},
    "deep": {"limit": 40, "queries": 3},
}


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%a %b %d %H:%M:%S %z %Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _parse_tweet(tweet: dict[str, Any], index: int, topic: str) -> dict[str, Any] | None:
    author = tweet.get("author") or {}
    handle = author.get("username") if isinstance(author, dict) else None
    if not handle:
        return None
    handle = str(handle).lstrip("@")
    tweet_id = str(tweet.get("id") or "").strip()
    if not tweet_id:
        return None
    text = str(tweet.get("text") or "")[:500]
    return {
        "id": f"XQ{index + 1}",
        "text": text,
        "url": f"https://x.com/{handle}/status/{tweet_id}",
        "author_handle": handle,
        "date": _normalize_date(tweet.get("createdAt")),
        "engagement": {
            "likes": _safe_int(tweet.get("likeCount")),
            "reposts": _safe_int(tweet.get("retweetCount")),
            "replies": _safe_int(tweet.get("replyCount")),
            "quotes": _safe_int(tweet.get("quoteCount")),
            "views": _safe_int(tweet.get("viewCount")),
            "bookmarks": _safe_int(tweet.get("bookmarkCount")),
        },
        "relevance": 0.8 if topic else 0.5,
        "why_relevant": "AISA/Xquik compatibility search",
    }


def expand_xquik_queries(topic: str, depth: str) -> list[str]:
    cleaned = topic.strip()
    query_count = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])["queries"]
    return [cleaned] * min(query_count, 1)


def _search_via_aisa(topic: str, from_date: str, depth: str, token: str) -> dict[str, Any]:
    items = aisa.parse_twitter_response(
        aisa.search_twitter(token, topic, from_date, depth=depth),
        query=topic,
    )
    return {"items": items}


def _search_via_legacy_http(topic: str, token: str) -> dict[str, Any]:
    try:
        payload = http.get(
            "https://api.xquik.invalid/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": topic},
            timeout=30,
            retries=1,
        )
    except http.HTTPError as exc:
        if exc.status_code in (401, 403):
            return {"items": [], "error": "auth failed"}
        return {"items": [], "error": str(exc)}
    raw_tweets = payload.get("tweets")
    if not isinstance(raw_tweets, list):
        return {"items": []}
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, tweet in enumerate(raw_tweets):
        tweet_id = str((tweet or {}).get("id") or "")
        if not tweet_id or tweet_id in seen_ids:
            continue
        seen_ids.add(tweet_id)
        parsed = _parse_tweet(tweet, len(items), topic)
        if parsed:
            items.append(parsed)
    return {"items": items}


def search_xquik(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = "",
) -> dict[str, Any]:
    """Search X while preserving the Xquik function contract."""
    del to_date
    if not token:
        return {"items": [], "error": "No XQUIK_API_KEY configured"}
    if token.startswith("sk-"):
        return _search_via_aisa(topic, from_date, depth, token)
    return _search_via_legacy_http(topic, token)


def search_and_enrich(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = "",
) -> dict[str, Any]:
    return search_xquik(topic, from_date, to_date, depth=depth, token=token)


def parse_xquik_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    return response.get("items", [])
