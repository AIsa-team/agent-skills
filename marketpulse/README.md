# MarketPulse (Equity Market Data) 📊

Query real-time and historical financial data for equities—prices, news, financial statements, metrics, analyst estimates, insider/institutional activity, SEC filings, earnings press releases, segmented revenues, stock screening, and macro interest rates.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

## Features

- **Stock Data**: Historical prices, real-time quotes
- **Company News**: Latest news by ticker
- **Financial Statements**: Income, balance sheets, cash flow
- **Segmented Revenues**: Revenue broken out by segment and geography
- **Analyst Estimates**: EPS forecasts
- **Earnings Press Releases**: Quarterly earnings releases
- **Insider Trading**: Track insider transactions
- **Institutional Ownership**: 13F-style holdings data
- **SEC Filings**: 10-K, 10-Q, 8-K and more — with filing item extraction
- **Stock Screener**: Filter by metrics
- **Line-Item Search**: Pull specific line items across multiple tickers
- **Macro Interest Rates**: Snapshot and historical central-bank rates

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Stock prices
python scripts/market_client.py stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31

# Earnings press releases
python scripts/market_client.py stock earnings --ticker AAPL
```

## Documentation

See [SKILL.md](SKILL.md) for complete API documentation.

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

