"""AIsa API helpers for chat, search, and social retrieval."""

from __future__ import annotations

import json
import math
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from . import dates, http

AISA_BASE_URL = "https://api.aisa.one"
AISA_CHAT_COMPLETIONS_URL = f"{AISA_BASE_URL}/v1/chat/completions"
AISA_TWITTER_SEARCH_URL = f"{AISA_BASE_URL}/apis/v1/twitter/tweet/advanced_search"
AISA_YOUTUBE_SEARCH_URL = f"{AISA_BASE_URL}/apis/v1/youtube/search"
AISA_TAVILY_SEARCH_URL = f"{AISA_BASE_URL}/apis/v1/tavily/search"
AISA_POLYMARKET_SEARCH_URL = f"{AISA_BASE_URL}/apis/v1/polymarket/public-search"
AISA_CHAT_TIMEOUT = 60
AISA_CHAT_RETRIES = 1

DEPTH_LIMITS = {
    "quick": 6,
    "default": 12,
    "deep": 24,
}


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def chat_completion(
    api_key: str,
    model: str,
    prompt: str,
    *,
    response_mime_type: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    if response_mime_type == "application/json":
        payload["response_format"] = {"type": "json_object"}
    return http.post(
        AISA_CHAT_COMPLETIONS_URL,
        payload,
        headers=_headers(api_key),
        timeout=AISA_CHAT_TIMEOUT,
        retries=AISA_CHAT_RETRIES,
        max_429_retries=1,
    )


def search_twitter(
    api_key: str,
    query: str,
    from_date: str,
    depth: str = "default",
) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "query": f"{query} since:{from_date}",
            "queryType": "Top",
            "count": DEPTH_LIMITS.get(depth, DEPTH_LIMITS["default"]),
        }
    )
    return http.get(
        f"{AISA_TWITTER_SEARCH_URL}?{params}",
        headers=_headers(api_key),
        timeout=45,
    )


def search_youtube(
    api_key: str,
    query: str,
    depth: str = "default",
) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "engine": "youtube",
            "q": query,
        }
    )
    response = http.get(
        f"{AISA_YOUTUBE_SEARCH_URL}?{params}",
        headers=_headers(api_key),
        timeout=45,
    )
    response["_observed_at"] = datetime.now(timezone.utc).isoformat()
    return response


def search_tavily(
    api_key: str,
    query: str,
    date_range: tuple[str, str] | None = None,
    *,
    limit: int | None = None,
    count: int = 5,
    topic: str = "news",
) -> dict[str, Any]:
    max_results = min(20, max(0, limit if limit is not None else count))
    payload: dict[str, Any] = {
        "query": query,
        "topic": topic,
        "max_results": max_results,
        "include_raw_content": False,
    }
    if date_range:
        payload["start_date"] = date_range[0]
        payload["end_date"] = date_range[1]
    return http.post(
        AISA_TAVILY_SEARCH_URL,
        payload,
        headers=_headers(api_key),
        timeout=45,
    )


def search_polymarket(
    api_key: str,
    query: str,
) -> dict[str, Any]:
    params = urllib.parse.urlencode({"q": query, "events_status": "active", "keep_closed_markets": 0,
                                    "limit_per_type": 12, "search_profiles": "false", "search_tags": "false"})
    response = http.get(
        f"{AISA_POLYMARKET_SEARCH_URL}?{params}",
        headers=_headers(api_key),
        timeout=30,
    )
    response["_observed_at"] = datetime.now(timezone.utc).isoformat()
    return response


