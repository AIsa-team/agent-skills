# AIsa Prediction Market Toolkit 📈⚖️

**A comprehensive toolkit for accessing prediction market data and finding cross-platform arbitrage opportunities for autonomous agents. Powered by AIsa.**

This repository contains skills and Python clients that allow AI agents and developers to interact with prediction markets like **Polymarket** and **Kalshi** using a single, unified API.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

## 📁 Included Files

### Skill
- `skill.md`: The skill definition for cross-platform prediction-market arbitrage lookups.

### Scripts
- `script/prediction_market_client.py`: CLI and Python wrapper for Polymarket, Kalshi, and cross-platform market-matching endpoints.
- `script/arbitrage_finder.py`: CLI that scans matching markets, compares prices, calculates spreads, and checks liquidity.

## Setup

Both the skill and the Python scripts require an AIsa API key.

```bash
export AISA_API_KEY="your-key-here"
```

## Using the Python Scripts

Run the scripts from the repository root with the `script/` path prefix.

### Prediction Market Client

```bash
# Search for open election markets
python script/prediction_market_client.py polymarket markets --search "election" --status open

# Get current price for a specific token
python script/prediction_market_client.py polymarket price <token_id>

# Get wallet portfolio and PnL
python script/prediction_market_client.py polymarket positions <wallet_address>
python script/prediction_market_client.py polymarket pnl <wallet_address> --granularity day

# Search for Fed rate markets
python script/prediction_market_client.py kalshi markets --search "fed rate" --status open

# Get orderbook for a market
python script/prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

### Arbitrage Finder

```bash
# Scan all NBA games on March 30, 2025, showing only spreads > 2% and liquidity > $500
python script/arbitrage_finder.py scan nba --date 2025-03-30 --min-spread 2.0 --min-liquidity 500

# Check a specific event using its Polymarket slug
python script/arbitrage_finder.py match --polymarket-slug nba-lakers-vs-celtics

# Or using its Kalshi ticker
python script/arbitrage_finder.py match --kalshi-ticker KXNBA-25-LAL-BOS
```

## Using the Skill

Load `skill.md` into the agent context.

Important details:
- The repository contains `skill.md`, not `SKILL.md`.
- The cURL examples in `skill.md` use product placeholders such as `{token_id}` and `{market_ticker}` by design.
- Before executing any `curl` command, the runner must verify that every `{...}` placeholder has been replaced with a concrete value.
- If a final command still contains `{token_id}` or any other brace placeholder, do not execute it. Fail fast and report a missing-parameter error.

## ID Lookup Workflow

Most endpoints require IDs fetched from a markets endpoint first:

1. `token_id`: from `side_a.id` or `side_b.id` in `/polymarket/markets`
2. `condition_id`: from `condition_id` in `/polymarket/markets`
3. `market_ticker`: from `market_ticker` in `/kalshi/markets`

## Pricing

| API Operation | Cost |
|---------------|------|
| Prediction market read query | $0.01 |

## Documentation

For complete endpoint documentation, see the AIsa API Reference: https://aisa.one/docs/api-reference/
