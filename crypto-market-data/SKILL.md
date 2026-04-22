---
name: crypto-market-data
description: "Query real-time and historical cryptocurrency market data via CoinGecko — simple prices, coin details, historical charts, OHLC candles, token prices by contract address, market-cap rankings, exchange data and tickers, categories, trending searches, and crypto news. Use for crypto research, price tracking, on-chain token lookup, portfolio analysis, and market-cap screening."
license: MIT
compatibility: "Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY."
metadata: {"aisa": {"emoji": "🪙", "homepage": "https://aisa.one", "requires": {"bins": ["curl", "python3"], "env": ["AISA_API_KEY"]}, "primaryEnv": "AISA_API_KEY", "harnesses": ["claude-code", "claude", "opencode", "cursor", "codex", "gemini-cli", "openclaw", "hermes", "goose"]}}
---
# Crypto Market Data 🪙

**Complete cryptocurrency market data for autonomous agents. Powered by AIsa.**

One API key. Prices, charts, tokens by contract address, exchanges, categories, and news — every CoinGecko surface under a single CLI.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## 🔥 What Can You Do?

### Price Tracking
```text
"What is the current price of bitcoin and ethereum in USD and EUR?"
```

### Historical Charts
```text
"Get the last 30 days of BTC price data in USD"
```

### OHLC Candles
```text
"Pull 7-day OHLC candles for solana"
```

### Token Lookup by Contract Address
```text
"Find the CoinGecko price for USDC at 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 on Ethereum"
```

### Market-Cap Screening
```text
"List the top 25 coins by market cap with 24h change"
```

### Exchange Research
```text
"What are Binance's top trading pairs by trust score?"
```

### Trend Discovery
```text
"What are the top trending coin searches on CoinGecko right now?"
```

### Category Breakdown
```text
"Rank DeFi coin categories by market cap"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

### Simple prices

```bash
# Current price of bitcoin and ethereum in USD + EUR with 24h change
python3 {baseDir}/scripts/coingecko_client.py simple price \
  --ids bitcoin,ethereum --vs usd,eur --include-24hr-change

# All supported fiat/crypto currencies usable as vs_currency
python3 {baseDir}/scripts/coingecko_client.py simple supported-currencies

# Price by on-chain contract address (USDC on Ethereum)
python3 {baseDir}/scripts/coingecko_client.py simple token-price \
  --platform ethereum \
  --addresses 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  --vs usd --include-24hr-vol
```

### Coin data, markets, and history

```bash
# Full coin data for bitcoin
python3 {baseDir}/scripts/coingecko_client.py coins data --id bitcoin

# Top 25 coins by market cap (USD)
python3 {baseDir}/scripts/coingecko_client.py coins markets \
  --vs usd --order market_cap_desc --per-page 25

# Directory of all coins with ids/symbols/names
python3 {baseDir}/scripts/coingecko_client.py coins list

# Historical snapshot for a specific date (dd-mm-yyyy)
python3 {baseDir}/scripts/coingecko_client.py coins history \
  --id bitcoin --date 01-01-2024

# 30-day daily market chart for BTC in USD
python3 {baseDir}/scripts/coingecko_client.py coins chart \
  --id bitcoin --vs usd --days 30

# Explicit UNIX timestamp range
python3 {baseDir}/scripts/coingecko_client.py coins chart-range \
  --id bitcoin --vs usd --from 1704067200 --to 1706745600

# 7-day OHLC candles
python3 {baseDir}/scripts/coingecko_client.py coins ohlc \
  --id bitcoin --vs usd --days 7

# Exchange-listed trading pairs for a coin
python3 {baseDir}/scripts/coingecko_client.py coins tickers \
  --id bitcoin --order trust_score_desc

# Full data / chart by contract address
python3 {baseDir}/scripts/coingecko_client.py coins contract \
  --platform ethereum \
  --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

python3 {baseDir}/scripts/coingecko_client.py coins contract-chart \
  --platform ethereum \
  --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  --vs usd --days 14
```

### Categories

```bash
# All category IDs and names
python3 {baseDir}/scripts/coingecko_client.py categories list

# Category leaderboard (market cap, volume, top-3 coins)
python3 {baseDir}/scripts/coingecko_client.py categories markets \
  --order market_cap_desc
```

### Exchanges

```bash
# Exchanges with current trading volume and metadata
python3 {baseDir}/scripts/coingecko_client.py exchanges list --per-page 50

# Just the ID -> name map (useful for resolving user input)
python3 {baseDir}/scripts/coingecko_client.py exchanges id-map

# Detailed data for a specific exchange
python3 {baseDir}/scripts/coingecko_client.py exchanges data --id binance

# Trading pairs on a specific exchange
python3 {baseDir}/scripts/coingecko_client.py exchanges tickers \
  --id binance --order trust_score_desc
