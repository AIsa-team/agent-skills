---
name: marketpulse
description: Query real-time and historical financial data for equities—prices, news, financial statements, metrics, analyst estimates, insider and institutional activity, SEC filings, earnings press releases, segmented revenues, stock screening, and macro interest rates.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 📊
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
# MarketPulse 📊

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

**Complete equity market data for autonomous agents. Powered by AIsa.**

One API key. Stocks, financials, filings, and macro data. Everything you need.

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

### Investment Research
```
"Full analysis: NVDA price trends, insider trades, analyst estimates, SEC filings"
```

### Earnings Analysis
```
"Get Tesla earnings press releases, analyst estimates, and price reaction"
```

### Market Screening
```
"Find stocks with P/E < 15 and revenue growth > 20%"
```

### Whale Watching
```
"Track insider trades at Apple and correlate with price movements"
```

### Segment Deep-Dive
```
"Break down Apple's revenue by product segment and geography"
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
# All financial statements (requires period)
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

**Parameters:**
- `ticker`: Stock symbol (required)
- `period`: `annual`, `quarterly`, or `ttm` (required)

### Segmented Revenues

```bash
# Break down revenue by business segment and geography
curl "https://api.aisa.one/apis/v1/financial/financials/segmented-revenues?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Parameters:**
- `ticker`: Stock symbol (required)
- `period`: `annual` or `quarterly` (required)

### Financial Metrics

```bash
# Real-time financial metrics snapshot
curl "https://api.aisa.one/apis/v1/financial/financial-metrics/snapshot?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Historical financial metrics (period required)
curl "https://api.aisa.one/apis/v1/financial/financial-metrics?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Analyst Estimates

```bash
# Earnings per share estimates
curl "https://api.aisa.one/apis/v1/financial/analyst-estimates?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Earnings Press Releases

```bash
# Get earnings press releases
curl "https://api.aisa.one/apis/v1/financial/earnings/press-releases?ticker=NVDA" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Note:** This endpoint has narrower ticker coverage than other financial endpoints. Passing an unsupported ticker returns `{"error":"Invalid ticker"}`. See [earnings-press-releases-tickers.md](./earnings-press-releases-tickers.md) for the full list of supported tickers (~2,776 as of 2026-04-14).

### Insider Trading

```bash
# Get insider trades
curl "https://api.aisa.one/apis/v1/financial/insider-trades?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Institutional Ownership

```bash
# Get institutional ownership (by ticker OR investor)
curl "https://api.aisa.one/apis/v1/financial/institutional-ownership?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### SEC Filings

```bash
# Get SEC filings
curl "https://api.aisa.one/apis/v1/financial/filings?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get SEC filing items (requires filing type and year)
curl "https://api.aisa.one/apis/v1/financial/filings/items?ticker=AAPL&filing_type=10-K&year=2024" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Company Facts

```bash
# Get company facts (by ticker or CIK)
curl "https://api.aisa.one/apis/v1/financial/company/facts?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Stock Screener

```bash
# Screen for stocks matching criteria
curl -X POST "https://api.aisa.one/apis/v1/financial/financials/search/screener" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filters":{"pe_ratio":{"max":15},"revenue_growth":{"min":0.2}}}'
```

### Search Line Items

```bash
# Search specific financial line items across tickers
curl -X POST "https://api.aisa.one/apis/v1/financial/financials/search/line-items" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tickers":["AAPL","MSFT"],"line_items":["revenue","net_income"],"period":"annual"}'
```

### Interest Rates (Macro)

```bash
# Current interest rates
curl "https://api.aisa.one/apis/v1/financial/macro/interest-rates/snapshot" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Historical interest rates
curl "https://api.aisa.one/apis/v1/financial/macro/interest-rates?bank=fed" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Python Client

