"""AISA-backed X/Twitter discovery wrapper."""

from __future__ import annotations

import json
from typing import Any

from . import aisa

AISA_X_DEFAULT = "twitter-advanced-search"


def search_x(
    api_key: str,
    model: str,
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Search X for relevant posts using the AISA Twitter proxy."""
    del model, to_date
    if mock_response is not None:
        return mock_response
    return aisa.search_twitter(api_key, topic, from_date, depth=depth)


def parse_x_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse AISA Twitter response to normalized X items.

    Accepts both the new AISA-native response and the legacy xAI JSON envelope
    used by older tests/fixtures.
    """
    if "output" in response:
        try:
            for item in response.get("output") or []:
                if not isinstance(item, dict):
                    continue
                for content in item.get("content") or []:
                    if not isinstance(content, dict):
                        continue
                    text = content.get("text")
                    if not isinstance(text, str):
                        continue
                    payload = json.loads(text)
                    raw_items = payload.get("items") or []
                    parsed: list[dict[str, Any]] = []
                    for index, raw in enumerate(raw_items):
                        if not isinstance(raw, dict):
                            continue
                        engagement = raw.get("engagement") or {}
                        parsed.append(
                            {
                                "id": raw.get("id") or f"AX{index + 1}",
                                "text": str(raw.get("text") or "")[:500],
                                "url": raw.get("url") or "",
                                "author_handle": raw.get("author_handle") or "",
                                "date": raw.get("date"),
                                "engagement": {
                                    "likes": engagement.get("likes"),
                                    "reposts": engagement.get("reposts"),
                                    "replies": engagement.get("replies"),
                                    "quotes": engagement.get("quotes"),
                                },
                                "why_relevant": raw.get("why_relevant") or "AIsa Twitter search",
                                "relevance": raw.get("relevance"),
                            }
                        )
                    return [item for item in parsed if item.get("url")]
        except (json.JSONDecodeError, TypeError, ValueError):
            return []
    return aisa.parse_twitter_response(response)
