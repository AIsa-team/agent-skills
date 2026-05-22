#!/usr/bin/env python3
"""
Trend Forecaster — Multi-signal trend analysis powered by AIsa.

Usage:
    python3 trend_forecast.py "Will the Fed cut rates in 2026?"
    python3 trend_forecast.py "Tesla outlook" --output json
    python3 trend_forecast.py "AI chip market" --output markdown --save report.md

Chains 5 AIsa API endpoints:
  1. LLM Gateway  (query decomposition + synthesis)
  2. Prediction Markets  (contract odds)
  3. Twitter/X  (social sentiment)
  4. Tavily  (news velocity)
  5. MarketPulse  (stock/financial data)
"""

import argparse
import json
import sys
import os
import textwrap
from datetime import datetime

# Add scripts dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aisa_client as aisa


# ── Step 1: Decompose query into source-specific searches ───

DECOMPOSE_PROMPT = """You decompose a user's trend query into targeted search terms for 4 data sources.

Rules:
- prediction_market_query: Short phrase matching Polymarket/Kalshi contract titles (e.g. "Fed rate cut 2026", "Trump election")
- twitter_query: Hashtags, keywords, or phrases people tweet about this topic
- news_query: News-oriented search query for the last 7 days
- stock_symbols: List of 0-5 relevant ticker symbols. Empty list if not a financial topic.
  stock_symbols should only contain real stock ticker symbols (e.g. AAPL, NVDA, TLT).
  Do NOT use abbreviations for institutions like FED, SEC, or FDA.
  For Federal Reserve topics, use rate-sensitive ETFs like TLT, BND, or financials like JPM, GS.
  Return an empty list if no real tickers are relevant.
- topic_summary: One sentence describing what the user wants to forecast

Respond ONLY with valid JSON, no markdown fences:
{"prediction_market_query": "...", "twitter_query": "...", "news_query": "...", "stock_symbols": ["..."], "topic_summary": "..."}"""


def decompose_query(user_query):
    """Break user query into source-specific search terms via LLM."""
    print("\n⚙️  Decomposing query...", file=sys.stderr)
    result = aisa.llm_chat(
        messages=[
            {"role": "system", "content": DECOMPOSE_PROMPT},
            {"role": "user", "content": user_query},
        ],
        model="gpt-4.1-mini",
        temperature=0.2,
    )

    if isinstance(result, dict) and "error" in result:
        print(f"  ❌ LLM decomposition failed: {result}", file=sys.stderr)
        return None

    try:
        # Strip markdown fences if present
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"  ❌ Failed to parse decomposition: {e}", file=sys.stderr)
        print(f"  Raw response: {result[:300]}", file=sys.stderr)
        return None


# ── Step 2-5: Gather signals from each source ──────────────

def gather_signals(queries):
    """Gather data from all 4 sources. Returns dict of results."""
    signals = {
        "prediction_markets": None,
        "twitter": None,
        "news": None,
        "stocks": None,
    }
    sources_hit = 0

    # Prediction Markets
    print("\n📊 Querying prediction markets...", file=sys.stderr)
    pm_result = aisa.search_prediction_markets(queries["prediction_market_query"])
    if "error" not in pm_result:
        signals["prediction_markets"] = pm_result
        sources_hit += 1
    else:
        print(f"  ⚠️  Prediction markets unavailable: {pm_result.get('detail', 'unknown')}", file=sys.stderr)

    # Twitter / X
    print("\n🐦 Querying Twitter/X sentiment...", file=sys.stderr)
    tw_result = aisa.search_twitter(queries["twitter_query"])
    if "error" not in tw_result:
        signals["twitter"] = tw_result
        sources_hit += 1
    else:
        print(f"  ⚠️  Twitter unavailable: {tw_result.get('detail', 'unknown')}", file=sys.stderr)

    # News via Tavily
    print("\n📰 Querying news sources...", file=sys.stderr)
    news_result = aisa.search_news(queries["news_query"])
    if "error" not in news_result:
        signals["news"] = news_result
        sources_hit += 1
    else:
        print(f"  ⚠️  News unavailable: {news_result.get('detail', 'unknown')}", file=sys.stderr)

    # Stock data (if applicable) — MarketPulse /financial/ endpoints
    symbols = queries.get("stock_symbols", [])
    if symbols and symbols != [""] and len(symbols) > 0:
        print("\n💹 Querying market data...", file=sys.stderr)
        stock_data = {}
        for symbol in symbols[:5]:  # Cap at 5 symbols
            if not symbol:
                continue
            ticker_signals = {}
            prices = aisa.get_stock_prices(symbol, interval="day")
            if "error" not in prices:
                ticker_signals["prices"] = prices
            metrics = aisa.get_financial_metrics(symbol)
            if "error" not in metrics:
                ticker_signals["metrics"] = metrics
            news = aisa.get_stock_news(symbol)
            if "error" not in news:
                ticker_signals["news"] = news
            if ticker_signals:
                stock_data[symbol] = ticker_signals
        if stock_data:
            signals["stocks"] = stock_data
            sources_hit += 1
        else:
            print("  ⚠️  No stock data returned", file=sys.stderr)
    else:
        print("\n💹 Skipping stock data (non-financial topic)", file=sys.stderr)

    return signals, sources_hit


