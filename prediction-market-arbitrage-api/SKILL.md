---
name: prediction-market-arbitrage-api
description: 'Find arbitrage opportunities across Polymarket and Kalshi prediction markets via AIsa API. Scan sports markets for cross-platform price discrepancies, compare real-time odds, verify orderbook liquidity. Use when user asks about: prediction market arbitrage, cross-platform price differences, sports betting arbitrage, odds comparison, risk-free profit, market inefficiencies.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: ⚖️
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# Prediction Market Arbitrage Api

Find arbitrage opportunities across [Polymarket](https://polymarket.com) and [Kalshi](https://kalshi.com) via [AIsa API](https://aisa.one).

## Setup

```bash
export AISA_API_KEY="your-key"
```

Get a key at [aisa.one](https://aisa.one) ($0.01/query, pay-as-you-go).

## Workflow

Finding arbitrage involves these steps:

1. **Scan matching markets** across platforms (`scan` for bulk, `match` for specific)
2. **Review spreads** — the tool calculates price differences automatically
3. **Verify liquidity** — use `prediction_market_client.py orderbooks` to check depth before acting

## Quick Examples

### Scan a sport for arbitrage

```bash
# Scan all NBA markets on a date — shows spreads automatically
python3 scripts/arbitrage_finder.py scan nba --date 2025-04-01
```

### Analyze a specific market

```bash
# By Polymarket slug
python3 scripts/arbitrage_finder.py match --polymarket-slug <slug>

# By Kalshi ticker
python3 scripts/arbitrage_finder.py match --kalshi-ticker <ticker>
```

### Verify liquidity before acting

```bash
# Check orderbook depth on both sides
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id>
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

## Commands

### arbitrage_finder.py — Automated Detection

```bash
python3 scripts/arbitrage_finder.py scan <sport> --date <YYYY-MM-DD> [--min-spread <pct>] [--min-liquidity <usd>] [--json]
python3 scripts/arbitrage_finder.py match --polymarket-slug <slug> [--min-spread <pct>] [--min-liquidity <usd>] [--json]
python3 scripts/arbitrage_finder.py match --kalshi-ticker <ticker> [--min-spread <pct>] [--min-liquidity <usd>] [--json]
```

Sports: `nba`, `nfl`, `mlb`, `nhl`, `soccer`, `tennis`.

### prediction_market_client.py — Raw Market Data

Use for manual price checks and deeper analysis.

```bash
# Search markets
python3 scripts/prediction_market_client.py polymarket markets --search <kw> --status open --limit 5
python3 scripts/prediction_market_client.py kalshi markets --search <kw> --status open --limit 5

# Get prices (use token_id / market_ticker from markets output)
python3 scripts/prediction_market_client.py polymarket price <token_id>
python3 scripts/prediction_market_client.py kalshi price <market_ticker>

# Cross-platform sports matching
python3 scripts/prediction_market_client.py sports by-date <sport> --date <YYYY-MM-DD>
python3 scripts/prediction_market_client.py sports matching (--polymarket-slug <slug> | --kalshi-ticker <ticker>)

# Orderbook depth
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id>
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

## Understanding Arbitrage

Arbitrage exists when the combined cost of all mutually exclusive outcomes across platforms is less than `1.0`:

> "Yes" at `0.40` on Polymarket + "No" at `0.55` on Kalshi = cost `0.95`, guaranteed payout `1.00` → 5.3% profit.

Always verify orderbook depth — a spread without liquidity is not executable.

## Security & Permissions

**Requires:** `AISA_API_KEY` environment variable.

All operations are **read-only** via HTTPS GET to `api.aisa.one`. Arbitrage spreads are calculated locally. No trades executed, no wallets connected, no personal data sent beyond the API key. Every response includes `usage.cost` and `usage.credits_remaining`.

Full docs: [AIsa API Reference](https://docs.aisa.one/reference/).
