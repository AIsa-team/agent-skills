---
name: crypto-market-data
description: Query real-time and historical cryptocurrency market data via CoinGecko — simple prices, coin details, historical charts, OHLC candles, token prices by contract address, market-cap rankings, exchange data and tickers, categories, trending searches, and crypto news. Use for crypto research, price tracking, on-chain token lookup, portfolio analysis, and market-cap screening.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🪙
    homepage: https://aisa.one
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---
# Crypto Market Data 🪙

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. Adding the server does not always start sign-in. If no sign-in window opens, start it from the client's own MCP authentication entry (a menu, command, or connector button); if only the user can reach that entry, tell them where it is. Sign-in is the slow step, not the API. Before it starts, tell the user in one line that an AIsa sign-in window or card is about to open and to click **Allow** (one click if the browser is already signed in to AIsa). Do not call step 2 until the user says sign-in is done or the AIsa tools appear; calling it earlier only returns 401, so do not retry in a loop. If the client must restart to load the server, tell the user and wait. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify (step 2)

Make one free authenticated call on the interface you connected:

- MCP (A, B): call `account` (no arguments). If it is not in the tool list, call `use` with `{"operation_id": "account"}` instead. Returns the key, balance, and usage.
- CLI (C): `aisa balance`. (`aisa whoami` is local only and does not count.)
- HTTP (D): `GET https://api.aisa.one/v1/models` with the Bearer header returns 200.

AIsa is connected only when this call succeeds. A tool list or a 401 response does not count.

### Spending (approval before paid calls)

- Free: docs, `GET /v1/models`, MCP `search`, `list_categories`, `batch_get_schema`, `batch_quote`, `account`, and CLI `aisa search`, `aisa schema`, `aisa quote`, `aisa balance`.
- Quote the exact calls before running them: MCP `batch_quote`, CLI `aisa quote --json`. Run only what you quoted; re-quote if the tools or arguments change. Neither `batch_use` nor `aisa call` takes a price cap.
- If the quote reports `auto_execute_eligible: true` (a small total), run it without asking, unless the user set a tighter limit or asked only for a quote.
- Otherwise, before the first such call, tell the user in one message what you plan to call, the quoted price, and a total budget for the task in USD. Wait for approval, then run calls within that budget without asking again. Ask again only if the task changes or the next call would exceed the remaining budget.
- For operations billed by rows or credits, also set the operation's own limit (for example `limit`) so the cost stays bounded.
- Do not retry a failed paid call without telling the user.
- Direct HTTP (D) follows the stricter rule at https://aisa.one/docs/get-started/cli.md#direct-http-fallback: read the endpoint's reference and published pricing first; state the exact endpoint and scope, formula or rate, and documented maximum USD exposure; then wait for a separate user message explicitly approving that scope and cap. Do not make paid calls to test availability. Docs, `/v1/models`, and capability or MCP discovery are allowed before approval.

### Cost accounting

The settled cost of a direct HTTP call is reported by the response header `X-AISA-Customer-Cost-Micros-USD` (integer micro-USD; 1 USD = 1,000,000 micro-USD), or by a successful native Tool result's `customer_cost_micros_usd`. Missing cost metadata means unknown, not free. Response bodies do not carry `usage.cost` or `usage.credits_remaining`; do not report those fields as the charge. Reference: https://aisa.one/docs/guides/pricing

### Errors

- `401`: not signed in or invalid key. Redo Connect option A (step 1A in llms.txt) or check the key.
- `402`: low balance, or the operation requires the Go-to-Market plan. The response says which and where to resolve it. Tell the user which one it is (top up the balance, or subscribe to the plan) with the link from the response; do not retry.
- `429`: rate limited. Wait and retry with backoff. Details: https://aisa.one/docs/api-reference/rate-limits
<!-- aisa-rules:end -->

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
