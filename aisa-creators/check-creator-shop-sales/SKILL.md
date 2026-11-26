---
name: check-creator-shop-sales
description: "Use AIsa creator commerce and TikTok Shop data to review a creator’s sales history, product mix and suitability for an affiliate campaign."
license: MIT
metadata:
  version: "0.1.0"
---

# Check creator shop sales

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

Identify the creator, marketplace and requested reporting window. Resolve ambiguous handles before quoting lookups. Use the default or available reporting period only if clearly labeled.

For a TikTok Shop market-specific lookup, use the resolved native ID with `id_namespace: tiktok_shop.creator` and the marketplace country. Omit `country` when using a handle, profile URL or FastMoss ID.

## AIsa operations

Task contract: [`creators.get_commerce_stats`](https://aisa.one/docs/tasks/creators-get_commerce_stats.md). Example POST body for the Tasks API:

```json
{"input": {"platform": "tiktok", "handle": "tannercolson"}}
```

Use AIsa for the lookup. Discover the matching Task/Plan or published tool on the connected MCP or CLI. Use the invocation schema returned by discovery; the JSON below illustrates the HTTP Task envelope. If only provider tools are exposed, select the named AIsa provider operation for the same outcome and quote its own arguments. Read the returned `status` (found, partial or not_found) and `result`. Preserve any coverage gaps.

For an allowed direct Tasks API fallback, read the linked Tasks reference and POST to its published operation on https://api.aisa.one. Quote the exact body with `X-AISA-Cost-Mode: quote`. For approved execution use a fresh `Idempotency-Key` per logical request and the approved `X-AISA-Max-Price-USD`; reconcile ambiguous requests before retrying. Derive subsequent IDs and enrichment costs from the results, not from guessed handles.

## Read commerce at the right level

1. Send platform plus one identity. An ID from a shop, product or social post is not a creator ID. For a native ID preserve its provider namespace. Use the Task’s actual country enum and supported routing; TikTok returns commerce summaries/products, whereas other routes can return quotes only.
2. On MCP discover AIsa TikTok Shop **Get creator sales performance** and **Get creator listings** for the same market. Both require a resolved `creator_id` and `country`. For promoted products, `post_fastmoss_apis_v1_fastmoss_creator_productlist` is another AIsa source; use the FastMoss creator identifier and current body schema. Never substitute a TikTok handle into a numeric provider ID slot.
3. Present a creator summary with source, currency, observation window, creator-attributed GMV and units/orders separately where reported. Then show the leading products with links or source IDs, reported sales scope and overlap with the user’s category. Attribute live and video sales separately if the source supports it.
4. For comparisons use matching markets, dates, units and currencies. Keep estimated GMV distinct from settled revenue; do not sum product/shop totals into creator totals. An absent value is unknown, not zero. Include a commission rate or collaboration quote only when explicitly reported and scoped. End with a product-fit recommendation and one question to clarify before an offer.
