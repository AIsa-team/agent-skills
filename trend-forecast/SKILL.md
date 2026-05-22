---
name: trend-forecast
description: >
  Multi-signal trend forecasting for autonomous agents. Combines prediction market
  odds, Twitter/X social sentiment, news velocity, and stock market data into a
  unified trend analysis with confidence scoring. Powered by AIsa — one API key,
  five data streams.
version: 1.0.0
triggers:
  - "forecast trend"
  - "predict what happens with"
  - "trend analysis for"
  - "what's the outlook on"
  - "will X happen"
  - "what are the odds of"
  - "sentiment analysis on"
  - "market outlook for"
tools:
  - bash
  - read
  - write
metadata:
  openclaw:
    emoji: "📈"
    requires:
      bins:
        - curl
        - python3
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# Trend Forecast

> Multi-signal trend analysis for autonomous agents. Powered by AIsa.
> One API key. Five data streams. Confidence-scored forecasts.

## Context

You are a trend forecasting agent. When the user asks about a topic's trajectory,
outlook, or probability, you gather signals from five independent data sources
through AIsa's unified API, then synthesize a forecast with a confidence score.

This skill is NOT a web search tool. It is a **multi-signal aggregation engine**
that pulls structured data from prediction markets, social media, news, and
financial markets — then uses an LLM to synthesize a trend report.

All endpoints share one auth header: `Authorization: Bearer $AISA_API_KEY`.
The REST surface lives under `https://api.aisa.one/apis/v1`; the OpenAI-compatible
LLM gateway lives under `https://api.aisa.one/v1` (note: no `/apis`).

## Example Prompts

- "What's the outlook on the AI chip market over the next 6 months?"
- "Will the Fed cut rates before September?"
- "Forecast the trend for Tesla stock based on current sentiment"
- "What are prediction markets saying about the 2026 midterms?"
- "Trend analysis for remote work adoption — combine social, news, and market data"

## Environment

```bash
export AISA_API_KEY="your-aisa-api-key"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER QUERY                           │
│          "What's the outlook on X?"                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              QUERY DECOMPOSITION (LLM)                  │
│  Break topic into search terms per data source          │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┬────────────┐
          ▼            ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │Prediction│ │ Twitter  │ │  News    │ │  Stock   │
    │ Markets  │ │Sentiment │ │ Velocity │ │  Data    │
    │ (odds)   │ │ (volume) │ │ (tavily) │ │(financial)│
    └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
         │            │            │             │
         └────────────┴─────┬──────┴─────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│              SIGNAL SYNTHESIS (LLM)                     │
│  Weigh signals, detect agreement/conflict,              │
│  produce confidence score (0-100) + forecast            │
└─────────────────────────────────────────────────────────┘
```

## Workflow

Follow these steps in order. Each step calls a specific AIsa API endpoint.

### Step 1: Decompose the Query

Use the AIsa LLM gateway to break the user's query into source-specific search terms.

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1-mini",
    "messages": [
      {
        "role": "system",
        "content": "You decompose a user query into search terms for 4 data sources. Respond ONLY with JSON: {\"prediction_market_query\": \"...\", \"twitter_query\": \"...\", \"news_query\": \"...\", \"stock_symbols\": [\"...\"], \"topic_summary\": \"...\"}. stock_symbols must be real tickers (AAPL, NVDA, TLT) — never institution abbreviations like FED/SEC/FDA."
      },
      {"role": "user", "content": "<USER_QUERY>"}
    ],
    "temperature": 0.2
  }'
```

### Step 2: Gather Prediction Market Signals

Prices come in **two steps**: first query `/markets` to find the market and its
ID, then pass that ID to `/market-price/` to get the current odds. Prices are
decimals 0–1 representing probability (`0.65` = 65%).

```bash
# 1. Find Polymarket markets (params: search, status, market_slug, limit)
curl "https://api.aisa.one/apis/v1/polymarket/markets?search=<PREDICTION_MARKET_QUERY>&status=open&limit=5" \
  -H "Authorization: Bearer $AISA_API_KEY"

# 2. Price a token (token_id = side_a.id or side_b.id from step 1)
curl "https://api.aisa.one/apis/v1/polymarket/market-price/<TOKEN_ID>" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

For Kalshi, the flow is the same but keyed on `market_ticker`:

```bash
curl "https://api.aisa.one/apis/v1/kalshi/markets?search=<PREDICTION_MARKET_QUERY>&limit=5" \
  -H "Authorization: Bearer $AISA_API_KEY"

curl "https://api.aisa.one/apis/v1/kalshi/market-price/<MARKET_TICKER>" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Extract: market titles, current YES/NO prices (decimal probability), volume, and recency.

### Step 3: Gather Twitter/X Social Sentiment

Search Twitter for recent discussion volume and sentiment signals. The tweet
search endpoint is `/twitter/tweet/advanced_search` with params `query` and
`queryType` (`Latest` or `Top`).

```bash
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=<TWITTER_QUERY>&queryType=Latest" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Extract: tweet count, engagement metrics (likes, retweets, replies), notable accounts
posting about the topic, and overall sentiment tone.

