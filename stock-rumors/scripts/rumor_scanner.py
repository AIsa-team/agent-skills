#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai>=1.0.0",
# ]
# ///
"""
🔮 Rumor Scanner — early signals, M&A rumors, insider activity via AIsa API.

Usage:
    uv run rumor_scanner.py
    uv run rumor_scanner.py --output json
    uv run rumor_scanner.py --focus ma         # M&A only
    uv run rumor_scanner.py --focus insider    # Insider activity only
    uv run rumor_scanner.py --focus analyst    # Analyst actions only
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from openai import OpenAI


SYSTEM_PROMPT = """You are a market intelligence analyst specializing in early signal detection.
You have access to real-time financial data tools for fetching news, SEC filings, insider transactions,
analyst updates, and social sentiment signals.

Scan recent data (last 24–48 hours) aggressively for signals that precede mainstream coverage.
Use your tools to search for: M&A keywords, insider filings, analyst rating changes, unusual options activity,
and social media whispers. Always fetch live data."""


RUMOR_PROMPT = """🔮 Run a Rumor & Early Signal Scanner for {focus_desc}.

Scan the following sources using your financial data tools:

1. **M&A / Takeover Signals** (fetch recent news):
   - Keywords: "acquisition", "merger", "takeover bid", "buyout", "strategic review", "going private"
   - Unusual premium in options (call skew)
   - Halt & resume activity

2. **Insider Trading Activity** (SEC EDGAR / Form 4 filings):
   - Director/CEO/CFO purchases (especially open-market buys)
   - Cluster buying (multiple insiders buying same week)
   - 10b5-1 plan deviations

3. **Analyst Actions** (last 48 hours):
   - Rating upgrades / downgrades
   - Price target changes (especially >15% revisions)
   - Initiations with strong conviction
   - Rare double-upgrades (Buy→Strong Buy)

4. **Social & News Whispers**:
   - Finance news with phrases: "hearing that", "sources say", "according to people familiar", "rumored to"
   - Unusual spike in social mentions for a ticker
   - Pre-announcement leaks or "developing story" coverage

5. **Regulatory / SEC Activity**:
   - SEC investigations or subpoenas
   - Unusual 13D/13G filings (activist investors crossing 5% threshold)
   - Wells notices

---

## Required Output Format

### 🔮 Rumor & Early Signal Report
**Timestamp:** {timestamp}

---

### 🏢 M&A Signals

For each M&A signal found:
**[TICKER] — [Company Name]**
- **Signal Type:** Acquisition Target / Acquirer / Merger Talks / Strategic Review
- **Source:** [news source / filing / options data]
- **Details:** [what was reported]
- **Impact Score:** X/10
- **Evidence Quality:** Strong / Moderate / Weak (rumor)

---

### 👔 Insider Activity

For each notable insider transaction:
**[TICKER] — [Insider Name, Title]**
- **Action:** Purchased / Sold X,XXX shares @ $XX.XX
- **Date:** YYYY-MM-DD
- **Total Value:** $X,XXX,XXX
- **Context:** [first purchase in X months? cluster buying? etc.]
- **Signal Strength:** Bullish / Neutral / Bearish
- **Impact Score:** X/10

---

### 📊 Analyst Actions

For each significant analyst action:
**[TICKER]** | [Firm]: [Old Rating] → [New Rating] | PT: $XX → $XX
- **Rationale:** [brief reason given by analyst]
- **Impact Score:** X/10

---

### 🐦 Social & News Whispers

For each whisper signal:
- **[TICKER]:** "[relevant quote or headline]" — Source: [outlet/platform], Date: [date]
  - Keywords matched: [list]
  - Potential impact: [assessment]
  - Impact Score: X/10

---

### ⚖️ Regulatory / SEC Activity

For each regulatory signal:
- **[TICKER]:** [Filing type / action] — [details] — Impact Score: X/10

---

### 🎯 Top 5 Signals (Ranked by Impact)

| Rank | Ticker | Signal Type | Impact Score | Quality | Action |
|------|--------|-------------|-------------|---------|--------|
| 1 | ... | M&A Rumor | X/10 | Strong | Monitor |
| 2 | ... | Insider Buy | X/10 | Strong | Watch for confirmation |
...

**Impact Score Guide:**
- M&A/Takeover rumor: base +5
- Insider cluster buying: base +4
- Analyst double-upgrade: base +3
- "Sources say" language: base +2
- High social engagement bonus: +2

### 💡 Analyst Note
[2–3 sentences on the most actionable signals today and what to watch for as confirmation]

---
⚠️ NOT FINANCIAL ADVICE. Rumors are unconfirmed. Always verify before acting. For informational purposes only."""


FOCUS_DESCRIPTIONS = {
    "all": "all signal types (M&A, insider, analyst, social, regulatory)",
    "ma": "M&A and takeover signals only",
    "insider": "insider trading activity only (Form 4 filings, cluster buys)",
    "analyst": "analyst rating changes and price target revisions only",
    "social": "social media whispers and news leaks only",
}


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


def run_rumor_scanner(focus: str = "all", output_format: str = "text") -> str:
    client = get_client()
    model = os.environ.get("AISA_MODEL", "gpt-4o")

    focus_desc = FOCUS_DESCRIPTIONS.get(focus, FOCUS_DESCRIPTIONS["all"])
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    prompt = RUMOR_PROMPT.format(focus_desc=focus_desc, timestamp=timestamp)

    if output_format == "json":
        prompt += (
            "\n\nAfter the full report, append a compact JSON summary:\n"
            "```json\n"
            "{\"timestamp\": \"...\", \"signals\": ["
            "{\"ticker\": \"XYZ\", \"type\": \"MA\", \"impact_score\": 7, "
            "\"quality\": \"Moderate\", \"summary\": \"Acquisition rumor from Reuters\"}]}\n"
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
    parser = argparse.ArgumentParser(description="🔮 Rumor Scanner — early signals via AIsa API")
    parser.add_argument("--focus", choices=["all", "ma", "insider", "analyst", "social"], default="all")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()

    print("🔍 Scanning for early signals & rumors via AIsa API...\n", file=sys.stderr)
    result = run_rumor_scanner(focus=args.focus, output_format=args.output)
    print(result)


if __name__ == "__main__":
    main()
