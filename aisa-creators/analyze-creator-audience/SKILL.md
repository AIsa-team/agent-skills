---
name: analyze-creator-audience
description: "Use AIsa audience reports to assess whether a known creator reaches a campaign market and audience, with source-specific coverage."
license: MIT
metadata:
  version: "0.1.0"
---

# Analyze a creator audience

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

Start with a profile and the intended buyer or market. When no campaign target is supplied, summarize audience composition and avoid inventing a target.

## AIsa operations

Task contract: [`creators.get_audience`](https://aisa.one/docs/tasks/creators-get_audience.md). Example POST body for the Tasks API:

```json
{"input": {"platform": "tiktok", "profile_url": "https://www.tiktok.com/@alexhomebarista"}}
```

Use AIsa for the lookup. Discover the matching Task/Plan or published tool on the connected MCP or CLI. Use the invocation schema returned by discovery; the JSON above illustrates the HTTP Task envelope. If only provider tools are exposed, select the named AIsa provider operation for the same outcome and quote its own arguments. Read the returned `status` (found, partial or not_found) and `result`. Preserve any coverage gaps.

For an allowed direct Tasks API fallback, read the linked Tasks reference and POST to its published operation on https://api.aisa.one. Quote the exact body with `X-AISA-Cost-Mode: quote`. For approved execution use a fresh `Idempotency-Key` per logical request and the approved `X-AISA-Max-Price-USD`; reconcile ambiguous requests before retrying. Derive subsequent IDs and enrichment costs from the results, not from guessed handles.

## Read the report

- Send platform plus exactly one identity. For native IDs include the required namespace. Inspect demographics and engagement coverage separately. Where the Task is unavailable on MCP, discover `influencersclub.creators-enrich-analytics`; for a supported account its arguments include `body.platform` and `body.handle`.
- For each source report, retain the observed population (followers, viewers or engagers), date/window, denominator, units and sample size when reported. Do not average incompatible providers, infer age or country from appearance, or turn a creator’s location into a follower statistic.
- Return a compact table of requested market shares, age bands and performance measures. For multiple handles, compare only like-for-like measures. A median calculated from recent posts must identify the sample and window; label provider-reported averages as averages.
- Close with one campaign implication supported by the data and the largest remaining gap. If the target is a joint segment such as US followers aged 25–34, separate marginal shares do not establish its size. For partial delivery list the available measures and missing components.

## Connect audience evidence to content recommendations

Use AIsa profile and account-feed operations, rather than search-result rank, for the measurement sample. Discover their current schemas and quote exact calls. Resolve display name, follower/subscriber count and reported account region from the discovery result or `influencersclub.creators-enrich-profile`. Record source and retrieval date.

| Platform | Recent content through AIsa |
| --- | --- |
| YouTube | `youtube.channels.videos` with the resolved channel ID or handle and `sortBy: latest`; also read `youtube.channels.shorts` if Shorts are a separate feed. Merge by video ID and publication time. Look up missing video metrics with `youtube.videos` using the post URL. |
| TikTok | `tiktok.profiles.handle.videos` with the returned handle and `sortBy: latest`. Preserve pinned posts' original dates and paginate past older pinned items. |
| Instagram | `get_instagram_user_posts` with the handle and returned `next_max_id`; use `get_instagram_user_reels` to fill Reel coverage. Merge duplicate media IDs and retain post type; `get_instagram_post` takes the post URL for detail. |

For another explicitly requested platform, discover its AIsa author-feed and post-detail tools. Use post-detail/analytics lookup when a list omits counts or disclosures; a page of comments does not establish the total comment count. Retain post IDs, links, dates and metric provenance. Sort the creator's own public posts newest first; exclude reposts and duplicates, and page until the sample is covered or the source/budget is exhausted.

Start from the supplied profile URL, even when no product brief is supplied. Analyze the latest seven public posts as a transparent starting sample. Group by topic and format (e.g. walkthrough, comparison, short review). Record views, likes, comments, publication dates and links. Within each comparable format show sample count, median views and view-based engagement, plus a representative post. Compare to the creator's own recent baseline; distinguish a single breakout from a recurring pattern and flag freshly posted content.

Finish the report with (1) the strongest observed topics/formats and their evidence, (2) two or three content or product categories this creator could credibly promote and why, connecting a measured audience characteristic with concrete content evidence when available, and (3) a tailored creative concept for the strongest recommendation. When demographics or post counts are sparse, state which conclusions rely on content alone and what evidence would improve them.
