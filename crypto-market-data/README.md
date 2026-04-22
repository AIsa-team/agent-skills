# Crypto Market Data 🪙

**Complete cryptocurrency market data for autonomous agents. Powered by AIsa.**

One API key. Prices, charts, tokens by contract address, exchanges, categories, and news — every CoinGecko surface under a single CLI.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.

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
python3 scripts/coingecko_client.py simple price \
  --ids bitcoin,ethereum --vs usd,eur --include-24hr-change

# All supported fiat/crypto currencies usable as vs_currency
python3 scripts/coingecko_client.py simple supported-currencies

# Price by on-chain contract address (USDC on Ethereum)
python3 scripts/coingecko_client.py simple token-price \
  --platform ethereum \
  --addresses 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  --vs usd --include-24hr-vol
```

### Coin data, markets, and history

```bash
# Full coin data for bitcoin
python3 scripts/coingecko_client.py coins data --id bitcoin

# Top 25 coins by market cap (USD)
python3 scripts/coingecko_client.py coins markets \
  --vs usd --order market_cap_desc --per-page 25

# Directory of all coins with ids/symbols/names
python3 scripts/coingecko_client.py coins list

# Historical snapshot for a specific date (dd-mm-yyyy)
python3 scripts/coingecko_client.py coins history \
  --id bitcoin --date 01-01-2024

# 30-day daily market chart for BTC in USD
python3 scripts/coingecko_client.py coins chart \
  --id bitcoin --vs usd --days 30

# Explicit UNIX timestamp range
python3 scripts/coingecko_client.py coins chart-range \
  --id bitcoin --vs usd --from 1704067200 --to 1706745600

# 7-day OHLC candles
python3 scripts/coingecko_client.py coins ohlc \
  --id bitcoin --vs usd --days 7

# Exchange-listed trading pairs for a coin
python3 scripts/coingecko_client.py coins tickers \
  --id bitcoin --order trust_score_desc

# Full data / chart by contract address
python3 scripts/coingecko_client.py coins contract \
  --platform ethereum \
  --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

python3 scripts/coingecko_client.py coins contract-chart \
  --platform ethereum \
  --address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 \
  --vs usd --days 14
```

### Categories

```bash
# All category IDs and names
python3 scripts/coingecko_client.py categories list

# Category leaderboard (market cap, volume, top-3 coins)
python3 scripts/coingecko_client.py categories markets \
  --order market_cap_desc
```

### Exchanges

```bash
# Exchanges with current trading volume and metadata
python3 scripts/coingecko_client.py exchanges list --per-page 50

# Just the ID -> name map (useful for resolving user input)
python3 scripts/coingecko_client.py exchanges id-map

# Detailed data for a specific exchange
python3 scripts/coingecko_client.py exchanges data --id binance

# Trading pairs on a specific exchange
python3 scripts/coingecko_client.py exchanges tickers \
  --id binance --order trust_score_desc
```

### News and trending

```bash
python3 scripts/coingecko_client.py news
python3 scripts/coingecko_client.py trending
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

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
