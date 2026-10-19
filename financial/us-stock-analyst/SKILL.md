---
name: us-stock-analyst
description: 'Professional US stock analysis with financial data, news, social sentiment, and multi-model AI. Comprehensive reports at $0.02-0.10 per analysis. Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries curl, python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.2"
  aisa:
    emoji: 📈
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

# US Stock Analyst 📈

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

**Professional equity analysis powered by AIsa's unified API platform.**

One API key. Complete market intelligence. AI-powered insights.

## 🔥 What Can You Do?

### Investment Research
```
"Analyze NVDA: financial metrics, analyst estimates, insider trades, 
news sentiment, and AI-powered valuation"
```

### Portfolio Monitoring
```
"Track my portfolio (AAPL, MSFT, GOOGL): daily updates on metrics, 
news, and sentiment changes"
```

### Earnings Analysis
```
"Full Tesla Q4 earnings analysis: results vs estimates, guidance, 
price reaction, analyst updates"
```

### Competitor Analysis
```
"Compare AMD vs NVDA: financials, growth, valuation, market sentiment"
```

### Screening & Discovery
```
"Find tech stocks with P/E < 30, revenue growth > 20%, 
and positive insider activity"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

---

## Core Capabilities

### 📊 Financial Data (MarketPulse APIs)

**Real-time Financial Metrics**
```bash
curl "https://api.aisa.one/apis/v1/financial/financial-metrics/snapshot?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Returns: Market cap, P/E ratio, revenue, EPS, profit margin, ROE, debt/equity, and more.

**Historical Stock Prices**
```bash
# Daily prices for last 30 days
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&start_date=2025-01-01&end_date=2025-01-31&interval=day&interval_multiplier=1" \
  -H "Authorization: Bearer $AISA_API_KEY"

# 5-minute intraday data
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&start_date=2025-02-07&end_date=2025-02-07&interval=minute&interval_multiplier=5" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Financial Statements**
```bash
# All statements (income, balance, cash flow)
curl "https://api.aisa.one/apis/v1/financial/financial_statements/all?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Analyst Estimates**
```bash
# EPS forecasts and ratings
curl "https://api.aisa.one/apis/v1/financial/analyst/eps?ticker=AAPL&period=annual" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Insider Trading**
```bash
# Track insider buy/sell activity
curl "https://api.aisa.one/apis/v1/financial/insider/trades?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Institutional Ownership**
```bash
# See who owns the stock
curl "https://api.aisa.one/apis/v1/financial/institutional/ownership?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**SEC Filings**
```bash
# Access 10-K, 10-Q, 8-K filings
curl "https://api.aisa.one/apis/v1/financial/sec/filings?ticker=AAPL" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

### 📰 News & Research

**Company News**
```bash
curl "https://api.aisa.one/apis/v1/financial/news?ticker=AAPL&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Web Search (News & Articles)**
```bash
curl -X POST "https://api.aisa.one/apis/v1/scholar/search/web?query=AAPL+stock+analysis&max_num_results=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Academic Research**
```bash
curl -X POST "https://api.aisa.one/apis/v1/scholar/search/scholar?query=semiconductor+industry+analysis&max_num_results=5" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

### 🐦 Social Sentiment

**Twitter Search**
```bash
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=\$AAPL&queryType=Latest" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

### 📺 Video Content

**YouTube Search (Earnings Calls, Analysis)**
```bash
curl "https://api.aisa.one/apis/v1/youtube/search?engine=youtube&q=AAPL+earnings+call&gl=us&hl=en" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

### 🤖 AI Analysis (Multi-Model)

**LLM Gateway (OpenAI Compatible)**
```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are a professional equity analyst."
      },
      {
        "role": "user",
        "content": "Analyze Apple stock investment prospects"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 2000
  }'
```

**Supported Models:**
- GPT-4, GPT-4 Turbo (OpenAI)
- Claude 3 Opus, Sonnet, Haiku (Anthropic)
- Gemini 1.5 Pro, Ultra (Google)
- Qwen Max, Plus (Alibaba)
- DeepSeek V2 (DeepSeek)
- Grok (xAI)

---

## Python Client

```bash
# Basic analysis
python3 scripts/stock_analyst.py analyze --ticker AAPL

# Standard analysis with multiple models
python3 scripts/stock_analyst.py analyze --ticker NVDA --depth standard --models gpt-4 claude-3-opus

# Deep analysis (all data sources)
python3 scripts/stock_analyst.py analyze --ticker TSLA --depth deep

# Quick screening
python3 scripts/stock_analyst.py analyze --ticker MSFT --depth quick