### Step 4: Gather News Signals

Use AIsa's Tavily relay to search recent news articles about the topic.

```bash
curl -X POST "https://api.aisa.one/apis/v1/tavily/search" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "<NEWS_QUERY>",
    "search_depth": "advanced",
    "max_results": 10,
    "topic": "news",
    "days": 7
  }'
```

Extract: article count, source diversity, headline sentiment, publication velocity
(are articles accelerating or decelerating?).

### Step 5: Gather Stock/Market Signals (if applicable)

If the topic relates to a publicly traded company, sector, or financial instrument,
query AIsa's MarketPulse `/financial/` endpoints. Pull three signals per ticker:

```bash
# Historical prices (interval is required: day, week, month, etc.)
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=<STOCK_SYMBOL>&interval=day" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Real-time financial metrics snapshot
curl "https://api.aisa.one/apis/v1/financial/financial-metrics/snapshot?ticker=<STOCK_SYMBOL>" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Company news
curl "https://api.aisa.one/apis/v1/financial/news?ticker=<STOCK_SYMBOL>" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Extract: recent price trend (1d, 5d, 30d), valuation/profitability metrics, and
headline sentiment. For deeper signals, add `/financial/analyst-estimates`,
`/financial/insider-trades`, or the macro `/financial/macro/interest-rates/snapshot`.

Use only real ticker symbols (AAPL, NVDA, TLT) — never institution abbreviations
like FED/SEC/FDA. If no stock symbols are relevant, skip this step and note
"N/A — non-financial topic".

### Step 6: Synthesize Forecast

Pass all gathered signals to the AIsa LLM gateway for synthesis.

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4.1-mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a trend analyst. Given structured signals from prediction markets, Twitter, news, and stock data, produce a forecast. Output JSON: {\"trend_direction\": \"bullish|bearish|neutral|mixed\", \"confidence_score\": 0-100, \"time_horizon\": \"...\", \"headline\": \"...\", \"analysis\": \"...\", \"signal_agreement\": \"high|medium|low\", \"key_signals\": [...], \"risks\": [...], \"data_gaps\": [...]}"
      },
      {
        "role": "user",
        "content": "TOPIC: <TOPIC_SUMMARY>\n\nPREDICTION MARKETS:\n<PM_DATA>\n\nTWITTER SENTIMENT:\n<TWITTER_DATA>\n\nNEWS VELOCITY:\n<NEWS_DATA>\n\nMARKET DATA:\n<STOCK_DATA>"
      }
    ],
    "temperature": 0.3
  }'
```

### Step 7: Format and Deliver

Present the forecast to the user in this format:

```
📈 TREND FORECAST: <headline>

Direction: <trend_direction>
Confidence: <confidence_score>/100
Signal Agreement: <signal_agreement>
Time Horizon: <time_horizon>

ANALYSIS:
<analysis paragraph>

KEY SIGNALS:
- <signal 1>
- <signal 2>
- <signal 3>

RISKS & CAVEATS:
- <risk 1>
- <risk 2>

DATA GAPS:
- <any sources that returned no data>
```

## Rules

- ALWAYS call at least 3 of the 4 data sources before synthesizing. A forecast
  from fewer than 3 sources must include a prominent "LOW CONFIDENCE — limited
  data sources" warning.
- NEVER present prediction market odds as certainties. Always frame them as
  "prediction markets currently price X at Y%" not "X will happen".
- NEVER provide financial advice. Frame all output as informational analysis,
  not investment recommendations. Include a disclaimer when stock data is involved.
- For stock signals, use only real ticker symbols. Never pass institution
  abbreviations (FED, SEC, FDA) to the `/financial/` endpoints — they will fail.
- If the AISA_API_KEY is not set, prompt the user to set it and provide a link
  to https://aisa.one to create an account.
- If any API call fails, log the error, continue with remaining sources, and
  note the gap in the final output.

## Automation

For recurring forecasts, use the Python script:

```bash
python3 scripts/trend_forecast.py "Will the Fed cut rates in 2026?" --output json
python3 scripts/trend_forecast.py "Tesla outlook" --output markdown --save report.md
python3 scripts/trend_forecast.py "Bitcoin outlook" --model gpt-4.1
```

See `scripts/trend_forecast.py` for the full implementation and `references/api_endpoints.md`
for complete AIsa endpoint documentation.