def parse_twitter_response(response: dict[str, Any], *, query: str = "") -> list[dict[str, Any]]:
    raw_items = (
        response.get("tweets")
        or response.get("results")
        or response.get("data")
        or response.get("items")
        or []
    )
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        text = _first(item, "full_text", "text", "content")
        url = _first(item, "url", "tweet_url")
        if not url:
            tweet_id = _first(item, "tweet_id", "id", "rest_id")
            handle = _handle_from_item(item)
            if tweet_id and handle:
                url = f"https://x.com/{handle}/status/{tweet_id}"
        if not url:
            continue
        items.append(
            {
                "id": f"AX{index + 1}",
                "text": str(text or "").strip()[:500],
                "url": url,
                "author_handle": _handle_from_item(item),
                "date": _normalize_date(_first(item, "createdAt", "created_at", "date", "published_at")),
                "engagement": {
                    "likes": _to_int(_first(item, "likeCount", "favorite_count", "likes", "like_count")),
                    "reposts": _to_int(_first(item, "retweetCount", "retweet_count", "reposts")),
                    "replies": _to_int(_first(item, "replyCount", "reply_count", "replies")),
                    "quotes": _to_int(_first(item, "quoteCount", "quote_count", "quotes")),
                },
                "why_relevant": "AIsa Twitter search",
                "relevance": 0.8 if not query else _query_relevance(query, str(text or "")),
            }
        )
    return items


def parse_youtube_response(response: dict[str, Any], *, topic: str, from_date: str,
                           to_date: str | None = None) -> list[dict[str, Any]]:
    observed_at = dates.parse_date(response.get("_observed_at")) or datetime.now(timezone.utc)
    to_date = to_date or observed_at.date().isoformat()
    raw_items = (
        response.get("video_results")
        or response.get("videos")
        or response.get("items")
        or response.get("results")
        or []
    )
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        video_id = _first(item, "videoId", "id")
        url = _first(item, "link", "url")
        if not url and video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
        if not url:
            continue
        title = str(_first(item, "title", "name") or "")
        snippet = str(_first(item, "snippet", "description") or "")[:500]
        channel = _first(item, "channel", "channel_name", "author")
        if isinstance(channel, dict):
            channel = _first(channel, "title", "name")
        published = _first(item, "published_time", "publishedDate", "published_at", "date")
        parsed_date = dates.parse_date(published, reference_time=observed_at)
        items.append(
            {
                "video_id": video_id or f"aisa-{index + 1}",
                "title": title,
                "url": url,
                "channel_name": str(channel or ""),
                "date": parsed_date.date().isoformat() if parsed_date else None,
                "date_confidence": "med" if published and "ago" in str(published).lower() else "high",
                "engagement": {
                    "views": _to_int(_first(item, "views", "view_count")),
                    "likes": _to_int(_first(item, "likes", "like_count")),
                    "comments": None,
                },
                "duration": _first(item, "duration", "length"),
                "relevance": _youtube_relevance(topic, title, snippet),
                "why_relevant": "AIsa YouTube search",
                "description": snippet,
            }
        )
    return [item for item in items if item.get("date") and from_date <= item["date"] <= to_date]


