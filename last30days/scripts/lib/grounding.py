"""Web search retrieval via the AIsa Tavily proxy."""

from __future__ import annotations

from urllib.parse import urlparse

from . import aisa, dates


def web_search(
    query: str,
    date_range: tuple[str, str],
    config: dict,
    backend: str = "auto",
) -> tuple[list[dict], dict]:
    """Run grounded web search through AIsa only."""
    if backend == "none":
        return [], {}
    if backend not in {"auto", "aisa"}:
        raise ValueError(f"Unsupported web backend: {backend!r}")
    key = config.get("AISA_API_KEY")
    if not key:
        if backend == "aisa":
            raise RuntimeError("AISA_API_KEY is required when web_backend='aisa'")
        return [], {}
    response = aisa.search_tavily(key, query, date_range)
    items, artifact = aisa.parse_tavily_response(response, date_range=date_range)
    if items:
        return items, artifact
    artifact = dict(artifact or {})
    artifact.setdefault("label", "aisa-tavily")
    artifact["warning"] = (
        "AISA Tavily search returned 0 items. Check whether this AISA/Tavily key has web-search access "
        "or whether the query/date window is too strict."
    )
    return items, artifact


def _normalize_date(value: object) -> str | None:
    if value is None:
        return None
    parsed = dates.parse_date(str(value).strip())
    if not parsed:
        return None
    return parsed.date().isoformat()


def _in_date_range(pub_date: str | None, date_range: tuple[str, str]) -> bool:
    if not pub_date:
        return False
    return date_range[0] <= pub_date <= date_range[1]


def _domain(url: str) -> str:
    return urlparse(url).netloc.strip().lower()
