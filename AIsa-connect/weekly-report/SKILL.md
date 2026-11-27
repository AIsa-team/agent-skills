---
name: weekly-report
description: "Create a weekly business report from CRM, payment, calendar, email and team updates through AIsa Connect. Use for weekly briefings, pipeline and cash follow-ups, owner decisions and next-week priorities; keep marketing channel analysis in Marketing Analytics."
license: MIT
metadata:
  version: "0.1.0"
---

# Weekly Report

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

Business owners and small-team leads. Work across the app accounts the user connects through AIsa.

Before reading or changing connected app data, read
[references/connect-runtime.md](references/connect-runtime.md). It defines account
selection, capability discovery, execution and recovery for this workflow.
First establish which apps the user actually wants to use for this task. Ask
the scenario question below for any missing choices and wait for the answer;
reuse app choices the user has already explicitly supplied. Only then check
those apps and obtain authorization links for missing or expired connections.
Start task data operations after the required connections and permissions are
verified, following the runtime reference.

## Confirm the apps for this task

If app choices are missing, ask in the user's language, adapting this question
to the requested work and omitting roles already resolved:

“Which apps do you use for the sales/CRM, payments/orders, team updates and
calendar/email you want in this report? Should I return the report here, or use
a document app you name? You can skip categories you do not use.”

## App roles

These are examples of app roles, not a preselected or required stack. Use the
user's named apps and verify their live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| HubSpot; Salesforce or Pipedrive as alternatives | Pipeline, account owners, deal changes and next steps |
| Stripe or Shopify | Payments, orders and exceptions, with their separate accounting definitions |
| Google Calendar and Gmail; Outlook as an alternative | Upcoming commitments and relevant unanswered customer threads |
| Slack; Teams or Feishu as alternatives | Team blockers and commitments in the selected channels |
| Notion; a supported document destination as an alternative | Prior decisions and the report destination |
| Linear, Asana, ClickUp, Monday or Jira (optional) | Delivery milestones and overdue commitments |

## Start from the week, not a pile of dashboards

Resolve the business, reporting period, comparison period, timezone and audience.
Use the last completed week plus the upcoming week when the owner simply asks
for a weekly briefing, and state those dates. Reuse an existing report and its
metric definitions when provided; do not interview the user about new KPIs.

## Build the business picture

1. Read changes in the selected CRM, payment/order exceptions, relevant team
   threads, calendar commitments and prior decisions from the apps the user
   selected. If a required source is unavailable, wait for its connection or the
   user's explicit agreement to a reduced scope; disclose any agreed omissions.
2. Separate pipeline value from won revenue, invoiced amounts, cash received,
   refunds and order totals. Keep currency, period and source definition beside
   each metric. Never add a Stripe payment to its matching Shopify order as
   another sale. Reconcile on transaction/order IDs where available.
3. Compare like-for-like periods. Explain movements with linked records,
   then connect the movement to this week's commitments: a slipping deal,
   overdue invoice, missed handoff or meeting that needs preparation.
4. Rank what needs the owner. Close with one main priority and its evidence;
   additional actions should have an owner, due date and status, not generic
   productivity advice. Do not invent a priority in a genuinely quiet week.
5. Deliver one coherent report. Save it or share a leadership/team summary
   only within the user's request, respecting the audience's access to financial
   and customer details. Reporting an overdue payment does not authorize a
   payment reminder or financial transaction.

## Combine the business snapshot, KPIs and commitments

Collect three complementary inputs, then
merge their findings: a business snapshot, already-defined weekly KPI reports,
and the week ahead. If the user has saved weekly reports in the chosen document
or spreadsheet destination, read those and fold their findings into the matching
business section. If no report is defined, skip that input without creating a
report-building interview. Calendar/email commitments supply the forward view;
reuse the business snapshot's numbers rather than recomputing them in this leg.
Deliver in the user's existing format preference. Saving or posting still follows
the chosen destination and authorization. Use the user's existing preferences
without creating new settings files or changing their workspace.

## Deliverable

Produce a dated report containing: the week's headline; a compact metric table
with current value, comparison, definition and source; material risks and open
commitments; the upcoming week's shape; one main priority; and coverage gaps.
Use “not queried” rather than zero for missing sources. Include the shared
action ledger when saving or sharing; a chat draft alone is not a saved report.

## Try it

“Prepare last week's business report from HubSpot, Stripe, Slack and my calendar.
Highlight pipeline changes, payment follow-ups and next week's priorities.
Keep the sources and give me the report before sharing it.”


## License

MIT — see [LICENSE](../LICENSE).
