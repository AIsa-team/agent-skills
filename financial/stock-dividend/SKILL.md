---
name: stock-dividend
description: 'Analyze read-only dividend metrics for stocks via AIsa API. Provides yield, payout ratio, growth CAGR, safety score, income rating, and Dividend Aristocrat/King status without placing trades, making purchases, or managing brokerage accounts. Use when: the user needs market data, stock analysis, dividend research, or read-only financial data workflows.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.2"
  aisa:
    emoji: 📊
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
    version: 1.0.2
  openclaw:
    clawhub-slug: stock-dividend-aisa
---

# Dividend Analysis — AIsa Edition

Analyze dividend metrics for one or more tickers using the AIsa API. This is a read-only research helper: it does not connect to brokerage accounts, place orders, make purchases, or manage portfolios.

## Usage

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ PG KO
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ PG KO --output json
```

### Arguments

- **Tickers**: One or more dividend-paying stock symbols. Inputs are validated before they are sent to the model.
- `--output json`: Append structured JSON summary

## Permission Boundary

- The only required secret is `AISA_API_KEY`.
- Requests go to `https://api.aisa.one/v1` by default.
- `AISA_BASE_URL` is optional and should only point to a trusted AIsa-compatible HTTPS endpoint.
- Do not provide brokerage credentials, trading passwords, cookies, or payment details. This skill has no purchase or order-placement workflow.

## Analysis Output

For each ticker, the analysis includes:

- **Core Metrics**: Yield, ex-date, frequency, last payment amount
- **Payout Analysis**: Payout ratio, FCF payout, coverage ratio
- **Growth**: 1Y, 3Y CAGR, 5Y CAGR, consecutive years of increases
- **Last 5 Annual Dividends** table
- **Safety Score (0-100)**: Based on payout ratio (25pts), FCF coverage (20pts), growth consistency (20pts), balance sheet (15pts), earnings stability (10pts), consecutive years (10pts)
- **Income Rating**: Excellent (80+), Good (60-79), Moderate (40-59), Poor (<40)
- **Dividend Aristocrat/King** status check

When multiple tickers are provided, a ranked comparison table is included.

**NOT FINANCIAL ADVICE.** For informational purposes only.
