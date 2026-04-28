#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
🔥 Hot Scanner — Find viral trending stocks & crypto via AIsa API.

Usage:
    uv run hot_scanner.py
    uv run hot_scanner.py --focus crypto
    uv run hot_scanner.py --focus stocks
    uv run hot_scanner.py --output json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from openai import OpenAI


SYSTEM_PROMPT = """You are a real-time market intelligence analyst with access to live financial data tools.
Use your built-in tools to scan Yahoo Finance, CoinGecko, and financial news sources for trending
and high-momentum assets RIGHT NOW. Fetch current data — do not use outdated knowledge."""


HOT_SCANNER_PROMPT = """🔥 Run a Hot Scanner: find the most trending and high-momentum {focus} right now.

Use your financial data tools to pull the following live data:

**For Stocks:**
- Yahoo Finance: Top gainers (today, >3% move), top losers, most active by volume
- Unusual volume: stocks trading at >2x their 30-day average volume
- Pre/post-market movers (if available)
- Recent IPOs or earnings-driven moves

**For Crypto:**
- CoinGecko: Trending coins (search volume), top 24h gainers (>10%), biggest 24h losers
- Bitcoin dominance and 24h BTC price change (sets the crypto mood)
- Top 5 coins by 24h trading volume

**News Catalysts:**
- Pull recent finance headlines (last 6 hours) and extract ticker mentions
- Flag any breaking news driving price action

---

## Required Output Format

### 🔥 Hot Scanner Report
**Timestamp:** {timestamp}
**Market Status:** [Pre-market / Open / After-hours / Closed]

---

### 📈 Top Stock Movers (Today)

**🚀 Gainers:**
| Ticker | Company | Change | Price | Volume | Catalyst |
|--------|---------|--------|-------|--------|----------|
| ... | ... | +XX% | $XX | XXM | [reason] |
(list top 5–8)

**📉 Losers:**
| Ticker | Company | Change | Price | Volume | Catalyst |
|--------|---------|--------|-------|--------|----------|
(list top 5)

**🔊 Most Active (by volume):**
| Ticker | Company | Volume | vs 30d Avg | Change |
|--------|---------|--------|-----------|--------|
(list top 5)

---

### 🪙 Crypto Highlights

**BTC:** $XX,XXX ({btc_change}% 24h) | BTC Dominance: XX%
**Overall Crypto Mood:** [Bullish / Bearish / Mixed]

**🔥 Trending Coins (CoinGecko):**
| Rank | Coin | Symbol | 24h Change | Market Cap Tier | Category |
|------|------|--------|-----------|----------------|----------|
(list top 8)

**⬆️ Top Gainers (24h):**
| Coin | Change | Price | Volume |
(list top 5)

**⬇️ Top Losers (24h):**
| Coin | Change | Price | Volume |
(list top 3)

---

### 📰 News-Driven Movers
List 5–8 news items with the ticker they affect and expected impact:
- [TICKER] "Headline text" → [bullish/bearish], impact: [high/medium/low]

---

### 🎯 Top 5 Watchlist Picks (Right Now)
Based on all the above data, pick the 5 most interesting tickers to watch today:

| # | Ticker | Type | Why It's Hot | Risk Level |
|---|--------|------|-------------|------------|
| 1 | ... | Stock/Crypto | [reason] | High/Med/Low |

### ⚡ Quick Take
[2–3 sentence market summary: What's the dominant theme today? Any sector rotation? Crypto correlated with stocks or diverging?]

---
⚠️ NOT FINANCIAL ADVICE. For informational purposes only."""


def get_client() -> OpenAI:
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("❌ Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("   Set it with: export AISA_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("AISA_BASE_URL", "https://api.aisa.one/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_json_block(text: str) -> dict:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        inline = re.search(r"(\{.*\})\s*$", text, re.DOTALL)
        candidate = inline.group(1) if inline else None
    if candidate is None:
        raise ValueError("No JSON block found in model output.")
    return json.loads(candidate)


def run_hot_scanner(focus: str = "both", output_format: str = "text") -> str:
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")

    focus_map = {
        "both": "stocks and cryptocurrencies",
        "stocks": "stocks (equities only, no crypto)",
        "crypto": "cryptocurrencies (no stocks)",
    }
    focus_str = focus_map.get(focus, "stocks and cryptocurrencies")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    prompt = HOT_SCANNER_PROMPT.format(
        focus=focus_str,
        timestamp=timestamp,
        btc_change="fetch live",
    )

    if output_format == "json":
        prompt += (
            "\n\nAfter the full report, append a compact JSON summary:\n"
            "```json\n"
            "{\"timestamp\": \"...\", \"top_stocks\": [{\"ticker\": \"NVDA\", \"change_pct\": 8.4, "
            "\"catalyst\": \"earnings beat\"}], "
            "\"top_crypto\": [{\"symbol\": \"SOL\", \"change_24h\": 12.1}], "
            "\"watchlist\": [\"NVDA\", \"TSLA\", \"SOL\", \"BTC-USD\", \"AAPL\"]}\n"
            "```"
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        if output_format == "json":
            return json.dumps(extract_json_block(content), indent=2, ensure_ascii=False)
        return content
    except Exception as e:
        print(f"❌ AIsa API error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="🔥 Hot Scanner — trending stocks & crypto via AIsa API")
    parser.add_argument("--focus", choices=["both", "stocks", "crypto"], default="both")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    print("🔍 Scanning for hot trends via AIsa API...\n", file=sys.stderr)
    result = run_hot_scanner(focus=args.focus, output_format=args.output)
    print(result)


if __name__ == "__main__":
    main()
