---
name: prediction-market-data
description: Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 📈
    homepage: https://aisa.one
    requires:
      bins:
      - curl
      - python
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
# Cross-Platform Prediction Market Data 📈

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify

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

**Prediction markets data access for autonomous agents. Powered by AIsa.**

One API key. Full Polymarket and Kalshi intelligence.

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

## What Can You Do?

### Probability Checks
```text
"What are the odds of [event] happening?"
```

### Market Sentiment
```text
"Research the current market sentiment on the upcoming election."
```

### Trading Analysis
```text
"Analyze historical prices and orderbooks for this market."
```

### Portfolio Tracking
```text
"Track portfolio positions and P&L for wallet address X."
```

### Arbitrage Detection
```text
"Find arbitrage opportunities across Polymarket and Kalshi."
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## How to Look Up IDs

Most endpoints require an ID that comes from the `/markets` response. Always query markets first, then pass the relevant ID to downstream endpoints.

1. **Polymarket `token_id`**: Query `/polymarket/markets`, find `side_a.id` or `side_b.id` in the response, then pass it to `/polymarket/market-price/{token_id}`.
2. **Polymarket `condition_id`**: Query `/polymarket/markets`, find `condition_id` in the response, then pass it to `/polymarket/candlesticks/{condition_id}`.
3. **Kalshi `market_ticker`**: Query `/kalshi/markets`, find `market_ticker` in the response, then pass it to `/kalshi/market-price/{market_ticker}`.

## End-to-End Examples

### Get the current price of a Polymarket market

Prices require a `token_id`, which comes from the `/markets` response. Always query markets first.

**Step 1: Find a market and extract the token_id:**

```bash
# Search for open election markets and grab a token_id
python scripts/prediction_market_client.py polymarket markets --search "election" --status open --limit 5
```

The response includes a `side_a.id` and `side_b.id` for each market; these are the token IDs for the Yes and No sides respectively:

```json
{
  "markets": [
    {
      "title": "Will Trump nationalize elections?",
      "market_slug": "will-trump-nationalize-elections",
      "condition_id": "0xe6522d64f35a6843ebdbccab2e3d4a1385350be6d40a3de766330e207b71a8ba",
      "side_a": {
        "id": "44482086252598348208660011972852804909957485351743405768768577675743702971026",
        "label": "Yes"
      },
      "side_b": {
        "id": "68987475491741167427045844503509447338405188188495224371188027929166363674438",
        "label": "No"
      }
    }
  ]
}
```

**Step 2: Fetch the current price using the token_id:**

```bash
# Use side_a.id (Yes) or side_b.id (No) from Step 1
python scripts/prediction_market_client.py polymarket price 44482086252598348208660011972852804909957485351743405768768577675743702971026
```

The price is a decimal between 0 and 1 representing the probability (e.g. `0.20` = 20% chance of Yes).

---

### Get the current price of a Kalshi market

**Step 1: Find a market and extract the market_ticker:**

```bash
python scripts/prediction_market_client.py kalshi markets --search "fed rate" --status open --limit 5
```

```json
{
  "markets": [
    {
      "title": "Will the federal funds rate be above 3.75% after the Mar 2026 meeting?",
      "market_ticker": "KXFED-26MAR-T3.75",
      "last_price": 6
    }
  ]
}
```

**Step 2: Fetch the price using the market_ticker:**

```bash
python scripts/prediction_market_client.py kalshi price KXFED-26MAR-T3.75
```

---

## Core Capabilities

### Polymarket

#### Markets

```bash
# Find markets on Polymarket
curl -X GET "https://api.aisa.one/apis/v1/polymarket/markets?search=election&status=open" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Step 1: query /polymarket/markets to get a token_id from side_a.id or side_b.id
# Step 2: pass that token_id here to get the current price
curl -X GET "https://api.aisa.one/apis/v1/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Activity

```bash
# Fetch activity data for a specific user
curl -X GET "https://api.aisa.one/apis/v1/polymarket/activity?user={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orders?market_slug={market_slug}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific asset
# token_id comes from side_a.id or side_b.id in /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Candlesticks

```bash
# Fetch historical candlestick data for a market
# condition_id comes from /polymarket/markets response
curl -X GET "https://api.aisa.one/apis/v1/polymarket/candlesticks/{condition_id}?interval=60" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Positions

