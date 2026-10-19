---
name: aisa-twitter-api
description: Search and inspect Twitter/X posts, profiles, timelines, communities, and trends through AIsa, or publish user-authorized posts with OAuth. Use for recent X research, account comparisons, conversation review, and approved text or media posting.
license: Apache-2.0
compatibility: Requires Python 3.11+, a POSIX system, AISA_API_KEY, and access to api.aisa.one. Executed requests require an authorized estimate budget; publishing also requires the linked X account and user authorization.
metadata:
  version: "1.1.1"
  aisa:
    emoji: 🐦
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Requires Python 3.11+, a POSIX system, AISA_API_KEY, and access to api.aisa.one. Executed requests require an authorized estimate budget; publishing also requires the linked X account and user authorization.
    version: "1.1.1"
---
# AIsa Twitter API

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

Use the read client for one-page research and the OAuth client for approved
posting. Both preserve provider data, report failures with nonzero exit status,
and account for requests through a durable cost ledger. This skill does not
create schedules or maintain a persistent watchlist by itself.

## Setup

Resolve commands relative to this installed skill directory, or use absolute
script paths. Python 3.11+ and a POSIX system are required; there are no third-party
runtime packages.

`AISA_API_KEY` resolves from the environment, then `~/.aisa/credentials`, then the
active Hermes profile configuration. Do not print the key or put it in command
arguments. OAuth binds the X account to that AIsa key; account authorization does
not itself authorize publishing content.

## Research

```bash
# Inspect an authenticated free quote; this does not retrieve posts.
python3 scripts/twitter_client.py search --query "AI agents" --type Latest --quote

# Execute within the user's approved estimate budget.
python3 scripts/twitter_client.py search --query "AI agents" --type Latest \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json

# Reuse the same task budget for another page or operation.
python3 scripts/twitter_client.py community-search --query "AI agents" --type Top \
  --cost-ledger research-costs.json
```

Read [cost controls and recovery](references/cost-control.md) before execution.
When a quote reports `may_exceed_estimate`, use `--allow-variable-cost` only if the
user accepted that possibility. Admission estimates are not final-charge caps.

Use `--help` for profiles, timelines, followers, searches, tweet detail/replies,
lists, and communities. Results contain original provider objects plus `_aisa`
HTTP and billing metadata. Native IDs, URLs, timestamps, metrics, and cursors are
not rewritten. Report missing data as missing; a quote is not retrieved evidence.

Requests fetch one page. Use a returned cursor only on an operation that supports
it, and reuse the ledger for additional pages. `mentions`, `user-search`, and
`quotes` reject nonempty cursors because the current parameter contracts do not
declare them despite pagination prose. `space-detail` is blocked before network
access because its contract does not declare the required cost controls.

For a time-bounded research question, include the appropriate X search operators
(e.g. `since:YYYY-MM-DD until:YYYY-MM-DD`) and inspect result dates before drawing
conclusions. Link supporting posts and describe the coverage actually retrieved.
Do not turn a one-off research request into scheduled monitoring.

## Approved posting

Read [posting and media](references/post_twitter.md) for account linking, exact
payloads, thread behavior, and recovery. Use the user's authorized text, target,
attachments, and number of posts. OAuth approval only links an account.

```bash
# Preview locally without credentials, spending, uploads, or publishing.
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" --dry-run

# Link an account when needed; --media also requests media.write for uploads.
python3 scripts/twitter_oauth_client.py authorize --media \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger posting-costs.json

# Publish the authorized content using the existing task budget.
python3 scripts/twitter_oauth_client.py post --text "$APPROVED_TEXT" \
  --cost-ledger posting-costs.json
```

Local files use the dedicated binary upload endpoint, followed by a post using
returned media IDs. Each request is separately quoted and recorded. Existing
media IDs can be attached directly. Oversized content requires explicit
`--thread`; inspect `--dry-run` output before publishing the expanded thread.

No external write is retried automatically. If an upload/post result is ambiguous,
inspect the account and request-specific billing evidence before continuing.
Preserve confirmed IDs and partial results. Do not republish an entire thread to
recover a failed later chunk. `status` shows local configuration, not live OAuth
account validity. Do not request X passwords or browser cookies.

## API contracts

The clients use [AIsa's Twitter API](https://aisa.one/docs/api-reference) with
Bearer authentication. The operation/parameter snapshot used by tests is in
`tests/fixtures/provider_contracts.json`; live contracts remain authoritative.

- [Advanced search](https://aisa.one/docs/api-reference/twitter/get_twitter-tweet-advanced-search)
- [Community search](https://aisa.one/docs/api-reference/twitter/get_twitter-community-get-tweets-from-all-community)
- [OAuth authorization](https://aisa.one/docs/api-reference/twitter/post_twitter-auth-twitter)
- [Media upload](https://aisa.one/docs/api-reference/twitter/post_twitter-upload-media)
- [Post creation](https://aisa.one/docs/api-reference/twitter/post_twitter-post-twitter)
- [Billing and quote semantics](https://aisa.one/docs/guides/pricing)

## Validation

```bash
python3 -m unittest discover -s tests -v
```

Tests use fixtures and mocked transport; they do not authorize accounts, upload
media, publish posts, or execute paid retrieval.
