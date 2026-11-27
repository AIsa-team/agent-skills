---
name: meeting-notes
description: "Turn a customer call transcript into meeting notes, decisions, action owners, a follow-up email and proposed CRM updates through AIsa Connect. Use after discovery, demo or onboarding calls; not for recording meetings or a general CRM hygiene audit."
license: MIT
metadata:
  version: "0.1.1"
---

# Meeting Notes

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

Sales, customer-facing teams and business owners. Work across the app accounts the user connects through AIsa.

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

“Where are the meeting transcript or notes? If you want customer follow-up,
CRM updates or assigned tasks, which email, CRM and task apps do you use for
those? You can also provide the transcript here.”

## App roles

These are examples of app roles, not a preselected or required stack. Use the
user's named apps and verify their live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| Fireflies; Gong, Otter.ai or an existing transcript document as alternatives | Meeting transcript and speaker/timestamp evidence |
| HubSpot; Salesforce or Pipedrive as alternatives | Resolve the customer, opportunity and live field definitions |
| Gmail or Outlook | Relevant thread and an approved draft/reply destination |
| Slack; Teams or Feishu as alternatives | Internal handoff to the selected channel |
| Notion, Confluence or Google Drive (optional) | Durable decision record |
| Linear, Asana, ClickUp, Monday or Jira (optional) | Confirmed action items in one selected task system |

## Resolve the actual meeting

Use the named call, transcript ID or user-provided notes. For “latest call”,
filter by the user's participation, customer and completed meeting time; ask
if multiple calls remain plausible. Calendar titles and autogenerated summaries
alone are not evidence of what was said. If no transcript exists, accept notes
and label their coverage rather than fabricating a recording.

## Turn the call into the next steps

1. Read the transcript, matched customer/opportunity and relevant existing
   thread. Resolve contacts using identifiers and participants; do not attach
   the notes to a same-name account or assume an opportunity when several exist.
2. Separate decisions, explicit commitments, requests, objections, unresolved
   questions and tentative ideas. Give each action its stated owner, date and
   transcript citation. Leave unstated owners/dates unassigned; recommendations
   belong in a separate proposal, not in the meeting's factual record.
3. Draft a concise customer email: agreed outcome, our commitments, their next
   steps and unanswered questions. Use the verified thread/recipient and sender
   identity. Creating a mailbox draft requires a supported authorized action;
   otherwise return copy-ready text. A draft is not a sent message.
4. Prepare an internal recap and field-level CRM change set: record ID,
   human-readable field, current value, proposed value, reason and source.
   Check the live field schema. Do not infer a deal stage, amount or close date
   from enthusiasm or a tentative customer comment.
5. Apply only requested/approved destinations and changes. Link task records
   to the transcript and customer; deduplicate by meeting ID and action key.
   Return the actual email, note, task and CRM outcomes independently.

## Prepare the customer and internal handoff

Normalize the meeting source, date/time, internal/external participants, record
link and transcript or cited-answer evidence before extracting anything. A tool
that returns cited answers rather than transcript text can support only those
answers; an empty answer means unavailable evidence, not “not discussed”.
Keep the customer email concise (normally under 150 words), in the supplied
voice, with each side's commitments and the next meeting. Open the complete
existing email thread before describing its history and preserve its thread ID
when the current draft action supports it. Otherwise provide copy-ready text and
state the threading limitation. Never invent an attachment that is not available.
The internal recap includes account, known CRM stage/value, headline, risks and
next steps split between our team and the customer. CRM figures must come from
the CRM, not an assumption in the transcript.

## Deliverable

One meeting pack: meeting identity and source; short summary; decisions;
actions with owner/date/evidence; open questions; customer email; internal
recap; and CRM before/after proposals. Mark each destination as draft,
completed, pending or unavailable. Do not count draft tasks as created tasks.

## Try it

“Summarize my latest Northwind customer call. Extract decisions and commitments,
draft the follow-up email, and show the HubSpot updates you recommend.
Let me review the changes before applying them.”


## License

MIT — see [LICENSE](../LICENSE).
