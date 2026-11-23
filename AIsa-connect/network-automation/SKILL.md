---
name: network-automation
description: "Build a routine network health review from existing telemetry, device inventory and tickets through AIsa Connect. Use for branch health checks, asset reconciliation and evidence-linked Jira or Slack updates; not autonomous network configuration or incident command."
license: MIT
metadata:
  version: "0.1.0"
---

# Network Automation

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

IT teams and network administrators. Work across the app accounts the user connects through AIsa.

Before reading or changing connected app data, read
[references/connect-runtime.md](references/connect-runtime.md). It defines account
selection, capability discovery, execution and recovery for this workflow.

## App roles

Choose the user's available stack; alternatives in a row are choices, not a
requirement to connect every app. Verify live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| Datadog | Existing network telemetry and monitor states, if configured |
| Cisco Meraki (optional) | Organizations, networks, device inventory and device details |
| Jira | Existing network tickets and a supported issue/comment destination |
| Slack; Teams or Feishu as alternatives | Internal operations handoff |
| Databox (optional) | Ingest approved health summaries and check ingestion status |
| Notion, Confluence or Google Sheets (optional) | Asset baseline, runbook and inspection record |

## Scope a routine inspection

Resolve organization, branch/network, device scope, time window, timezone,
baseline and user-approved thresholds. A connector does not add missing network
telemetry: Datadog needs existing metrics for the relevant devices. If the user
reports an active outage, surface the urgent evidence for their incident process
without declaring this Skill an incident commander or repair system.

## Correlate inventory, signals and work

1. Read the selected network/device inventory and health signals. Inventory
   proves a device is recorded, not that it is reachable. Missing telemetry,
   stale last-seen data and a failed query are unknown, not healthy or offline.
   Do not run probes, packet capture or scans as an implicit fallback.
2. Normalize stable organization/network/device IDs and telemetry tags.
   Match conservatively; name similarity is not proof two resources are the
   same. Keep timestamps, units, observation intervals and threshold sources.
   Configuration drift requires both a baseline and actual configuration
   evidence; inventory alone cannot establish it.
3. Search existing Jira issues for the affected device/site and time window.
   Link matching evidence; distinguish an ongoing condition from a new finding.
   A nearby alert and code/configuration change are correlation, not root cause.
4. Build a prioritized inspection queue: resource, observation, baseline,
   severity rationale, evidence, matching issue, suggested owner and next check.
   Never invent thresholds or assign a definitive cause from sparse samples.
5. Prepare a Jira issue/comment and minimal Slack update when useful. Execute
   requested/approved changes only after deduplication. Do not change network
   settings, restart devices, silence monitors or close tickets from this review.
6. If requested, push an approved aggregate to a selected Databox dataset using
   the current schema. Retain ingestion ID and check its status before claiming
   ingestion succeeded. Databox ingestion actions do not read an existing
   dashboard's KPI values. Current Meraki discovery provides inventory/detail
   reads, not configuration writes; re-discover rather than extrapolating.

## Deliverable

A dated health review with inventory coverage, known/unknown signals, findings,
related tickets and next checks. Include data freshness and unmonitored assets.
Report ticket/message/ingestion outcomes independently. Do not call a network
healthy because no matching alerts were returned, or promise continued monitoring
after this one-time run.

## Try it

“Review branch-west network health for the last day. Match Datadog signals with
Meraki inventory and open Jira tickets, highlight gaps, and prepare a team update.
Do not change device settings.”


## License

MIT — see [LICENSE](../LICENSE).
