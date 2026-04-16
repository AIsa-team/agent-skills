#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
Dividend analysis using AIsa API with Yahoo Finance tools.

Usage:
    uv run dividends.py JNJ
    uv run dividends.py JNJ PG KO MCD
    uv run dividends.py JNJ --output json
"""

import argparse
import os
import sys
from openai import OpenAI


SYSTEM_PROMPT = """You are a dividend investing specialist with access to real-time financial data tools.
Use your built-in financial data tools to fetch current dividend metrics, payout history,
earnings data, and company financials. Always retrieve live data — do not rely on outdated knowledge."""


DIVIDEND_PROMPT = """Perform a detailed dividend analysis for: {tickers}

For each ticker, fetch live data and produce this report:

---
## {ticker} — Dividend Analysis

**Company:** [full name]
**Current Price:** [live]
**Sector:** [sector]

### 📊 Core Dividend Metrics

| Metric | Value |
|--------|-------|
| Annual Dividend Per Share | $X.XX |
| Dividend Yield | X.XX% |
| Ex-Dividend Date | YYYY-MM-DD |
| Payment Frequency | Quarterly / Monthly / Annual |
| Last Payment Date | YYYY-MM-DD |

### 💰 Payout Analysis

| Metric | Value | Status |
|--------|-------|--------|
| Payout Ratio (Div/EPS) | XX% | safe / moderate / high / unsustainable |
| Free Cash Flow Payout | XX% | [assessment] |
| EPS (TTM) | $X.XX | — |
| Dividend Coverage Ratio | X.Xx | [safe if >2x] |

**Payout Status Thresholds:**
- ✅ Safe: < 50%
- ⚠️ Moderate: 50–70%
- 🔶 High: 70–90%
- 🔴 Unsustainable: > 100%

### 📈 Dividend Growth

| Period | CAGR |
|--------|------|
| 1-Year Growth | XX% |
| 3-Year CAGR | XX% |
| 5-Year CAGR | XX% |

**Consecutive Years of Dividend Increases:** X years
**Dividend Aristocrat Status:** Yes / No (requires 25+ consecutive years of increases)
**Dividend King Status:** Yes / No (requires 50+ years)

**Last 5 Annual Dividends:**
| Year | Annual Dividend | YoY Change |
|------|----------------|------------|
| 2024 | $X.XX | +X.X% |
| 2023 | $X.XX | +X.X% |
| ... | ... | ... |

### 🛡️ Safety Score (0–100)

Calculate a safety score based on:
- Payout ratio (lower = safer): up to 25 pts
- Free cash flow coverage: up to 20 pts
- Dividend growth consistency: up to 20 pts
- Balance sheet strength (debt/equity): up to 15 pts
- Earnings stability (EPS variance): up to 10 pts
- Years of consecutive increases: up to 10 pts

**Safety Score: XX / 100**
**Income Rating:** Excellent (80+) / Good (60–79) / Moderate (40–59) / Poor (<40)

### 📋 Key Findings
[3–5 bullet points with specific data supporting the rating]

### ⚠️ Risks
[Any concerns: dividend cut history, high debt, declining earnings, sector headwinds]

### 🎯 Income Investor Verdict
[2–3 sentence summary: is this a good dividend investment? Best for which type of income investor?]

---

{compare_note}

⚠️ NOT FINANCIAL ADVICE. For informational purposes only."""


def get_client() -> OpenAI:
    api_key = os.environ.get("AISA_API_KEY")
    if not api_key:
        print("❌ Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("   Set it with: export AISA_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("AISA_BASE_URL", "https://api.aisa.one/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def analyze_dividends(tickers: list[str], output_format: str = "text") -> str:
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")

    compare_note = ""
    if len(tickers) > 1:
        compare_note = (
            f"\n### Dividend Comparison Table\n"
            f"After the individual analyses, produce a ranked comparison:\n"
            f"| Ticker | Yield | Safety Score | 5Y CAGR | Payout Ratio | Income Rating |\n"
            f"|--------|-------|-------------|---------|-------------|---------------|\n"
            f"... and a 2-sentence verdict on the best income pick.\n"
        )

    prompt = DIVIDEND_PROMPT.format(
        tickers=", ".join(tickers),
        ticker=tickers[0] if len(tickers) == 1 else "each ticker",
        compare_note=compare_note,
    )

    if output_format == "json":
        prompt += (
            "\n\nAfter the full analysis, append a JSON summary block:\n"
            "```json\n"
            "{\"dividends\": [{\"ticker\": \"JNJ\", \"yield\": 3.1, \"annual_dividend\": 4.76, "
            "\"payout_ratio\": 45.2, \"payout_status\": \"safe\", \"safety_score\": 82, "
            "\"income_rating\": \"Excellent\", \"consecutive_years\": 62, "
            "\"growth_5y_cagr\": 5.8, \"ex_dividend_date\": \"2024-02-20\"}]}\n"
            "```"
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AIsa API error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dividend analysis via AIsa API")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols (e.g., JNJ PG KO)")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers]
    print(f"💰 Fetching dividend data for {', '.join(tickers)} via AIsa API...\n", file=sys.stderr)

    result = analyze_dividends(tickers, output_format=args.output)
    print(result)


if __name__ == "__main__":
    main()