```

### News and trending

```bash
python3 {baseDir}/scripts/coingecko_client.py news
python3 {baseDir}/scripts/coingecko_client.py trending
```

## Inputs and Outputs

- **Input:** coin IDs (e.g. `bitcoin`, `ethereum`, `solana`), fiat/crypto `vs_currency` codes (`usd`, `eur`, `btc`), category/exchange IDs, or on-chain platform+contract-address pairs. Use `coins list` and `exchanges id-map` to resolve user-friendly names to CoinGecko IDs.
- **Output:** JSON responses printed to stdout, matching the CoinGecko schema for each endpoint (price dictionaries, coin/exchange objects, arrays of timestamped `[ts, value]` pairs for charts, `[ts, o, h, l, c]` tuples for OHLC, ticker arrays, etc.).

## When to use / When NOT to use

**Use when:**
- You need current or historical **crypto** prices, market caps, volumes, or charts.
- You need to look up a token by its **on-chain contract address** (ethereum, binance-smart-chain, polygon-pos, etc.).
- You need **exchange-level** data — trust scores, volumes, per-pair tickers.
- You're screening across categories (DeFi, AI, L1s, etc.) or surfacing trending coins.

**Do NOT use when:**
- You need **equities or traditional finance** data — use the `marketpulse` skill.
- You need **order-book depth on prediction markets** (Polymarket, Kalshi) — use `prediction-market-data`.
- You need **on-chain wallet balances, transfers, or gas traces** — CoinGecko is a pricing/market-data source, not a node RPC.

## Requirements

- Python 3, `curl`, POSIX shell
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## API Reference

This skill calls the following AIsa CoinGecko endpoints directly:

- [Simple Price](https://aisa.one/docs/api-reference/coingecko/simple-price) — current price for one or more coins in any supported currencies
- [Supported Currencies](https://aisa.one/docs/api-reference/coingecko/supported-currencies) — list of all supported fiat and crypto `vs_currency` codes
- [Coin Price by Token Address](https://aisa.one/docs/api-reference/coingecko/coin-price-by-token-address) — current price of tokens by contract address on a supported platform
- [Coins List (ID Map)](https://aisa.one/docs/api-reference/coingecko/coins-list) — directory of all coins with id, symbol, and name
- [Coins Markets](https://aisa.one/docs/api-reference/coingecko/coins-markets) — all coins with full market data (price, market cap, volume, etc.)
- [Coin Data by ID](https://aisa.one/docs/api-reference/coingecko/coin-data-by-id) — current coin info including price, markets, links, community and developer data
- [Coin Tickers](https://aisa.one/docs/api-reference/coingecko/coin-tickers) — exchange-listed trading pairs for a coin
- [Coin Historical Data](https://aisa.one/docs/api-reference/coingecko/coin-historical-data) — historical snapshot (price, market cap, volume) for a given date
- [Coin Historical Chart](https://aisa.one/docs/api-reference/coingecko/coin-historical-chart) — historical market data over the last N days
- [Coin Market Chart Range](https://aisa.one/docs/api-reference/coingecko/coin-market-chart-range) — historical market data within an explicit UNIX timestamp range
- [Coin OHLC](https://aisa.one/docs/api-reference/coingecko/coin-ohlc) — OHLC candles for a coin
- [Coin Data by Token Address](https://aisa.one/docs/api-reference/coingecko/coin-data-by-token-address) — full coin data by contract address on a supported platform
- [Coin Historical Chart by Contract](https://aisa.one/docs/api-reference/coingecko/coin-historical-chart-by-contract) — historical market data for a token by contract address
- [Categories List](https://aisa.one/docs/api-reference/coingecko/categories-list) — all coin categories used by CoinGecko
- [Categories with Market Data](https://aisa.one/docs/api-reference/coingecko/categories-with-market-data) — categories with market cap, volume, and top-3 coins
- [Exchanges List](https://aisa.one/docs/api-reference/coingecko/exchanges-list) — all exchanges with current trading volume and metadata
- [Exchanges List (ID Map)](https://aisa.one/docs/api-reference/coingecko/exchanges-list-id-map) — exchange identifiers and names for mapping
- [Exchange Data by ID](https://aisa.one/docs/api-reference/coingecko/exchange-data-by-id) — detailed data for a single exchange (volume, tickers, trust score)
- [Exchange Tickers](https://aisa.one/docs/api-reference/coingecko/exchange-tickers) — trading pairs listed on a given exchange
- [Crypto News](https://aisa.one/docs/api-reference/coingecko/crypto-news) — latest crypto news articles aggregated by CoinGecko
- [Trending Search](https://aisa.one/docs/api-reference/coingecko/trending-search) — top-7 trending coin searches in the last 24 hours

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
