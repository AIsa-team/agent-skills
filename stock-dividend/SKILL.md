---
name: stock-dividend
description: Analyze dividend metrics for stocks via AIsa API. Provides yield, payout ratio, growth CAGR, safety score (0-100), income rating, and Dividend Aristocrat/King status. Use when the user asks about dividends, income investing, or dividend safety.
---

# Dividend Analysis — AIsa Edition

Analyze dividend metrics for one or more tickers using the AIsa API.

## Usage

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ PG KO
python3 "${CLAUDE_PLUGIN_ROOT}/skills/stock-dividend/scripts/dividends.py" JNJ PG KO --output json
```

### Arguments

- **Tickers**: One or more dividend-paying stock symbols
- `--output json`: Append structured JSON summary

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
