---
name: aisa-tavily
description: 'Search the web and extract public page content through AIsa''s Tavily-backed API relay. Use when: the user needs web search, source discovery, current news lookup, or URL content extraction. Supports concise result sets, deeper research, and news-focused queries.'
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries node, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🔎
    requires:
      bins:
      - node
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries node, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# AIsa Tavily Search

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

Search the web and extract public page content through AIsa's Tavily-backed API relay. Use this skill when the user needs open-web research, source discovery, current-news lookup, or readable extraction from a specific public URL.

## When to use

- When the user needs web search results for a topic, question, company, product, or event
- When the user wants source discovery before summarizing, comparing, or validating information
- When the user needs current-news lookup with recent-day filtering
- When the user provides a public URL and wants the page content extracted for downstream analysis

## When NOT to use

- Do not use this skill for sites that require login, browser interaction, cookies, or private account access
- Do not use this skill for posting, social engagement, media upload, or OAuth-based workflows; it performs search and public-URL extraction only
- Do not use this skill when there is no network access to `https://aisa.one` or `https://api.aisa.one`

## Quick Reference

| Task | Command |
| --- | --- |
| Search the web | `node scripts/search.mjs "query"` |
| Search with more results | `node scripts/search.mjs "query" -n 10` |
| Run deeper research | `node scripts/search.mjs "query" --deep` |
| Search news | `node scripts/search.mjs "query" --topic news` |
| Search recent news only | `node scripts/search.mjs "query" --topic news --days 7` |
| Extract content from a URL | `node scripts/extract.mjs "https://example.com/article"` |

## Capabilities

- Search the web through AIsa's Tavily-backed relay
- Return concise, relevant result sets for research and agent workflows
- Run deeper research with `--deep` for broader coverage
- Focus on news search with `--topic news`
- Limit news lookback windows with `--days <n>`
- Extract readable content from a public URL

## Search

```bash
node scripts/search.mjs "query"
node scripts/search.mjs "query" -n 10
node scripts/search.mjs "query" --deep
node scripts/search.mjs "query" --topic news
```

## Options

- `-n <count>`: Number of results (default: 5, max: 20)
- `--deep`: Use advanced search for deeper research (slower, more comprehensive)
- `--topic <topic>`: Search topic - `general` (default) or `news`
- `--days <n>`: For news topic, limit to last n days

## Extract content from URL

```bash
node scripts/extract.mjs "https://example.com/article"
```

## Setup

Requirements:
- `node`
- `AISA_API_KEY`
- Internet access with outbound requests to `https://aisa.one` and `https://api.aisa.one`

Auth, relay, and side-effect notes:
- This skill requires `AISA_API_KEY` from https://marketplace.aisa.one
- Requests are sent through AIsa's remote relay at `https://aisa.one` and `https://api.aisa.one`
- This skill does not use OAuth
- This skill does not upload media or files
- This skill may send user search queries and public target URLs to the remote AIsa relay in order to return search results or extracted content

## Example Requests

- "Search for recent coverage of OpenAI enterprise pricing"
- "Find sources comparing vector databases for production RAG"
- "Look up this week's news about NVIDIA export controls"
- "Extract the main content from this article URL"

## Notes

- Needs `AISA_API_KEY` from https://marketplace.aisa.one
- Powered by AIsa's unified API gateway (`https://aisa.one` / `https://api.aisa.one`)
- Use `--deep` for complex research questions
- Use `--topic news` for current events
- Search and extraction operate through remote relay requests, not local browser automation
