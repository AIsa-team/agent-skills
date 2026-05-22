# AIsa API Endpoints — Trend Forecaster

Every endpoint the skill touches, documented from the actual calls in
`scripts/aisa_client.py`.

- **REST base URL:** `https://api.aisa.one/apis/v1`
- **LLM base URL:** `https://api.aisa.one/v1` (OpenAI-compatible — note: **no** `/apis`)
- **Auth header:** `Authorization: Bearer $AISA_API_KEY` on every request

---

## LLM Gateway (query decomposition + synthesis)

OpenAI-compatible. Base URL is `https://api.aisa.one/v1`. The skill uses
`gpt-4.1-mini` for both decomposition and synthesis (override with `--model`).

| Method | Path                   | Purpose                          | Price/call |
|--------|------------------------|----------------------------------|------------|
| POST   | `/v1/chat/completions` | Standard OpenAI chat completions | ~$0.01–0.05 (model-dependent) |

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4.1-mini", "messages": [...], "temperature": 0.3}'
```

Available models: `gpt-4.1`, `gpt-4.1-mini`, `claude-sonnet-4-20250514`,
`gemini-2.5-flash`, `deepseek-r1`, `qwen-3`, and 70+ more.

Client function: `llm_chat(messages, model="gpt-4.1-mini", temperature=0.3)`.

---

## MarketPulse — Stock / Financial Data (20 endpoints)

All under `/financial/`. Prices ~$0.001/call, financials ~$0.002/call,
macro ~$0.0005/call.

| Method | Path                                            | Purpose                                              |
|--------|-------------------------------------------------|------------------------------------------------------|
| GET    | `/financial/prices`                             | Historical stock prices (requires `interval`, e.g. `?ticker=AAPL&interval=day`) |
| GET    | `/financial/news`                               | Company news by ticker (`?ticker=AAPL`)              |
| GET    | `/financial/financials`                         | All financial statements (requires `period`, e.g. `?ticker=AAPL&period=annual`) |
| GET    | `/financial/financials/income-statements`       | Income statements (requires `period`)                |
| GET    | `/financial/financials/balance-sheets`          | Balance sheets (requires `period`)                   |
| GET    | `/financial/financials/cash-flow-statements`    | Cash flow statements (requires `period`)             |
| GET    | `/financial/financials/segmented-revenues`      | Revenue by segment and geography (requires `period`) |
| GET    | `/financial/financial-metrics/snapshot`         | Real-time financial metrics (`?ticker=AAPL`)         |
| GET    | `/financial/financial-metrics`                  | Historical metrics (requires `period`)               |
| GET    | `/financial/analyst-estimates`                  | EPS estimates (`?ticker=AAPL`)                       |
| GET    | `/financial/earnings/press-releases`            | Earnings press releases (~2,776 supported tickers)   |
| GET    | `/financial/insider-trades`                     | Insider trades (`?ticker=AAPL`)                      |
| GET    | `/financial/institutional-ownership`            | Institutional ownership (by ticker or investor)      |
| GET    | `/financial/filings`                            | SEC filings (`?ticker=AAPL`)                         |
| GET    | `/financial/filings/items`                      | SEC filing items (requires `filing_type` and `year`) |
| GET    | `/financial/company/facts`                      | Company facts (by ticker or CIK)                     |
| POST   | `/financial/financials/search/screener`         | Stock screener                                       |
| POST   | `/financial/financials/search/line-items`       | Search specific line items across tickers            |
| GET    | `/financial/macro/interest-rates/snapshot`      | Current interest rates                               |
| GET    | `/financial/macro/interest-rates`               | Historical rates                                     |

Client functions: `get_stock_prices`, `get_stock_news`, `get_financial_metrics`,
`get_analyst_estimates`, `get_insider_trades`, `get_interest_rates`. The
orchestrator pulls prices + metrics + news per ticker.

```bash
curl "https://api.aisa.one/apis/v1/financial/prices?ticker=AAPL&interval=day" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

> Use only real ticker symbols. Institution abbreviations (FED, SEC, FDA) are not
> tickers and will fail — for Fed topics use rate-sensitive ETFs like TLT/BND or
> financials like JPM/GS.

---

## Prediction Markets — Polymarket + Kalshi (16 endpoints)

All $0.010/call. Prices are decimals (`0.65` = 65% probability). The Yes price
is the probability the market thinks the event will happen.

**Two-step price lookup:** to get a price you must first query `/markets` to find
the market and its ID, then pass that ID to `/market-price/`. Polymarket uses
`token_id` (from `side_a.id` or `side_b.id` in the markets response); Kalshi uses
`market_ticker` (from the markets response).

