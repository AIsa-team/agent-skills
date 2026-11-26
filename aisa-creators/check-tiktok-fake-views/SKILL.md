---
name: check-tiktok-fake-views
description: "Assess view inflation for a TikTok video or the most-viewed of a creator’s ten latest posts, with a sourced risk score and collaboration recommendation."
license: MIT
metadata:
  version: "0.1.0"
---

# Check a TikTok video for inflated views

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

## Select the video

- **Video URL or numeric item ID:** inspect that exact video. Extract the digits after `/video/` as a string; resolve short links to a canonical public URL.
- **Creator profile:** resolve the TikTok handle. Discover and quote `tiktok.profiles.handle.videos` with `{"handle":"alexhomebarista","sortBy":"latest","includePinned":true}`. List the ten most recent distinct authored posts by original publication timestamp. Page past older pinned posts, preserve their actual dates and exclude reposts. From that chronological ten choose the video with the highest observed view count; break ties by latest publication. Do not use the profile’s all-time popular feed.
- Keep an audit strip with the sampled dates, video links and view counts. If a count is missing, try `get_tikhub_tiktok_analytics_fetch_video_metrics` for that item. With unresolved counts or fewer than ten public posts, disclose the coverage and call the selection the highest **observed** video. For a private/empty account or no usable views, report insufficient evidence and request a public video link.

## AIsa operations

Published AIsa tool: `get_tikhub_tiktok_analytics_detect_fake_views`. Discover its schema, quote the exact arguments, and run the approved call. Example MCP arguments:

```json
{"item_id":"7460937381265411370","content_category":"product"}
```

HTTP fallback under the shared rules: `GET https://api.aisa.one/apis/v1/tikhub/tiktok/analytics/detect_fake_views` with the same query parameters. Use `default` when the content category is unknown. The [operation reference](https://aisa.one/docs/api-reference/tikhub/get_tikhub-tiktok-analytics-detect_fake_views) documents the supported benchmarks.

## Score the selected video and advise on collaboration

Return the selected link, selection basis, snapshot date, content category, `fake_view_analysis.fake_score` **out of 100** (higher is riskier) and the returned risk level. Cite `main_detection_reason`, relevant component scores, `suspicious_features`, and available metric values. Put anomalies in context using comparable posts from the sampled profile. Note content age, paid amplification or format differences when evidenced. Distinguish the score from the separately modeled fake-view percentage; neither establishes that the creator purchased views.

Close with one campaign decision and a specific reason. Low reported risk with adequate evidence: proceed given campaign fit. Medium or conflicting evidence: recommend a limited pilot or request native analytics before committing. High/critical risk with corroborating signals: recommend against a reach-priced partnership pending review. If the provider omits the numeric score, label it unavailable and report the returned level; if evidence cannot support a decision, recommend deferring the partnership. For a profile input, make clear the score belongs to the selected breakout video and qualify any creator-level recommendation accordingly.
