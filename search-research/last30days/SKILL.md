---
name: last30days
description: Research the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web search. Returns a ranked, clustered brief with citations. Use when the task needs recent social evidence, competitor comparisons, launch reactions, trend scans, or person/company profiles.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3.11+ and a POSIX shell; hosted retrieval requires AISA_API_KEY and an authorized budget.
metadata:
  version: "1.1.1"
  aisa:
    emoji: 📰
    homepage: https://aisa.one
    requires:
      bins:
      - python3
      - bash
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
# last30days 📰

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

**30-day multi-source research brief for autonomous agents. Powered by AIsa.**

Combine public Reddit and Hacker News, AIsa-hosted X/YouTube/Polymarket/web retrieval, optional GitHub, and indexed TikTok/Instagram web discoveries into one ranked evidence brief. Native social engagement is not available from web discovery.

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

Requires Python 3.11+, a POSIX shell, and `AISA_API_KEY` for hosted retrieval (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Trend scan
```text
"last30days OpenAI Agents SDK"
```

### Competitor comparison
```text
"last30days Claude Code vs Codex"
```

### Person / company profile
```text
"last30days Peter Steinberger"
```

### Launch reaction
```text
"last30days GPT-5 launch --deep"
```

### Prediction-market angle
```text
"last30days bitcoin price"
```

## Quick Start

```bash
# 1. Export your AIsa key
export AISA_API_KEY=sk-...

# 2. Optional setup: inspect configuration and choose model pins
bash scripts/run-last30days.sh setup

# 3. Research within the user-authorized estimate budget
bash scripts/run-last30days.sh "OpenAI Agents SDK" \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json
```

Run paths relative to the installed skill directory, or resolve them to absolute paths.
The wrappers preserve the caller's working directory and project configuration.
Public-source/local and `--mock` runs do not need an AIsa key or budget.

For hosted work, honor the budget the user actually authorized. Read
[request costs and recovery](references/cost-control.md) before running paid retrieval.
Quotes marked `may_exceed_estimate` require explicit acceptance via
`--allow-variable-cost`; the final charge can exceed the admission estimate.

## Common Flags

```bash
# Low-latency profile (fewer candidates per source)
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --quick

# Higher-recall profile
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --deep

# Machine-readable output (full plan + candidates + clusters)
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --emit=json

# Restrict to specific sources
bash scripts/run-last30days.sh "$ARGUMENTS" --cost-ledger research-costs.json --search=reddit,x,grounding

# Inspect configured providers/sources (does not verify live availability)
bash scripts/run-last30days.sh --diagnose
```

## Inputs and Outputs

**Input.** A topic, person, company, product, or comparison — e.g.
`OpenAI Agents SDK`, `OpenClaw vs Codex`, `Peter Steinberger`.

**Output.** A markdown brief (default) or JSON with:

- `query_plan` — planner-generated subqueries and source weights
- `ranked_candidates` — reranked candidate pool with scores
- `clusters` — semantically grouped findings
- `items_by_source` — per-source item lists with dates, engagement, URLs
- `provider_runtime` — configured reasoning models and retrieval backends; inspect plan notes/warnings for fallbacks
- `errors_by_source` — failures, including partial source failures
- `artifacts.source_coverage` — retained counts and unavailable/empty/partial/failed source status
- `artifacts.costs` — exact known charges, unresolved requests, and durable ledger location

## When to use

- You need last-30-days evidence on a person, company, product, market, tool, or trend.
- You want a ranked competitor comparison, launch-reaction summary, creator/community sentiment scan, or shipping update.
- You want a structured JSON brief to feed into another agent.

## When NOT to use

- Timeless reference questions with no recent-evidence requirement.
- When you only want one official source and don't want social/community signals.

## Capabilities

- **Hosted retrieval**: X, YouTube, Polymarket public search, and Tavily web search through AIsa. TikTok/Instagram are indexed web discoveries, with unknown native engagement preserved as missing.
- **Public paths**: Reddit and Hacker News; GitHub is optional with `GH_TOKEN` or `GITHUB_TOKEN`.
- **Freshness**: ranked posts/articles require valid publication dates inside the requested window. Undated, future, and older items are excluded. Polymarket entries are explicitly labeled current observations, with resolution dates kept separate; they do not establish historical price movement.
- **Partial failures** remain visible when a source also returns usable results.

## Reasoning configuration

Deterministic planning and local ranking work without model configuration.
The current chat endpoint does not declare quote/admission-limit support, so
this release blocks hosted reasoning calls before dispatch and uses those local
fallbacks. Retrieval APIs with verified cost capabilities remain available.
Model pins (`AISA_MODEL` or per-role `LAST30DAYS_*_MODEL`) are retained for
configuration compatibility; their presence does not prove a model was called.

Unknown flags, malformed external plans, invalid date windows, and unsupported
creator/hashtag or deep-research options fail before research. `--lookback-days`
accepts 1–365 days. Mock mode covers Reddit, X, and web fixtures and performs no
network calls. The historical revision evaluator is restricted to mock mode
because old revisions do not provide the current accounting guarantees.

## API Reference

last30days calls the following AIsa endpoints directly. See the
[full API Reference](https://aisa.one/docs/api-reference) for the
complete catalog.

- [OpenAI Chat / `createChatCompletion`](https://aisa.one/docs/api-reference/chat/createchatcompletion) — configured reasoning integration; dispatch blocked pending verified cost capabilities
- [Twitter Advanced Search](https://aisa.one/docs/api-reference/twitter/get_twitter-tweet-advanced-search) — X retrieval
- [YouTube Search](https://aisa.one/docs/api-reference/search/get_youtube-search) — YouTube retrieval
- [Tavily Search](https://aisa.one/docs/api-reference/search/post_tavily-search) — grounded web
- [Polymarket Public Search](https://aisa.one/docs/api-reference/polymarket-gamma/any_polymarket_data_apis_v1_polymarket_public_search) — prediction-market retrieval

Reddit and Hacker News use their respective public APIs directly (no
AISA proxy required).

## Requirements

- **Python 3.11+**
- **`AISA_API_KEY`** — required for hosted retrieval. Get one at [aisa.one](https://aisa.one).
- **`GH_TOKEN` / `GITHUB_TOKEN`** — optional, enables the GitHub source.

```bash
# Optionally select a supported interpreter
for py in python3.14 python3.13 python3.12 python3.11 python3; do
  command -v "$py" >/dev/null 2>&1 || continue
  "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || continue
  export LAST30DAYS_PYTHON="$py"
  break
done
```
