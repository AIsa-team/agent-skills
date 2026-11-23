---
name: crm-automation
description: "Audit CRM data quality and prepare evidence-backed fixes with AIsa Connect. Use for duplicate contacts, missing owners or fields, stale close dates and record reconciliation in HubSpot, Salesforce or Pipedrive; not another meeting summary or automatic deal-stage advancement."
license: MIT
metadata:
  version: "0.1.0"
---

# CRM Automation

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

Sales, Sales Ops and RevOps. Work across the app accounts the user connects through AIsa.

Before reading or changing connected app data, read
[references/connect-runtime.md](references/connect-runtime.md). It defines account
selection, capability discovery, execution and recovery for this workflow.

## App roles

Choose the user's available stack; alternatives in a row are choices, not a
requirement to connect every app. Verify live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| HubSpot, Salesforce or Pipedrive | One selected CRM of record, its object schema and associations |
| Google Sheets | Import comparison and reviewable correction exports |
| Gmail or Outlook | Relevant activity evidence, not authority to change CRM fields |
| Slack; Teams or Feishu as alternatives | Owner and exception coordination |
| Apollo or Clay (optional) | Explicitly scoped, verified enrichment evidence |
| Typeform or another connected lead source (optional) | Compare incoming contact data with existing records |

## Define the audit boundary

Resolve the CRM tenant, object types, segment/pipeline, date window, fields of
interest and stale-record threshold. Read the live property schema, picklists,
required fields and associations. A CRM audit is not permission to sweep all
tenants or create a new CRM. If an account has no records, report that coverage.

## Find, explain and safely repair

1. Read the scoped records and permitted supporting evidence. Keep record IDs,
   current values, modification timestamps and source links. Follow pagination
   or mark the audit partial; do not claim “all contacts” after one search page.
2. Identify duplicate candidates using exact normalized email/IDs where
   appropriate, plus company and history. Similar names or domains alone are
   not merge decisions. Shared inboxes and one person at multiple companies
   require review. Keep conflicts and uncertain matches separate.
3. Flag missing required fields, invalid owner references, absent associations,
   stale close dates and missing next steps. “No activity returned” is distinct
   from “no activity exists”. Do not invent an owner, consent status or deadline.
4. Build a correction queue: record ID/link, issue type, old value, proposed
   value, evidence, confidence and downstream effect. Use enrichment only when
   requested and bounded; third-party guesses are not confirmed customer facts.
   Keep stage, forecast amount and consent changes explicit.
5. Apply the concrete changes the user approves. Re-read each record to detect
   intervening edits. Use the discovered update/merge action and field schema.
   Deduplication is a proposal until merge support and consequences are checked;
   do not emulate merge by deleting and recreating records.
6. Verify changed records and retain before/after values and IDs for recovery.
   Keep failures separate from untouched proposals. Resume from that queue,
   not by applying the original sheet to everything again.

## Audit the key data-quality issues

Check duplicate contacts/companies, missing required
fields, contacts without a company association, open deals past their close date
and deals lacking a next action. Include these where the selected CRM schema
supports them; record “not checked” for unsupported categories. The review queue
must show current and proposed values side by side with evidence. This solution
does not start activity logging, outreach or new-CRM creation merely
because the audit found an empty field or a quiet deal.

## Deliverable

Return coverage counts; findings by category; a sortable correction queue;
and executed-versus-proposed changes. Export CSV when the CRM or Sheets
connection cannot write. A data-quality report must not send outreach,
create opportunities or enroll contacts into marketing sequences.

## Try it

“Audit this HubSpot pipeline for duplicate contacts, missing owners and close
dates in the past. Show evidence and before/after values, keep uncertain matches
separate, and let me approve any updates.”


## License

MIT — see [LICENSE](../LICENSE).
