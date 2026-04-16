---
name: stock-analysis
description: Analyze stocks and cryptocurrencies with 8-dimension scoring via AIsa API. Provides BUY/HOLD/SELL signals with confidence levels, entry/target/stop prices, and risk flags. Supports single or multi-ticker analysis with optional fast mode and JSON output. Use when the user asks to analyze a stock, check a ticker, or compare investments.
---

# Stock & Crypto Analysis — AIsa Edition

Analyze one or more stock or crypto tickers using the AIsa API with live Yahoo Finance data.

## Setup

This skill requires an AIsa API key. Set it via plugin configuration or environment variable:

```bash
export AISA_API_KEY=your_key_here
export AISA_BASE_URL=https://api.aisa.one/v1   # optional
export AISA_MODEL=gpt-4o                         # optional
```

Or use the plugin's `userConfig` values (set automatically when the plugin is enabled).

## Usage

Run the analysis script with one or more ticker symbols:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-analysis/scripts/analyze_stock.py" AAPL
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-analysis/scripts/analyze_stock.py" BTC-USD ETH-USD
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-analysis/scripts/analyze_stock.py" AAPL MSFT GOOGL
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-analysis/scripts/analyze_stock.py" AAPL --fast
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-analysis/scripts/analyze_stock.py" AAPL --output json
```

### Arguments

- **Tickers**: One or more stock symbols (e.g., `AAPL`, `MSFT`) or crypto symbols (e.g., `BTC-USD`, `ETH-USD`)
- `--fast`: Skip slow analyses (insider trading, detailed news) for faster results
- `--output json`: Append a structured JSON summary after the analysis

### Multi-Ticker Comparison

When multiple tickers are provided, the script produces individual analyses followed by a ranked comparison table:

| Ticker | Score | Signal | Key Strength | Key Risk |
|--------|-------|--------|-------------|----------|

## 8-Dimension Scoring (Stocks)

| # | Dimension | Weight |
|---|-----------|--------|
| 1 | Earnings Surprise | 30% |
| 2 | Fundamentals (P/E, margins, growth) | 20% |
| 3 | Analyst Sentiment | 20% |
| 4 | Historical Patterns | 10% |
| 5 | Market Context (VIX, SPY/QQQ) | 10% |
| 6 | Sector Performance | 15% |
| 7 | Momentum (RSI, 52w range) | 15% |
| 8 | Sentiment (Fear/Greed, shorts, insiders) | 10% |

## 3-Dimension Scoring (Crypto)

| # | Dimension | Weight |
|---|-----------|--------|
| 1 | Market Cap & Category | 40% |
| 2 | BTC Correlation (30-day) | 30% |
| 3 | Momentum (RSI, range, volume) | 30% |

## Risk Flags

Automatically detected: Pre-earnings, Post-spike, Overbought, Risk-Off, Breaking News

## Output

Final recommendation includes: **Score (0-10)**, **Signal (BUY/HOLD/SELL)**, **Confidence (High/Medium/Low)**, and **Entry / Target / Stop prices**.

**NOT FINANCIAL ADVICE.** For informational purposes only.
