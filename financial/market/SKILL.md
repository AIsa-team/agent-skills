---
name: market
description: 'Query real-time and historical financial data across equities and crypto—prices, market moves, metrics, and trends for analysis, alerts, and reporting. Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.2"
  aisa:
    emoji: 📊
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
    version: "1.0.2"
---

# AIsa Market (`market`) 📊

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

**Complete market data for autonomous agents. Powered by AIsa.**

One API key. Stocks + Crypto + Financials. Everything you need.

## 🔥 What Can You Do?

### Cross-Asset Portfolio
```
"Get BTC, ETH prices alongside AAPL, NVDA stock data for my portfolio"
```

### Investment Research
```
"Full analysis: NVDA price trends, insider trades, analyst estimates, SEC filings"
```

### Crypto Tracking
```
"Real-time prices for BTC, ETH, SOL with 30-day historical charts"
```

### Earnings Analysis
```
"Get Tesla earnings reports, analyst estimates, and price reaction"
```

### Market Screening
```
"Find stocks with P/E < 15 and revenue growth > 20%"
```

### Whale Watching
```
"Track insider trades at Apple and correlate with price movements"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

---

## 🏦 Traditional Finance

### Stock Prices

```bash
# Historical price data (daily)
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&interval=day&interval_multiplier=1&start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Weekly price data
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&interval=week&interval_multiplier=1&start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Minute-level data (intraday)
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&interval=minute&interval_multiplier=5&start_date=2025-01-15&end_date=2025-01-15" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Parameters:**
- `ticker`: Stock symbol (required)
- `interval`: `second`, `minute`, `day`, `week`, `month`, `year` (required)
- `interval_multiplier`: Multiplier for interval, e.g., 5 for 5-minute bars (required)
- `start_date`: Start date YYYY-MM-DD (required)
- `end_date`: End date YYYY-MM-DD (required)

### Company News

```bash
# Get news by ticker
curl "https://api.aisa.one/apis/v1/financial/news?ticker=AAPL&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Financial Statements

```bash
# All financial statements
curl "https://api.aisa.one/apis/v1/financial/financials?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Income statements
curl "https://api.aisa.one/apis/v1/financial/financials/income-statements?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Balance sheets
curl "https://api.aisa.one/apis/v1/financial/financials/balance-sheets?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Cash flow statements
curl "https://api.aisa.one/apis/v1/financial/financials/cash-flow-statements?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Financial Metrics

```bash
# Real-time financial metrics snapshot
curl "https://api.aisa.one/apis/v1/financial/financial-metrics/snapshot?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Historical financial metrics
curl "https://api.aisa.one/apis/v1/financial/financial-metrics?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Analyst Estimates

```bash
# Earnings per share estimates
curl "https://api.aisa.one/apis/v1/financial/analyst-estimates?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Insider Trading

```bash
# Get insider trades
curl "https://api.aisa.one/apis/v1/financial/insider-trades?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Institutional Ownership

> **Not in the published contract.** No institutional-ownership operation is published in https://aisa.one/openapi.json; this request may return 404. Tracked in `scripts/validate_skills_known_issues.json`.

```bash
# Get institutional ownership
curl "https://api.aisa.one/apis/v1/financial/institutional/ownership?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### SEC Filings

```bash
# Get SEC filings
curl "https://api.aisa.one/apis/v1/financial/filings?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get SEC filing items (filing_type and year are required)
curl "https://api.aisa.one/apis/v1/financial/filings/items?ticker=AAPL&filing_type=10-K&year=2024" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Company Facts

```bash
# Get company facts by CIK
curl "https://api.aisa.one/apis/v1/financial/company/facts?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Stock Screener

```bash
# Screen for stocks matching criteria
# Filters are statement line items: [{"field", "operator": gt|lt|gte|lte|eq|in, "value"}]
curl -X POST "https://api.aisa.one/apis/v1/financial/financials/search/screener" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filters":[{"field":"revenue","operator":"gt","value":1000000000},{"field":"net_income","operator":"gt","value":0}],"limit":10}'
```

### Interest Rates

```bash
# Current interest rates
curl "https://api.aisa.one/apis/v1/financial/macro/interest-rates/snapshot" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Historical interest rates
curl "https://api.aisa.one/apis/v1/financial/macro/interest-rates?bank=fed" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## ₿ Cryptocurrency

> **Not in the published contract.** The Financial API publishes no crypto price operations (the `financial/crypto/...` routes below are absent from https://aisa.one/openapi.json), so the requests below may return 404 (tracked in `scripts/validate_skills_known_issues.json`). For crypto prices use the `crypto-market-data` skill (CoinGecko, `/apis/v1/coingecko/...`).

### Real-Time Price Snapshot

```bash
# Get current BTC price (use ticker format: SYMBOL-USD)
curl "https://api.aisa.one/apis/v1/financial/crypto/prices/snapshot?ticker=BTC-USD" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get current ETH price
curl "https://api.aisa.one/apis/v1/financial/crypto/prices/snapshot?ticker=ETH-USD" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get current SOL price
curl "https://api.aisa.one/apis/v1/financial/crypto/prices/snapshot?ticker=SOL-USD" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get TRUMP token price
curl "https://api.aisa.one/apis/v1/financial/crypto/prices/snapshot?ticker=TRUMP-USD" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Note:** Crypto tickers use format `SYMBOL-USD` (e.g., `BTC-USD`, `ETH-USD`).

