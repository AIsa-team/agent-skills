#!/usr/bin/env python3
"""
FinReport — Perplexity Sonar API wrapper.

Provides two analysis functions:
  - get_market_narrative: Sonar Pro deep-dive with citations
  - get_macro_context:    Sonar lightweight macro/sector summary
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


BASE_URL = "https://api.aisa.one/apis/v1"


def _get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY")
    if not key:
        raise ValueError(
            "AISA_API_KEY environment variable is not set. "
            "Add it to your shell profile or .env file."
        )
    return key


def _sonar_request(
    endpoint: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int = 120,
) -> str:
    """POST to a Perplexity Sonar endpoint; return the assistant message content.

    Retries once on 502/503/504. Raises RuntimeError on persistent failure.
    """
    api_key = _get_api_key()
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FinReport/1.0",
    }
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}", data=body, headers=headers, method="POST"
    )

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result: Dict[str, Any] = json.loads(response.read().decode("utf-8"))
                try:
                    return result["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    return json.dumps(result, indent=2)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {502, 503, 504} and attempt == 0:
                time.sleep(5)
                continue
            raise RuntimeError(
                f"Perplexity API error {exc.code}: {error_body[:200]}"
            ) from exc
        except urllib.error.URLError as exc:
            if attempt == 0:
                time.sleep(5)
                continue
            raise RuntimeError(f"Network error: {exc.reason}") from exc

    raise RuntimeError("Perplexity request failed after retry.")


def get_market_narrative(ticker: str, company_name: str) -> str:
    """
    Run Perplexity Sonar Pro analysis for a company or asset.

    Covers: recent developments, competitive landscape, key risks,
    analyst/investor sentiment. Returns structured markdown with citations.
    """
    return _sonar_request(
        "/perplexity/sonar-pro",
        "sonar-pro",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior financial analyst. Respond with structured "
                    "markdown. Always cite your sources inline."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyze {company_name} ({ticker}). Cover: "
                    "(1) recent business developments and news, "
                    "(2) competitive landscape and market position, "
                    "(3) key risks and headwinds, "
                    "(4) analyst and investor sentiment. "
                    "Be specific and cite your sources."
                ),
            },
        ],
    )


def _parse_risk_json(raw: str) -> Dict[str, str]:
    """Extract the JSON risk object from a Perplexity response.

    Handles three cases in order:
      1. Raw string is valid JSON directly.
      2. JSON is wrapped in a markdown code fence (```json ... ```).
      3. First { ... } block found anywhere in the string.
    Returns a dict with keys: market, macro, regulatory, competitive.
    Missing or unparseable values fall back to empty strings.
    """
    required = ("market", "macro", "regulatory", "competitive")

    def _to_dict(obj: Any) -> Dict[str, str]:
        return {k: str(obj.get(k, "")).strip() for k in required}

    # 1. Direct parse
    try:
        parsed = json.loads(raw.strip())
        if isinstance(parsed, dict):
            return _to_dict(parsed)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fence
    text = raw
    for fence in ("```json", "```"):
        idx = text.find(fence)
        if idx != -1:
            inner_start = idx + len(fence)
            inner_end = text.find("```", inner_start)
            if inner_end > inner_start:
                text = text[inner_start:inner_end].strip()
                break
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return _to_dict(parsed)
    except json.JSONDecodeError:
        pass

    # 3. Extract first { … } block
    brace_start = raw.find("{")
    brace_end = raw.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            parsed = json.loads(raw[brace_start : brace_end + 1])
            if isinstance(parsed, dict):
                return _to_dict(parsed)
        except json.JSONDecodeError:
            pass

    return {k: "" for k in required}


def get_risk_factors(ticker: str, narrative: str) -> Dict[str, str]:
    """Call Perplexity Sonar to extract 4 company-specific risk factors as JSON.

    Returns a dict with keys: market, macro, regulatory, competitive.
    Each value is one complete sentence under 150 characters.
    Falls back to empty strings per key on parse failure (caller supplies defaults).
    """
    raw = _sonar_request(
        "/perplexity/sonar",
        "sonar",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial risk analyst. "
                    "Respond with only a valid JSON object — no explanation, no markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Given this analysis for {ticker}, return exactly 4 risk factors "
                    f"as a JSON object with these exact keys: "
                    f"market, macro, regulatory, competitive. "
                    f"Each value must be one complete sentence under 150 characters, "
                    f"specific to {ticker}. Return only the JSON object.\n\n"
                    f"{narrative[:3000]}"
                ),
            },
        ],
    )
    return _parse_risk_json(raw)


def get_macro_context(ticker: str, sector: str) -> str:
    """
    Run Perplexity Sonar analysis for macro and sector context.

    Covers: Fed policy, sector trends, regulatory developments.
    Returns markdown text.
    """
    return _sonar_request(
        "/perplexity/sonar",
        "sonar",
        messages=[
            {
                "role": "user",
                "content": (
                    f"What is the current macroeconomic environment for the "
                    f"{sector} sector and how does it affect {ticker}? "
                    "Include relevant Fed policy, sector trends, and any "
                    "regulatory developments."
                ),
            }
        ],
    )