# ── Step 6: Synthesize forecast via LLM ─────────────────────

SYNTHESIS_PROMPT = """You are a trend analyst. Given structured signals from multiple data sources
(prediction markets, Twitter/X, news, and optionally stock data), produce a trend forecast.

Rules:
- Weigh sources by reliability: prediction markets > stock data > news > twitter
- Note when sources AGREE vs CONFLICT — agreement raises confidence
- Never present odds as certainties. Say "markets price at X%" not "X will happen"
- If fewer than 3 sources provided data, set confidence below 40 and note the limitation
- Include a financial disclaimer if stock data is involved

Respond ONLY with valid JSON, no markdown fences:
{
  "trend_direction": "bullish|bearish|neutral|mixed",
  "confidence_score": 0-100,
  "time_horizon": "short description of relevant timeframe",
  "headline": "one-line summary of the forecast",
  "analysis": "2-3 paragraph analysis synthesizing all signals",
  "signal_agreement": "high|medium|low",
  "key_signals": ["signal 1", "signal 2", "signal 3"],
  "risks": ["risk 1", "risk 2"],
  "data_gaps": ["any sources that returned no data"]
}"""


def synthesize_forecast(topic, signals, sources_hit):
    """Pass all signals to LLM for synthesis into a forecast."""
    print("\n🧠 Synthesizing forecast...", file=sys.stderr)

    # Build the signal summary for the LLM
    signal_text = f"TOPIC: {topic}\n\n"

    if signals["prediction_markets"]:
        signal_text += f"PREDICTION MARKETS:\n{json.dumps(signals['prediction_markets'], indent=2)[:2000]}\n\n"
    else:
        signal_text += "PREDICTION MARKETS: No data available\n\n"

    if signals["twitter"]:
        signal_text += f"TWITTER SENTIMENT:\n{json.dumps(signals['twitter'], indent=2)[:2000]}\n\n"
    else:
        signal_text += "TWITTER SENTIMENT: No data available\n\n"

    if signals["news"]:
        signal_text += f"NEWS VELOCITY:\n{json.dumps(signals['news'], indent=2)[:2000]}\n\n"
    else:
        signal_text += "NEWS VELOCITY: No data available\n\n"

    if signals["stocks"]:
        signal_text += f"STOCK/MARKET DATA:\n{json.dumps(signals['stocks'], indent=2)[:2000]}\n\n"
    else:
        signal_text += "STOCK/MARKET DATA: N/A\n\n"

    signal_text += f"SOURCES WITH DATA: {sources_hit}/4\n"

    result = aisa.llm_chat(
        messages=[
            {"role": "system", "content": SYNTHESIS_PROMPT},
            {"role": "user", "content": signal_text},
        ],
        model="gpt-4.1-mini",
        temperature=0.3,
    )

    if isinstance(result, dict) and "error" in result:
        return None

    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        print(f"  ❌ Failed to parse synthesis", file=sys.stderr)
        return None


# ── Step 7: Format output ───────────────────────────────────