### Historical Price Data

```bash
# Get BTC historical prices (daily)
curl "https://api.aisa.one/apis/v1/financial/crypto/prices?ticker=BTC-USD&interval=day&interval_multiplier=1&start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get ETH hourly data
curl "https://api.aisa.one/apis/v1/financial/crypto/prices?ticker=ETH-USD&interval=minute&interval_multiplier=60&start_date=2025-01-15&end_date=2025-01-16" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Supported Cryptocurrencies

| Ticker | Name |
|--------|------|
| BTC-USD | Bitcoin |
| ETH-USD | Ethereum |
| SOL-USD | Solana |
| BNB-USD | Binance Coin |
| XRP-USD | Ripple |
| DOGE-USD | Dogecoin |
| ADA-USD | Cardano |
| AVAX-USD | Avalanche |
| DOT-USD | Polkadot |
| MATIC-USD | Polygon |
| LINK-USD | Chainlink |
| UNI-USD | Uniswap |
| ATOM-USD | Cosmos |
| LTC-USD | Litecoin |
| TRUMP-USD | Trump Token |
| ... | And many more |

---

## Python Client

```bash
# ==================== Stock Data ====================
# Note: start_date and end_date are REQUIRED for prices
python3 scripts/market_client.py stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31
python3 scripts/market_client.py stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31 --interval week
python3 scripts/market_client.py stock news --ticker AAPL --count 10

# ==================== Financial Statements ====================
python3 scripts/market_client.py stock statements --ticker AAPL --type all            # --period annual|quarterly|ttm (default annual)
python3 scripts/market_client.py stock statements --ticker AAPL --type income
python3 scripts/market_client.py stock statements --ticker AAPL --type balance
python3 scripts/market_client.py stock statements --ticker AAPL --type cash

# ==================== Metrics & Analysis ====================
python3 scripts/market_client.py stock metrics --ticker AAPL
python3 scripts/market_client.py stock analyst --ticker AAPL

# ==================== Insider & Institutional ====================
python3 scripts/market_client.py stock insider --ticker AAPL
python3 scripts/market_client.py stock ownership --ticker AAPL

# ==================== SEC Filings ====================
python3 scripts/market_client.py stock filings --ticker AAPL

# ==================== Stock Screener ====================
python3 scripts/market_client.py stock screen --filter revenue:gt:1000000000 --filter net_income:gt:0 --limit 10

# ==================== Interest Rates ====================
python3 scripts/market_client.py stock rates
python3 scripts/market_client.py stock rates --historical

# ==================== Crypto Data ====================
# Note: Use ticker format SYMBOL-USD (or just SYMBOL, auto-converted)
python3 scripts/market_client.py crypto snapshot --ticker BTC-USD
python3 scripts/market_client.py crypto snapshot --ticker ETH  # Auto-converts to ETH-USD
python3 scripts/market_client.py crypto historical --ticker BTC-USD --start 2025-01-01 --end 2025-01-31
python3 scripts/market_client.py crypto portfolio --tickers BTC-USD,ETH-USD,SOL-USD
```

---

## API Endpoints Reference

### Traditional Finance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/financial/prices` | GET | Historical stock prices (requires interval params) |
| `/financial/news` | GET | Company news by ticker |
| `/financial/financials` | GET | All financial statements (requires `period`) |
| `/financial/financials/income-statements` | GET | Income statements |
| `/financial/financials/balance-sheets` | GET | Balance sheets |
| `/financial/financials/cash-flow-statements` | GET | Cash flow statements |
| `/financial/financial-metrics/snapshot` | GET | Real-time financial metrics |
| `/financial/financial-metrics` | GET | Historical metrics |
| `/financial/analyst-estimates` | GET | EPS estimates |
| `/financial/insider-trades` | GET | Insider trades |
| `/financial/institutional/ownership` | GET | Institutional ownership (not in the published contract) |
| `/financial/filings` | GET | SEC filings |
| `/financial/filings/items` | GET | SEC filing items (requires `filing_type`, `year`) |
| `/financial/company/facts` | GET | Company facts |
| `/financial/financials/search/screener` | POST | Stock screener (JSON body `filters[]`) |
| `/financial/macro/interest-rates/snapshot` | GET | Current interest rates |
| `/financial/macro/interest-rates` | GET | Historical rates (requires `bank`) |

### Cryptocurrency

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/financial/crypto/prices/snapshot` | GET | Real-time price snapshot (not in the published contract) |
| `/financial/crypto/prices` | GET | Historical OHLCV data (not in the published contract) |

---

## Pricing

| API | Cost |
|-----|------|
| Stock prices | ~$0.001 |
| Company news | ~$0.001 |
| Financial statements | ~$0.002 |
| Analyst estimates | ~$0.002 |
| SEC filings | ~$0.001 |
| Crypto snapshot | ~$0.0005 |
| Crypto historical | ~$0.001 |

The settled cost of each call is returned in the `X-AISA-Customer-Cost-Micros-USD` response header (integer micro-USD; 1 USD = 1,000,000). Do not look for a cost field in the response body.

---

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See the [API Reference](https://aisa.one/docs/api-reference) for complete endpoint documentation.
