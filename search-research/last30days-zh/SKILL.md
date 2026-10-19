---
name: last30days-zh
description: '聚合最近 30 天的 Reddit、X/Twitter、YouTube、TikTok、Instagram、Hacker News、Polymarket 和 web search 结果. Use when: the user needs recent multi-source research across the last 30 days.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, bash, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.10"
  aisa:
    emoji: 📰
    requires:
      bins:
      - python3
      - bash
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, bash, environment variables AISA_API_KEY and internet access to api.aisa.one.
    version: "1.0.10"
---

# last30days 中文版

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

聚合最近 30 天的社交平台、社区论坛、预测市场和 grounded web 结果，再合成为一份研究简报。

## 触发条件

- 当用户需要最近 30 天的人物、公司、产品、市场、工具或趋势研究时使用。
- 当用户需要竞品对比、发布反应、社区情绪、近期动态总结时使用。
- 当用户需要结构化 JSON 输出，例如 `query_plan`、`ranked_candidates`、`clusters`、`items_by_source` 时使用。

## 不适用场景

- 不适合纯百科类、没有时效要求的问题。
- 不适合只想看单一官方来源、完全不需要社区和社交信号的场景。

## 能力

- 通过 AISA 提供规划、重排、综合、grounded web search、X/Twitter、YouTube 和 Polymarket。
- Reddit 和 Hacker News 走公开路径。
- TikTok、Instagram、Threads、Pinterest 在启用时走托管发现路径。
- 对外发布层现在只保留无状态研究主链，不再默认携带旧的 watchlist / briefing / 第二凭证 GitHub 扩展面。

## 环境要求

- 主凭证：`AISA_API_KEY`
- Python `3.12+`
- 统一使用仓库相对路径下的 `scripts/` 命令，避免运行时变量替换失败。
- 可选 repo-local 配置文件：`./.last30days-data/config.env`，也可以直接传 `--api-key`。
- 小红书扩展只在显式提供 `XIAOHONGSHU_API_BASE` 时启用；公开发布包不会默认探测本地网络端点。

## 快速命令

```bash
bash scripts/run-last30days.sh "$ARGUMENTS" --emit=compact
python3 scripts/last30days.py "$ARGUMENTS" --api-key="$AISA_API_KEY"
python3 scripts/last30days.py "$ARGUMENTS" --emit=json
python3 scripts/last30days.py "$ARGUMENTS" --quick
python3 scripts/last30days.py "$ARGUMENTS" --deep
python3 scripts/last30days.py --diagnose
```

## 示例

- `last30days OpenAI Agents SDK`
- `last30days Peter Steinberger`
- `last30days OpenClaw vs Codex`
- `last30days Kanye West --quick`