def parse_tavily_response(response: dict[str, Any], *, date_range: tuple[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_items = response.get("results") or response.get("data") or []
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        url = _first(item, "url", "link")
        if not url:
            continue
        pub_date = _normalize_date(_first(item, "published_date", "date"))
        if pub_date and not (date_range[0] <= pub_date <= date_range[1]):
            continue
        items.append(
            {
                "id": f"AT{index + 1}",
                "title": str(_first(item, "title") or ""),
                "url": url,
                "source_domain": urllib.parse.urlparse(url).netloc.strip().lower(),
                "snippet": str(_first(item, "content", "snippet", "raw_content") or "")[:500],
                "date": pub_date,
                "relevance": 0.8,
                "why_relevant": "AIsa Tavily search",
            }
        )
    artifact = {"label": "aisa-tavily", "webSearchQueries": [response.get("query", "")], "resultCount": len(items)}
    return items, artifact


def parse_polymarket_response(response: dict[str, Any] | list[Any], *, topic: str = "",
                              observed_at: str | None = None) -> list[dict[str, Any]]:
    """Flatten public-search events and market arrays without confusing resolution with publication.

    Only a timestamp recorded when the response was retrieved establishes an
    observation date. Re-parsing an undated or cached payload does not make it fresh.
    """
    if isinstance(response, list):
        raw_items = response
    else:
        observed_at = observed_at or response.get("_observed_at")
        raw_items = (response.get("events") or response.get("markets") or response.get("data")
                     or response.get("results") or [])
    observations: list[tuple[dict[str, Any], str | None]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("markets"), list):
            if item.get("closed") is True:
                continue
            observations.extend((market, item.get("slug")) for market in item["markets"]
                                if isinstance(market, dict))
        else:
            observations.append((item, None))
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, (item, event_slug) in enumerate(observations):
        if item.get("closed") is True or item.get("active") is False:
            continue
        question = str(_first(item, "question", "title", "name") or "").strip()
        if not question:
            continue
        url = _first(item, "url")
        slug = _first(item, "market_slug", "slug")
        market_id = _first(item, "id", "conditionId", "condition_id", "market_id")
        if not url:
            if event_slug and slug:
                url = f"https://polymarket.com/event/{event_slug}/{slug}"
            elif slug:
                url = f"https://polymarket.com/event/{slug}"
        if not url:
            continue
        identity = str(market_id or url)
        if identity in seen:
            continue
        seen.add(identity)
        outcomes = _json_array(item.get("outcomes"))
        prices = _json_array(item.get("outcomePrices"))
        outcome_prices = [(str(name), price) for name, raw_price in zip(outcomes, prices)
                          if (price := _normalize_probability(raw_price)) is not None]
        probability = next((price for name, price in outcome_prices if name.lower() == "yes"), None)
        if probability is None:
            probability = _normalize_probability(_first(item, "probability", "yes_price", "price"))
        items.append(
            {
                "id": f"AP{market_id or index + 1}",
                "title": question,
                "question": question,
                "url": url,
                "date": None,
                "observed_at": observed_at,
                "end_date": _normalize_date(_first(item, "endDate", "end_date", "end_time")),
                "probability": probability,
                "outcome_prices": outcome_prices,
                "volume": _to_float(_first(item, "volumeNum", "volume", "volume_total")),
                "liquidity": _to_float(_first(item, "liquidityNum", "liquidity")),
                "container": "Polymarket",
                "why_relevant": "Current Polymarket market observation via AIsa; not historical odds",
                "metadata": {"retrieval_method": "native_api", "date_kind": "market_observation"},
                "relevance": _query_relevance(topic, question) if topic else 0.8,
            }
        )
    return items


def _handle_from_item(item: dict[str, Any]) -> str:
    author = item.get("author") or item.get("user")
    if isinstance(author, dict):
        handle = _first(author, "userName", "screen_name", "username")
        if handle:
            return str(handle).lstrip("@")
    return str(
        _first(item, "screen_name", "author_handle", "username", "user_name", "handle") or ""
    ).lstrip("@")


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize_date(value: object) -> str | None:
    if value is None:
        return None
    parsed = dates.parse_date(str(value).strip())
    if not parsed:
        return None
    return parsed.date().isoformat()


def _to_int(value: Any) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return int(number) if math.isfinite(number) and number >= 0 and number.is_integer() else None
    except (TypeError, ValueError, OverflowError):
        return None


def _to_float(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and number >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _normalize_probability(value: Any) -> float | None:
    prob = _to_float(value)
    if prob is None:
        return None
    return prob if 0 <= prob <= 1 else None


def _json_array(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return value if isinstance(value, list) else []


def _query_relevance(topic: str, text: str) -> float:
    topic_tokens = {token for token in topic.lower().split() if len(token) > 2}
    if not topic_tokens:
        return 0.8
    text_lower = text.lower()
    overlap = sum(1 for token in topic_tokens if token in text_lower)
    return min(1.0, max(0.4, overlap / max(1, len(topic_tokens))))


def _youtube_relevance(topic: str, title: str, snippet: str) -> float:
    text = f"{title} {snippet}".strip()
    base = _query_relevance(topic, text)
    if re_match := any(marker in text.lower() for marker in ("review", "breakdown", "reaction", "explained")):
        return min(1.0, base + 0.1)
    return base