```bash
# Fetch all Polymarket positions for a proxy wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/positions/wallet/{wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet

```bash
# Fetch wallet information
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet?eoa={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet Profit-and-Loss

```bash
# Fetch realized profit and loss (PnL) for a specific wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet/pnl/{wallet_address}?granularity=day" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Kalshi

#### Markets

```bash
# Find markets on Kalshi
curl -X GET "https://api.aisa.one/apis/v1/kalshi/markets?search=fed%20rate" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Fetch the current market price for a Kalshi market
# market_ticker comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data for Kalshi markets
# ticker (market_ticker) comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/trades?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific Kalshi market
# ticker (market_ticker) comes from /kalshi/markets response
curl -X GET "https://api.aisa.one/apis/v1/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Cross-Platform

#### Sports Markets

```bash
# Find equivalent markets across platforms for sports events
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Sports Markets by Date

```bash
# Find equivalent markets across platforms for a sport on a given date
# sport options: nfl, mlb, cfb, nba, nhl, cbb, pga, tennis
# date format: YYYY-MM-DD
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports/nba?date=2025-08-16" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Sport abbreviations:

| Abbreviation | Sport |
|---|---|
| `nfl` | Football |
| `mlb` | Baseball |
| `cfb` | College Football |
| `nba` | Basketball |
| `nhl` | Hockey |
| `cbb` | College Basketball |
| `pga` | Golf |
| `tennis` | Tennis |

## API Endpoints Reference

### Polymarket Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/polymarket/markets` | Find markets | `search`, `status`, `market_slug`, `limit` |
| `/polymarket/market-price/{token_id}` | Get market price | `token_id`, `at_time` |
| `/polymarket/activity` | Get user activity | `user`, `start_time`, `end_time` |
| `/polymarket/orders` | Get trade history | `market_slug`, `token_id`, `user` |
| `/polymarket/orderbooks` | Get orderbook history | `token_id`, `start_time`, `end_time` |
| `/polymarket/candlesticks/{condition_id}` | Get candlestick data | `condition_id`, `start_time`, `end_time`, `interval` |
| `/polymarket/positions/wallet/{wallet_address}` | Get wallet positions | `wallet_address`, `limit` |
| `/polymarket/wallet` | Get wallet info | `eoa` or `proxy`, `with_metrics` |
| `/polymarket/wallet/pnl/{wallet_address}` | Get wallet PnL | `wallet_address`, `granularity` |

### Kalshi Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/kalshi/markets` | Find markets | `search`, `status`, `market_ticker` |
| `/kalshi/market-price/{market_ticker}` | Get market price | `market_ticker`, `at_time` |
| `/kalshi/trades` | Get trade history | `ticker`, `start_time`, `end_time` |
| `/kalshi/orderbooks` | Get orderbook history | `ticker`, `start_time`, `end_time` |

### Cross-Platform Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/matching-markets/sports` | Find matching sports markets | `polymarket_market_slug` or `kalshi_event_ticker` |
| `/matching-markets/sports/{sport}` | Find sports markets by date | `sport` (nfl\|mlb\|cfb\|nba\|nhl\|cbb\|pga\|tennis), `date` (YYYY-MM-DD) |

## Response Schemas

### Markets Response
Returns markets array:
- `title` (string) - Market question (e.g., "Will Trump nationalize elections?")
- `market_slug` (string) - URL-friendly identifier
- `condition_id` (string) - Blockchain condition ID
- `start_time` / `end_time` (integer) - Unix timestamps
- `completed_time` (integer|null) - Null if still open
- `tags` (array) - Category tags (e.g., ["politics", "us election"])
- `volume_1_week` / `volume_1_month` / `volume_1_year` / `volume_total` (number) - Trading volume in USD
- `side_a` / `side_b` (object) - id and label (typically "Yes"/"No")
- `winning_side` (object|null) - Null if unresolved
- `image` (string) - Market thumbnail URL

### Activity Response
Returns activities array:
- `title` (string) - Market title
- `market_slug` (string) - Market identifier
- `side` (string) - Trade side: BUY, SELL, or MERGE
- `shares` (integer) - Raw share amount
- `shares_normalized` (number) - Human-readable share amount
- `price` (number) - Trade price (0-1, represents probability)
- `timestamp` (integer) - Unix timestamp of the trade
- `user` (string) - Wallet address of the trader
- `tx_hash` (string) - Blockchain transaction hash

## Understanding Odds
- Prices are shown as decimals (0.65 = 65% probability)
- "Yes" price = probability market thinks event will happen
- Higher volume = more confidence/liquidity
- Prices change based on trading activity

## Pricing

| API | Cost |
|-----|------|
| Prediction market read query | $0.01 |

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://aisa.one/docs/api-reference/) for complete endpoint documentation.