```bash
# ==================== Stock Data ====================
# Note: start_date and end_date are REQUIRED for prices
python3 {baseDir}/scripts/market_client.py stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31
python3 {baseDir}/scripts/market_client.py stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31 --interval week
python3 {baseDir}/scripts/market_client.py stock news --ticker AAPL --count 10

# ==================== Financial Statements ====================
python3 {baseDir}/scripts/market_client.py stock statements --ticker AAPL --type all --period annual
python3 {baseDir}/scripts/market_client.py stock statements --ticker AAPL --type income --period quarterly
python3 {baseDir}/scripts/market_client.py stock statements --ticker AAPL --type balance --period annual
python3 {baseDir}/scripts/market_client.py stock statements --ticker AAPL --type cash --period ttm

# ==================== Segmented Revenues ====================
python3 {baseDir}/scripts/market_client.py stock segments --ticker AAPL --period annual

# ==================== Metrics & Analysis ====================
python3 {baseDir}/scripts/market_client.py stock metrics --ticker AAPL
python3 {baseDir}/scripts/market_client.py stock metrics --ticker AAPL --historical --period annual
python3 {baseDir}/scripts/market_client.py stock analyst --ticker AAPL
python3 {baseDir}/scripts/market_client.py stock earnings --ticker AAPL

# ==================== Insider & Institutional ====================
python3 {baseDir}/scripts/market_client.py stock insider --ticker AAPL
python3 {baseDir}/scripts/market_client.py stock ownership --ticker AAPL

# ==================== SEC Filings ====================
python3 {baseDir}/scripts/market_client.py stock filings --ticker AAPL
python3 {baseDir}/scripts/market_client.py stock filings --ticker AAPL --items --filing-type 10-K --year 2024

# ==================== Stock Screener / Line Items ====================
python3 {baseDir}/scripts/market_client.py stock screen --pe-max 15 --growth-min 0.2
python3 {baseDir}/scripts/market_client.py stock line-items --tickers AAPL,MSFT --items revenue,net_income --period annual

# ==================== Interest Rates ====================
python3 {baseDir}/scripts/market_client.py stock rates
python3 {baseDir}/scripts/market_client.py stock rates --historical --bank fed
```

---

## Contract status

Validated against the published OpenAPI contract (https://aisa.one/openapi.json) on 2026-10-20. `GET /financial/financials/segmented-revenues`, `GET /financial/earnings/press-releases` and `GET /financial/institutional-ownership` are **not in the published contract** and may return 404; no published operation covers the same data. Tracked in `scripts/validate_skills_known_issues.json` until the owner maps or removes them.

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/financial/prices` | GET | Historical stock prices (requires interval params) |
| `/financial/news` | GET | Company news by ticker |
| `/financial/financials` | GET | All financial statements (requires `period`) |
| `/financial/financials/income-statements` | GET | Income statements (requires `period`) |
| `/financial/financials/balance-sheets` | GET | Balance sheets (requires `period`) |
| `/financial/financials/cash-flow-statements` | GET | Cash flow statements (requires `period`) |
| `/financial/financials/segmented-revenues` | GET | Revenue by segment/geography (requires `period`) |
| `/financial/financial-metrics/snapshot` | GET | Real-time financial metrics |
| `/financial/financial-metrics` | GET | Historical metrics (requires `period`) |
| `/financial/analyst-estimates` | GET | EPS estimates |
| `/financial/earnings/press-releases` | GET | Earnings press releases (see [supported tickers](./earnings-press-releases-tickers.md)) |
| `/financial/insider-trades` | GET | Insider trades |
| `/financial/institutional-ownership` | GET | Institutional ownership |
| `/financial/filings` | GET | SEC filings |
| `/financial/filings/items` | GET | SEC filing items (requires `filing_type`, `year`) |
| `/financial/company/facts` | GET | Company facts |
| `/financial/financials/search/screener` | POST | Stock screener |
| `/financial/financials/search/line-items` | POST | Search specific line items across tickers |
| `/financial/macro/interest-rates/snapshot` | GET | Current interest rates |
| `/financial/macro/interest-rates` | GET | Historical rates |

---

## Pricing

| API | Cost |
|-----|------|
| Stock prices | ~$0.001 |
| Company news | ~$0.001 |
| Financial statements | ~$0.002 |
| Segmented revenues | ~$0.002 |
| Analyst estimates | ~$0.002 |
| Earnings press releases | ~$0.001 |
| SEC filings | ~$0.001 |
| Line items / screener | ~$0.002 |
| Interest rates | ~$0.0005 |

---

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://aisa.one/docs/api-reference/) for complete endpoint documentation.
