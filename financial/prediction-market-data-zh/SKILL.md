---
name: prediction-market-data-zh
description: '通过 AIsa API 查询跨平台预测市场数据。支持 Polymarket 和 Kalshi 的市场行情、价格、订单簿、K线、持仓和交易记录。适用场景：查询预测市场赔率、选举博彩、事件概率、市场情绪、Polymarket 价格、Kalshi 价格、体育博彩赔率、钱包盈亏、跨平台市场对比。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 📈
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# 预测市场数据

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

通过 [AIsa API](https://aisa.one) 查询 [Polymarket](https://polymarket.com) 和 [Kalshi](https://kalshi.com) 预测市场。

## 配置

```bash
export AISA_API_KEY="your-key"
```

在 [aisa.one](https://aisa.one) 获取 Key（$0.01/次查询，按量付费）。

## 工作流程

查询预测市场数据的步骤：

1. **搜索市场**获取 ID（必须从这一步开始）
2. **从返回结果中提取 ID**（`token_id`、`condition_id` 或 `market_ticker`）
3. **用 ID 查询详情**（价格、订单簿、K线等）

## 快速示例

### Polymarket：搜索 → 获取价格

```bash
# 第一步：搜索市场，提取 token_id（side_a.id 或 side_b.id）
python3 scripts/prediction_market_client.py polymarket markets --search "election" --status open --limit 5

# 第二步：用第一步的 token_id 获取价格
python3 scripts/prediction_market_client.py polymarket price <token_id>
```

### Kalshi：搜索 → 获取价格

```bash
# 第一步：搜索市场，提取 market_ticker
python3 scripts/prediction_market_client.py kalshi markets --search "fed rate" --status open --limit 5

# 第二步：用第一步的 market_ticker 获取价格
python3 scripts/prediction_market_client.py kalshi price <market_ticker>
```

### 跨平台体育市场

```bash
python3 scripts/prediction_market_client.py sports by-date nba --date 2025-04-01
```

## ID 参考

大多数命令需要从 `markets` 返回中获取 ID，务必先搜索。

| 平台 | ID 字段 | 获取位置 |
|------|---------|----------|
| Polymarket | `token_id` | markets 输出中的 `side_a.id` 或 `side_b.id` |
| Polymarket | `condition_id` | markets 输出中的 `condition_id` |
| Kalshi | `market_ticker` | markets 输出中的 `market_ticker` |

## 命令参考

### Polymarket

```bash
python3 scripts/prediction_market_client.py polymarket markets [--search <关键词>] [--status open|closed] [--min-volume <数值>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket price <token_id> [--at-time <unix时间戳>]
python3 scripts/prediction_market_client.py polymarket activity --user <钱包地址> [--market-slug <slug>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket orders [--market-slug <slug>] [--token-id <id>] [--user <钱包地址>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket orderbooks --token-id <id> [--start <毫秒>] [--end <毫秒>] [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket candlesticks <condition_id> --start <unix时间戳> --end <unix时间戳> [--interval 1|60|1440]
python3 scripts/prediction_market_client.py polymarket positions <钱包地址> [--limit <数值>]
python3 scripts/prediction_market_client.py polymarket wallet (--eoa <地址> | --proxy <地址>) [--with-metrics]
python3 scripts/prediction_market_client.py polymarket pnl <钱包地址> --granularity <day|week|month>
```

### Kalshi

```bash
python3 scripts/prediction_market_client.py kalshi markets [--search <关键词>] [--status open|closed] [--min-volume <数值>] [--limit <数值>]
python3 scripts/prediction_market_client.py kalshi price <market_ticker> [--at-time <unix时间戳>]
python3 scripts/prediction_market_client.py kalshi trades [--ticker <ticker>] [--start <unix时间戳>] [--end <unix时间戳>] [--limit <数值>]
python3 scripts/prediction_market_client.py kalshi orderbooks --ticker <ticker> [--start <毫秒>] [--end <毫秒>] [--limit <数值>]
```

### 跨平台体育市场

```bash
python3 scripts/prediction_market_client.py sports matching (--polymarket-slug <slug> | --kalshi-ticker <ticker>)
python3 scripts/prediction_market_client.py sports by-date <运动类型> --date <YYYY-MM-DD>
```

支持：`nfl`、`mlb`、`cfb`、`nba`、`nhl`、`cbb`、`pga`、`tennis`。

## 理解赔率

价格为小数：`0.65` = 65% 隐含概率。"Yes" 价格 = 事件发生的概率。交易量越高 = 流动性越强。

## 契约状态（Contract status）

Validated against the published OpenAPI contract (https://aisa.one/openapi.json) on 2026-10-20. The routes below, used by this skill and its bundled client, are **not in the published contract** and may return 404. They are tracked with reasons in `scripts/validate_skills_known_issues.json` until the owner maps or removes them; the published operations that cover the same data have different parameters, so they were not substituted automatically:

| Legacy route in this skill | Published operation to migrate to |
|---|---|
| `GET /polymarket/market-price/{token_id}` | `GET /polymarket/price?token_id=&side=`, `GET /polymarket/midpoint?token_id=`, `GET /polymarket/prices-history?market=` |
| `GET /polymarket/orderbooks` | `GET /polymarket/book?token_id=`, `GET /polymarket/books?token_ids=` |
| `GET /polymarket/orders` (trade history) | `GET /polymarket/activity`, `GET /polymarket/data/orders` (the published `/polymarket/orders` is POST/DELETE order management) |
| `GET /polymarket/candlesticks/{condition_id}` | `GET /polymarket/prices-history?market=&interval=&fidelity=` |
| `GET /polymarket/positions/wallet/{wallet_address}` | `GET /polymarket/positions?user=` |
| `GET /polymarket/wallet`, `GET /polymarket/wallet/pnl/{wallet_address}` | `GET /polymarket/public-profile?address=`, `GET /polymarket/closed-positions?user=`, `GET /polymarket/value?user=` |
| `GET /kalshi/market-price/{market_ticker}` | `GET /kalshi/markets/{ticker}` |
| `GET /kalshi/orderbooks` | `GET /kalshi/markets/{ticker}/orderbook` |
| `GET /matching-markets/sports[/{sport}]` | no published equivalent (`GET /polymarket/sports` lists Polymarket sports only) |

## 安全与权限

**需要：** `AISA_API_KEY` 环境变量。

所有操作均为**只读**，通过 HTTPS GET 请求 `api.aisa.one`。不执行交易、不连接钱包、除 API Key 外不发送个人数据。每次调用的实际费用通过响应头 `X-AISA-Customer-Cost-Micros-USD`（整数微美元，1 美元 = 1,000,000 微美元）返回，响应体中没有费用字段。

完整文档：[AIsa API 参考](https://docs.aisa.one/reference/)。