| Method | Path                                            | Key params                              | Purpose                                                   |
|--------|-------------------------------------------------|-----------------------------------------|-----------------------------------------------------------|
| GET    | `/polymarket/markets`                           | `search`, `status`, `market_slug`, `limit` | List markets with fuzzy search                            |
| GET    | `/polymarket/market-price/{token_id}`           | `token_id`, `at_time`                   | Current/historical market price (probability 0–1)         |
| GET    | `/polymarket/events`                            | tags, status                            | Grouped related markets ordered by volume                 |
| GET    | `/polymarket/orderbooks`                        | market, condition, token                | Historical orderbook snapshots (bids, asks, metadata)     |
| GET    | `/polymarket/orders`                            | market, condition, token, time, wallet  | Historical trade data                                     |
| GET    | `/polymarket/activity`                          | wallet                                  | On-chain trading activity (MERGES, SPLITS, REDEEMS)       |
| GET    | `/polymarket/candlesticks/{condition_id}`       | `condition_id`                          | OHLC candlestick data with volume, open interest          |
| GET    | `/polymarket/positions/wallet/{wallet_address}` | `wallet_address`                        | Active positions for a proxy wallet                       |
| GET    | `/polymarket/wallet`                            | EOA, proxy, handle                      | Wallet info by EOA, proxy, or handle                      |
| GET    | `/polymarket/wallet/pnl/{wallet_address}`       | `wallet_address`                        | Realized PnL over time                                    |
| GET    | `/kalshi/markets`                               | `search`, `status`, `market_ticker`     | List Kalshi markets with fuzzy search                     |
| GET    | `/kalshi/market-price/{market_ticker}`          | `market_ticker`, `at_time`              | Current/historical yes/no pricing                         |
| GET    | `/kalshi/orderbooks`                            | market                                  | Historical orderbook snapshots                            |
| GET    | `/kalshi/trades`                                | market                                  | Executed trade history                                    |
| GET    | `/matching-markets/sports`                      | —                                       | Find equivalent markets across platforms                  |
| GET    | `/matching-markets/sports/{sport}`              | `sport`, date                           | Cross-platform sports markets by date                     |

Client functions: `search_prediction_markets` + `get_polymarket_price`
(Polymarket), `search_kalshi_markets` + `get_kalshi_price` (Kalshi).

```bash
# 1. Find the market
curl "https://api.aisa.one/apis/v1/polymarket/markets?search=Fed%20rate%20cut&status=open&limit=5" \
  -H "Authorization: Bearer $AISA_API_KEY"

# 2. Price the token (token_id = side_a.id / side_b.id from step 1)
curl "https://api.aisa.one/apis/v1/polymarket/market-price/<TOKEN_ID>" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Twitter / X (social sentiment)

| Method | Path                                       | Purpose                            |
|--------|--------------------------------------------|------------------------------------|
| GET    | `/twitter/tweet/advanced_search`           | Search tweets (`?query=...&queryType=Latest`, `Latest`\|`Top`) |
| GET    | `/twitter/trends`                          | Trending topics (`?woeid=1` = worldwide) |
| GET    | `/twitter/user/info`                       | User profile info (`?userName=...`) |
| GET    | `/twitter/user/last_tweets`                | User's recent tweets (`?userName=...`) |
| GET    | `/twitter/user/mentions`                   | User mentions (`?userName=...`)    |
| GET    | `/twitter/user/followers`                  | Follower list (`?userName=...`)    |
| GET    | `/twitter/user/followings`                 | Following list (`?userName=...`)   |
| GET    | `/twitter/user/batch_info_by_ids`          | Batch user info by IDs (`?userIds=...`) |
| GET    | `/twitter/user/search`                     | Search for users by keyword (`?query=...`) |

Client function: `search_twitter` (uses `/twitter/tweet/advanced_search`). Tweet
search params are `query` and `queryType` (`Latest`|`Top`) — there is no
`/twitter/search` endpoint or `search_type` param. Pricing varies by AIsa plan;
treat as ~$0.01/call for budgeting.

```bash
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=Fed%20rate%20cut&queryType=Latest" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Tavily — News / Web Search

| Method | Path             | Purpose                    | Price/call |
|--------|------------------|----------------------------|------------|
| POST   | `/tavily/search` | AI-optimized web search    | ~$0.01     |

Body fields: `query` (string), `search_depth` (`basic`|`advanced`),
`max_results` (5–20), `topic` (`general`|`news`), `days` (e.g. `7`).

Client function: `search_news`.

```bash
curl -X POST "https://api.aisa.one/apis/v1/tavily/search" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Fed rate cut", "search_depth": "advanced", "max_results": 10, "topic": "news", "days": 7}'
```

---

## Perplexity (supplemental deep research)

| Method | Path                  | Purpose                                |
|--------|-----------------------|----------------------------------------|
| POST   | `/perplexity/search`  | Deep research via Perplexity Sonar     |

Body: `{"query": "..."}`. Client function: `perplexity_search`.

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/search" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "outlook for AI chip demand 2026"}'
```

---

## Scholar / Web Search (supplemental)

| Method | Path                     | Purpose                                  |
|--------|--------------------------|------------------------------------------|
| POST   | `/scholar/search/web`    | Web search (`?query=...&max_num_results=10`) |
| POST   | `/scholar/search/smart`  | Smart hybrid search (`?query=...&max_num_results=10`) |
| POST   | `/scholar/search/scholar`| Academic search (`?query=...&max_num_results=10`) |
| POST   | `/scholar/explain`       | Confidence-scored explanation of results |

`/scholar/explain` body: `{"results": [...], "language": "en", "format": "summary"}`.
Not wired into the default orchestrator — available for deeper manual research.

---

## Per-forecast cost estimate

A typical forecast (decompose + 3–4 sources + synthesis) costs roughly:

- LLM calls (2× `gpt-4.1-mini`): ~$0.01–0.02
- Prediction markets: ~$0.01–0.02 (markets list + optional price lookups)
- Twitter search: ~$0.01
- Tavily news: ~$0.01
- Stock data (per ticker: prices + metrics + news): ~$0.003
- **Total: ~$0.05–0.08 per forecast**

Every response includes `usage.cost` and `usage.credits_remaining`. See
<https://aisa.one/docs/api-reference> for the full catalog and
<https://aisa.one/docs/guides/pricing> for current per-call pricing.
