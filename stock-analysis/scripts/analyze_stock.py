#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
Stock & crypto analysis using AIsa API (Yahoo Finance + Financial Data tools).

Usage:
    uv run analyze_stock.py AAPL
    uv run analyze_stock.py AAPL MSFT GOOGL
    uv run analyze_stock.py BTC-USD ETH-USD
    uv run analyze_stock.py AAPL --output json
    uv run analyze_stock.py AAPL --fast
"""

import argparse
import json
import os
import re
import sys
from typing import Any
from openai import OpenAI


SYSTEM_PROMPT = """You are a professional equity research analyst with access to real-time financial data tools.

When asked to analyze a stock or cryptocurrency, use your built-in financial data tools to fetch:
- Current price, volume, market cap
- Earnings history (actual vs estimated EPS, beat/miss)
- Fundamental metrics (P/E ratio, profit margins, revenue growth, debt/equity)
- Analyst ratings and consensus price targets
- Historical price action (52-week high/low, RSI, recent % change)
- Sector/index benchmarks (SPY, QQQ, sector ETF performance)
- Market sentiment indicators (VIX level, Fear & Greed index)
- Short interest and insider trading activity
- Recent news headlines (last 24–48 hours)
- For crypto: market cap tier, BTC correlation, 24h change

Always use live data. Do not use outdated knowledge — fetch current values with your tools."""


ANALYSIS_PROMPT = """Perform a comprehensive {asset_type} analysis for: {tickers}

## Required Output Structure

### For each ticker, produce:

---
## {ticker} Analysis

**Current Price:** [fetch live]
**Asset Type:** {asset_type}

### 8-Dimension Scoring (stocks) / 3-Dimension Scoring (crypto)

For STOCKS, score each dimension 0–10 and apply these weights:

| # | Dimension | Weight | Score | Weighted |
|---|-----------|--------|-------|---------|
| 1 | Earnings Surprise | 30% | X.X | X.X |
| 2 | Fundamentals (P/E, margins, growth) | 20% | X.X | X.X |
| 3 | Analyst Sentiment | 20% | X.X | X.X |
| 4 | Historical Patterns | 10% | X.X | X.X |
| 5 | Market Context (VIX, SPY/QQQ) | 10% | X.X | X.X |
| 6 | Sector Performance | 15% | X.X | X.X |
| 7 | Momentum (RSI, 52w range) | 15% | X.X | X.X |
| 8 | Sentiment (Fear/Greed, shorts, insiders) | 10% | X.X | X.X |
| | **TOTAL** | **100%** | — | **X.X** |

For CRYPTO, use:
| # | Dimension | Weight | Score | Weighted |
|---|-----------|--------|-------|---------|
| 1 | Market Cap & Category | 40% | X.X | X.X |
| 2 | BTC Correlation (30-day) | 30% | X.X | X.X |
| 3 | Momentum (RSI, range, volume) | 30% | X.X | X.X |
| | **TOTAL** | **100%** | — | **X.X** |

### Key Findings (3–5 bullets per dimension, data-backed)

[Provide specific numbers for each dimension, e.g., "RSI at 67 (approaching but not yet overbought)", "P/E of 28x vs sector average 31x", "3 of last 4 quarters beat EPS estimates by >5%"]

### ⚠️ Risk Flags (auto-detect these)
- [ ] Pre-earnings: Check if earnings date is within 14 days
- [ ] Post-spike: Flag if price is up >15% in last 5 trading days
- [ ] Overbought: Flag if RSI > 70 AND price near 52-week high (>95%)
- [ ] Risk-Off: Flag if GLD, TLT, UUP are all trending up (flight to safety)
- [ ] Breaking News: Flag any crisis/negative keywords in recent headlines

### 🎯 Final Recommendation

**Score:** X.X / 10
**Signal:** [BUY / HOLD / SELL]
**Confidence:** [High / Medium / Low]

> [2–3 sentence summary of the recommendation rationale]

**Entry:** [suggested price range or "at market" if BUY]
**Target:** [12-month price target if available from analysts]
**Stop:** [suggested stop-loss level]

---

{compare_note}

⚠️ NOT FINANCIAL ADVICE. For informational purposes only. Always do your own research."""


def get_client() -> OpenAI:
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("❌ Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("   Set it with: export AISA_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("AISA_BASE_URL", "https://api.aisa.one/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def _extract_balanced_json(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def extract_json_block(text: str) -> dict[str, Any]:
    candidates: list[str] = []

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.append(fenced.group(1))

    generic_fenced = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
    if generic_fenced:
        candidates.append(generic_fenced.group(1))

    balanced = _extract_balanced_json(text)
    if balanced:
        candidates.append(balanced)

    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    raise ValueError("No JSON block found in model output.")


def detect_asset_type(ticker: str) -> str:
    t = ticker.upper()
    if t.endswith("-USD") and t[:-4].isalpha():
        return "crypto"
    return "stock"


def analyze(tickers: list[str], output_format: str = "text", fast: bool = False) -> str:
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")

    # Determine asset types
    types = set(detect_asset_type(t) for t in tickers)
    asset_type = "mixed" if len(types) > 1 else types.pop()
    ticker_str = ", ".join(tickers)

    compare_note = ""
    if len(tickers) > 1:
        compare_note = f"\n### Comparison Summary\nAfter analyzing all {len(tickers)} tickers above, provide a ranked comparison table:\n| Ticker | Score | Signal | Key Strength | Key Risk |\n|--------|-------|--------|-------------|----------|\n... and a 2-sentence verdict on which is the best pick and why.\n"

    fast_note = ""
    if fast:
        fast_note = "\n[FAST MODE: Skip insider trading analysis and detailed news breakdown. Focus on price, fundamentals, and analyst data only for speed.]"

    prompt = ANALYSIS_PROMPT.format(
        tickers=ticker_str,
        ticker=tickers[0] if len(tickers) == 1 else "each ticker",
        asset_type=asset_type,
        compare_note=compare_note,
    ) + fast_note

    response_kwargs: dict[str, Any] = {}
    if output_format == "json":
        prompt += (
            "\n\nReturn ONLY valid JSON. Do not include markdown fences, tables, commentary, or prose outside the JSON object."
            "\nUse this exact shape:\n"
            "{\"tickers\": [{\"ticker\": \"AAPL\", \"score\": 7.2, \"signal\": \"BUY\", \"confidence\": \"High\", "
            "\"price\": 195.5, \"target\": 220.0, \"stop\": 175.0, \"risk_flags\": [\"Overbought\"], "
            "\"summary\": \"One short rationale sentence.\"}]}"
        )
        response_kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            **response_kwargs,
        )
        content = response.choices[0].message.content or ""
        if output_format == "json":
            return json.dumps(extract_json_block(content), indent=2, ensure_ascii=False)
        return content
    except Exception as e:
        print(f"❌ AIsa API error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Analyze stocks/crypto via AIsa API")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols (e.g., AAPL BTC-USD)")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--fast", action="store_true", help="Skip slow analyses (insider, news)")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers]
    print(f"🔍 Analyzing {', '.join(tickers)} via AIsa API...\n", file=sys.stderr)

    result = analyze(tickers, output_format=args.output, fast=args.fast)
    print(result)


if __name__ == "__main__":
    main()