def format_markdown(forecast, topic, signals=None, sources_hit=None):
    """Format forecast as readable markdown."""
    direction_emoji = {
        "bullish": "🟢",
        "bearish": "🔴",
        "neutral": "🟡",
        "mixed": "🔵",
    }

    emoji = direction_emoji.get(forecast.get("trend_direction", ""), "⚪")
    conf = forecast.get("confidence_score", "?")
    direction = forecast.get("trend_direction", "unknown").upper()

    lines = []
    lines.append(f"# 📈 TREND FORECAST: {forecast.get('headline', topic)}")
    lines.append("")
    lines.append(f"**Direction:** {emoji} {direction}")
    lines.append(f"**Confidence:** {conf}/100")
    lines.append(f"**Signal Agreement:** {forecast.get('signal_agreement', 'unknown')}")
    lines.append(f"**Time Horizon:** {forecast.get('time_horizon', 'not specified')}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Analysis")
    lines.append("")
    lines.append(forecast.get("analysis", "No analysis available."))
    lines.append("")
    lines.append("## Key Signals")
    lines.append("")
    for sig in forecast.get("key_signals", []):
        lines.append(f"- {sig}")
    lines.append("")
    lines.append("## Risks & Caveats")
    lines.append("")
    for risk in forecast.get("risks", []):
        lines.append(f"- {risk}")
    lines.append("")

    gaps = forecast.get("data_gaps", [])
    if gaps:
        lines.append("## Data Gaps")
        lines.append("")
        for gap in gaps:
            lines.append(f"- ⚠️ {gap}")
        lines.append("")

    if signals is not None:
        def status(key):
            return "✅" if signals.get(key) else "❌"

        hit = sources_hit if sources_hit is not None else sum(
            1 for k in ("prediction_markets", "twitter", "news", "stocks")
            if signals.get(k)
        )
        lines.append(f"## Data Sources ({hit}/4)")
        lines.append("")
        lines.append(f"- 📊 Prediction Markets: {status('prediction_markets')}")
        lines.append(f"- 🐦 Twitter/X Sentiment: {status('twitter')}")
        lines.append(f"- 📰 News (Tavily): {status('news')}")
        lines.append(f"- 💹 Market Data: {status('stocks')}")
        lines.append("")

    lines.append("---")
    lines.append("*This is informational analysis, not financial advice. "
                 "Prediction market odds reflect crowd sentiment, not certainties. "
                 "Powered by AIsa (aisa.one).*")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-signal trend forecasting powered by AIsa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python3 trend_forecast.py "Will the Fed cut rates?"
              python3 trend_forecast.py "Tesla outlook" --output json
              python3 trend_forecast.py "AI market" --save report.md
        """),
    )
    parser.add_argument("query", help="The trend/forecast question to analyze")
    parser.add_argument(
        "--output", choices=["markdown", "json"], default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument("--save", metavar="FILE", help="Save output to file")
    parser.add_argument(
        "--model", default="gpt-4.1-mini",
        help="LLM model for synthesis (default: gpt-4.1-mini)"
    )

    args = parser.parse_args()

    print(f"🔮 Trend Forecaster v1.0.0", file=sys.stderr)
    print(f"   Query: {args.query}", file=sys.stderr)
    print(f"   Powered by AIsa (aisa.one)", file=sys.stderr)

    # Step 1: Decompose
    queries = decompose_query(args.query)
    if not queries:
        print("❌ Failed to decompose query. Check your AISA_API_KEY.", file=sys.stderr)
        sys.exit(1)

    print(f"\n   Topic: {queries.get('topic_summary', args.query)}", file=sys.stderr)
    print(f"   Stocks: {queries.get('stock_symbols', [])}", file=sys.stderr)

    # Steps 2-5: Gather signals
    signals, sources_hit = gather_signals(queries)
    print(f"\n✅ Data gathered from {sources_hit}/4 sources", file=sys.stderr)

    if sources_hit < 2:
        print("⚠️  WARNING: Fewer than 2 sources returned data. "
              "Forecast will have very low confidence.", file=sys.stderr)

    # Step 6: Synthesize
    forecast = synthesize_forecast(
        queries.get("topic_summary", args.query),
        signals,
        sources_hit,
    )

    if not forecast:
        print("❌ Failed to synthesize forecast.", file=sys.stderr)
        sys.exit(1)

    # Step 7: Output
    if args.output == "json":
        output = json.dumps(forecast, indent=2)
    else:
        output = format_markdown(forecast, args.query, signals, sources_hit)

    print(output)

    if args.save:
        with open(args.save, "w") as f:
            f.write(output)
        print(f"\n💾 Saved to {args.save}", file=sys.stderr)


if __name__ == "__main__":
    main()