# Save report to file
python3 scripts/stock_analyst.py analyze --ticker GOOGL --output report.json
```

---

## Analysis Depth Options

| Mode | Time | Cost | Data Sources |
|------|------|------|--------------|
| **quick** | ~10s | $0.01-0.02 | Metrics, News, Twitter, Basic AI |
| **standard** | ~20s | $0.02-0.05 | + Analyst Estimates, Insider Trades, YouTube |
| **deep** | ~30s | $0.05-0.10 | + Statements, Institutional, SEC, Research |

---

## API Reference

| Category | Endpoint | Method | Cost |
|----------|----------|--------|------|
| **Financial Metrics** | `/financial/financial-metrics/snapshot` | GET | $0.002 |
| **Stock Prices** | `/financial/prices` | GET | $0.001 |
| **News** | `/financial/news` | GET | $0.001 |
| **Statements** | `/financial/financial_statements/*` | GET | $0.002 |
| **Analyst Estimates** | `/financial/analyst/eps` | GET | $0.002 |
| **Insider Trades** | `/financial/insider/trades` | GET | $0.001 |
| **Institutional** | `/financial/institutional/ownership` | GET | $0.001 |
| **SEC Filings** | `/financial/sec/filings` | GET | $0.001 |
| **Web Search** | `/scholar/search/web` | POST | $0.001 |
| **Scholar Search** | `/scholar/search/scholar` | POST | $0.002 |
| **Twitter** | `/twitter/tweet/advanced_search` | GET | $0.0004 |
| **YouTube** | `/youtube/search` | GET | $0.002 |
| **LLM** | `/v1/chat/completions` | POST | Token-based |

Every response includes `usage.cost` and `usage.credits_remaining`.

---

## Example Output

```json
{
  "ticker": "NVDA",
  "analysis_date": "2025-02-07T10:30:00Z",
  
  "investment_summary": "NVIDIA maintains dominant position in AI chip market with strong data center revenue growth. Recent Blackwell launch positions company for continued expansion...",
  
  "key_metrics": {
    "market_cap": 1780500000000,
    "pe_ratio": 68.5,
    "revenue": 60922000000,
    "revenue_growth": 1.26,
    "profit_margin": 0.489,
    "roe": 1.152
  },
  
  "sentiment_analysis": {
    "sentiment": "bullish",
    "confidence": "high",
    "key_themes": ["AI dominance", "Data center growth", "Blackwell launch"],
    "summary": "Overwhelmingly positive sentiment following Q4 earnings beat"
  },
  
  "valuation": {
    "assessment": "fairly_valued",
    "price_target_12m": 850.00,
    "reasoning": "Premium valuation justified by AI market leadership and strong growth trajectory"
  },
  
  "data_sources": {
    "Financial Metrics": "Available",
    "Stock News": 10,
    "Analyst Estimates": "Available",
    "Insider Trades": 15,
    "Twitter": "Available",
    "YouTube": 5
  }
}
```

---

## Pricing

**Analysis Costs:**
- Quick: $0.01-0.02 per stock
- Standard: $0.02-0.05 per stock
- Deep: $0.05-0.10 per stock

**Comparison:**
- Bloomberg Terminal: $2,000/month
- FactSet: $1,000/month
- Traditional Analyst Report: $50-500 each
- **AIsa Stock Analyst: $0.02-0.10 each** ✨

**Cost Breakdown:**
```
Standard Analysis ($0.02-0.05):
├── Financial Metrics: $0.002
├── Stock Prices: $0.001
├── Company News: $0.001
├── Analyst Estimates: $0.002
├── Insider Trades: $0.001
├── Twitter: $0.0004
├── YouTube: $0.002
└── LLM Analysis: $0.01-0.04
```

---

## Use Cases

### 1. Investment Research
Screen and analyze stocks before investing:
```python
analyst.analyze_stock("NVDA", depth="deep")
```

### 2. Portfolio Monitoring
Daily updates on your holdings:
```python
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    report = analyst.analyze_stock(ticker, depth="quick")
```

### 3. Earnings Season
Comprehensive earnings analysis:
```python
analyst.analyze_stock("TSLA", depth="standard")
# Check estimates, actual results, guidance, reaction
```

### 4. Insider Tracking
Monitor insider activity:
```python
report = analyst.analyze_stock("META", depth="standard")
print(report['raw_data']['insider_trades'])
```

### 5. Sentiment Analysis
Track market perception:
```python
report = analyst.analyze_stock("COIN", depth="standard")
print(report['sentiment_analysis'])
```

---

## Compliance

**Disclaimer (Always Included):**
> This analysis is for informational purposes only and should not be 
> considered personalized investment advice. Please conduct your own 
> research and consult with licensed financial advisors before making 
> investment decisions.

**Regulatory Compliance:**
- SEC Rule 15c2-1 (not investment advice)
- FINRA regulations (informational only)
- GDPR data privacy compliant

---

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go, minimum $5)
4. Set environment variable: `export AISA_API_KEY="your-key"`
5. Run analysis: `python scripts/stock_analyst.py analyze --ticker AAPL`

---

## Full API Documentation

- **API Reference**: https://aisa.mintlify.app/api-reference/introduction
- **Complete Docs**: https://aisa.mintlify.app/llms.txt
- **Support**: support@aisa.one
- **Discord**: https://discord.gg/aisa

---

## About AIsa

**AIsa** - Unified API infrastructure for AI agents.

Single API Key. Pay-Per-Use. Agent-Native.

- Website: https://aisa.one
- Documentation: https://aisa.mintlify.app
