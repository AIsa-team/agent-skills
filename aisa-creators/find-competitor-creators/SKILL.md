---
name: find-competitor-creators
description: "Use AIsa social and commerce data to study competitor creator campaigns, identify disclosed partners and prioritize outreach."
license: MIT
metadata:
  version: "0.1.0"
---

# Find creators who promoted a competitor

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

“Who has promoted Ninja espresso machines and could fit our US campaign?” Use the named brand, product aliases, platform, target market and requested launch window. Keep the campaign’s observation dates with the evidence.

For a TikTok Shop market-specific lookup, use the resolved native ID with `id_namespace: tiktok_shop.creator` and the marketplace country. Omit `country` when using a handle, profile URL or FastMoss ID.

## AIsa operations

Task contract: [`creators.get_commerce_stats`](https://aisa.one/docs/tasks/creators-get_commerce_stats.md). Example POST body for the Tasks API:

```json
{"input": {"platform": "tiktok", "handle": "tannercolson"}}
```

Use AIsa for the lookup. Discover the matching Task/Plan or published tool on the connected MCP or CLI. Use the invocation schema returned by discovery; the JSON above illustrates the HTTP Task envelope. If only provider tools are exposed, select the named AIsa provider operation for the same outcome and quote its own arguments. Read the returned `status` (found, partial or not_found) and `result`. Preserve any coverage gaps.

For an allowed direct Tasks API fallback, read the linked Tasks reference and POST to its published operation on https://api.aisa.one. Quote the exact body with `X-AISA-Cost-Mode: quote`. For approved execution use a fresh `Idempotency-Key` per logical request and the approved `X-AISA-Max-Price-USD`; reconcile ambiguous requests before retrying. Derive subsequent IDs and enrichment costs from the results, not from guessed handles.

## Identify partnerships and assess performance

1. Discover AIsa post search for the target platform. For TikTok use `tiktok.search` with arguments such as `{"query":"Ninja Luxe Cafe #NinjaPartner","region":"US","datePosted":"last-3-months"}`. Also search the brand plus model without a disclosure tag so platform-labeled posts are discoverable. Inspect caption, paid-partnership label, linked product and author. Record post URL, date, exact disclosure and snapshot views. Treat an organic review or a seller-name match as a lead pending confirmation.
2. For a **strategy** question group confirmed posts by week, creator size if known, format and selling point. Show representative posts and describe this as the observed sample. For **breakout partners**, rank posts within comparable windows; compare with that creator’s usual performance only if enough comparable posts are available.
3. For **conversion**, use the Task above or discover AIsa TikTok Shop creator sales performance. Require same-product, same-period attribution for a conversion claim; a rate also needs a stated denominator. Account-wide GMV and video views alone cannot establish the sponsored post’s sales. If there are only two confirmed partners, return two.
4. For **pilot selection**, prioritize actual product fit, market evidence and sample creative. Distinguish an actual quoted fee from a budget allocation; mark fees for inquiry when unavailable.

Search the competitor’s brand and product aliases on each target platform using AIsa post/video search. Record the specific competitor keyword and evidence of collaboration for each returned creator.

For YouTube keyword evidence discover `get_youtube_search` (supply `q` and the schema-supported YouTube engine). For Instagram use `get_instagram_reels_search` with `query`, or `get_instagram_search_hashtag` with `hashtag`. Keep the matching post URL so a reviewer can trace each account to the query.

## Build the shortlist

Target 10 distinct creators unless the user gives another count. A named target platform restricts the entire search to that platform; a seed URL alone identifies the seed, not a target-platform restriction. Without a target platform, allocate **5 YouTube, 3 TikTok and 2 Instagram**, or swap the last two when Instagram better fits the campaign. Make separate platform-scoped discovery calls. A person with confirmed linked accounts occupies one slot. Exhaust relevant in-scope candidates within budget; report shortfalls rather than adding weak matches or silently changing platforms.

## Enrich each selected creator

Use AIsa profile and account-feed operations, rather than search-result rank, for the measurement sample. Discover their current schemas and quote exact calls. Resolve display name, follower/subscriber count and reported account region from the discovery result or `influencersclub.creators-enrich-profile`. Record source and retrieval date.

| Platform | Recent content through AIsa |
| --- | --- |
| YouTube | `youtube.channels.videos` with the resolved channel ID or handle and `sortBy: latest`; also read `youtube.channels.shorts` if Shorts are a separate feed. Merge by video ID and publication time. Look up missing video metrics with `youtube.videos` using the post URL. |
| TikTok | `tiktok.profiles.handle.videos` with the returned handle and `sortBy: latest`. Preserve pinned posts' original dates and paginate past older pinned items. |
| Instagram | `get_instagram_user_posts` with the handle and returned `next_max_id`; use `get_instagram_user_reels` to fill Reel coverage. Merge duplicate media IDs and retain post type; `get_instagram_post` takes the post URL for detail. |

For another explicitly requested platform, discover its AIsa author-feed and post-detail tools. Use post-detail/analytics lookup when a list omits counts or disclosures; a page of comments does not establish the total comment count. Retain post IDs, links, dates and metric provenance. Sort the creator's own public posts newest first; exclude reposts and duplicates, and page until the sample is covered or the source/budget is exhausted.

- **Recent performance.** Select the latest seven authored posts before looking at performance. Report mean views = sum of observed views / number of posts with observed views. For engagement report 100 × sum(likes + comments) / sum(views), using the same posts with all three metrics available. Count reported zeros, exclude missing values and report coverage separately (e.g. views 6/7, engagement 5/7). A zero total denominator is unavailable. Do not replace missing view counts on photos with impressions, or select older high performers to fill gaps.
- **Commercial content share.** Inspect captions, paid-partnership labels, affiliate disclosures and promotional CTAs on those same seven posts. Label each once: disclosed paid partnership, clearly promotional without confirmed payment, no visible commercial evidence, or insufficient evidence. Cite a post and the signal for each positive classification. A brand mention alone is insufficient. Report (disclosed + clearly promotional) / inspected classifiable posts, with both counts and coverage. If some are unknown, also give the possible range over the whole observed sample. Never describe the whole numerator as paid sponsorship.
- **Fan profile.** For every shortlisted profile, call [`creators.get_audience`](https://aisa.one/docs/tasks/creators-get_audience.md) with `input.platform` and `input.profile_url`, or reuse a matching sourced report. Give leading audience markets, age bands and gender shares where returned, with sample population/window. A creator’s region does not establish follower geography.
- **Contacts.** Use [`creators.find_contact`](https://aisa.one/docs/tasks/creators-find_contact.md) with `input.profile_url` or `post_waveinflu_email_lookup` with `body.profile_url` on a supported platform. Prefer a published business email and contact page; preserve their sources and distinguish a form from an email. Use mock addresses only for explicitly illustrative data. Quote enrichment batches for the selected candidates, reuse data between steps and disclose any coverage lost to budget or unavailable data.

## Return results and invitations

Use one row per creator: display name and @handle, platform, profile link, account region, followers, seven-post mean views, engagement rate, commercial share with disclosed/promotional split, fan profile, public contact link and business email, and a product-specific selection reason. Link a representative post and show its observed performance to support the reason. Include sample dates, field coverage and the final platform split. Separate campaign fit from any unmeasured sales or conversion claims.

For **each selected creator** write one professional outreach draft with subject, recipient and body. Mention a specific verified piece of their content, connect it to the user's product and audience, propose one feasible collaboration angle, and ask about interest, availability or rates. Tailor the opening and idea individually. Use the requested language or a supported recipient language. Leave unspecified commercial terms open and return drafts for review.
