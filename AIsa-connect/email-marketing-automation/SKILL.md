---
name: email-marketing-automation
description: "Design audience segments, lifecycle email sequences, entry/exit rules and reviewable platform drafts through AIsa Connect. Use for welcome, nurture or re-engagement automation across Mailchimp, Klaviyo, CRM and commerce data; not cold outreach or unapproved campaign activation."
license: MIT
metadata:
  version: "0.1.0"
---

# Email Marketing Automation

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

Lifecycle, email, e-commerce and growth marketing teams. Work across the app accounts the user connects through AIsa.

Before reading or changing connected app data, read
[references/connect-runtime.md](references/connect-runtime.md). It defines account
selection, capability discovery, execution and recovery for this workflow.
If a required app account is not connected or its authorization has expired,
follow that reference to show the user a clickable authorization link and ask
them to click it. Resume dependent operations only after verifying the connection
is active for the intended account and has the required permissions.

## App roles

Choose the user's available stack; alternatives in a row are choices, not a
requirement to connect every app. Verify live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| Mailchimp or Klaviyo | One selected audience and supported draft/flow actions |
| HubSpot | Lifecycle stage, CRM context and conversion events |
| Shopify | Order/product context and purchase-based exits |
| Google Sheets | Review matrix and sequence export |
| ActiveCampaign (optional) | Only the contact/list/field operations actually exposed |
| Google Analytics; Slack, Teams or Feishu (optional) | Conversion review and internal approval handoff |

## Start with the lifecycle outcome

Resolve sequence type, goal, audience/list, brand voice, trigger, timezone and
destination platform. Use existing consent and suppression records; being in a
CRM, completing a purchase or having a public email address is not marketing
opt-in. If consent evidence is missing, draft content without creating enrollment.

## Design an executable journey

1. Read only the relevant audience attributes, subscription state, CRM stage,
   product information and existing flows. Select one platform of record.
   Do not move personal subscriber data to another system just to make joins
   convenient; use aggregate results when individual details are unnecessary.
2. Define entry criteria, exclusions, goal/exit event, re-entry interval,
   frequency cap and suppression precedence. Unsubscribe, bounce/suppression
   and goal completion override a planned next email. Avoid overlapping flows.
3. Draft the sequence architecture and each email: subject options, preheader,
   purpose, complete body, one primary CTA, destination, timing and conditions.
   Use observed product claims and approved offers. Personalization needs a
   fallback; never leave a broken token as customer-ready copy.
4. Map the design to live platform capability. Inspect separate actions for
   saving content, building a flow, enrollment, scheduling and sending.
   A generic campaign draft is not a running automation. ActiveCampaign contact
   actions do not imply flow creation; a missing capability becomes a setup
   checklist or export, not an invented API call.
5. Present the exact audience criteria, sender identity, copy, timing,
   suppression and downstream effects. Save supported drafts or configure a
   disabled flow only within the user's request. Activation/enrollment/send
   requires specific authorization and current connection scopes.
6. Recheck live suppression and goal state before any authorized enrollment
   or send. Reuse campaign/flow IDs to prevent duplicate sequences. Validate
   links and mapping; an optional test email needs an explicitly chosen test
   recipient. Report it separately from production delivery.

## Design the message progression and tests

Use the requested lifecycle as a narrative progression: a welcome sequence
should move from first value toward activation; nurture should connect useful
education, evidence and a relevant next step; re-engagement should offer a reason
to return and respect suppression. Adapt length and delays to the user's actual
request instead of forcing a fixed email count. For each email include
two or three subject options and complementary preview text where useful.
Add two or three suggested A/B tests with one variable, audience split, primary
metric and review window. A test plan is a proposal, not an activated experiment.
Use observed account baselines or clearly labelled targets. Do not present
generic benchmark ranges as measured results for this audience.

## Deliverable

Sequence overview, full email drafts, text flow diagram, branching/exit rules,
capability checklist and platform draft IDs. Include measurement definitions:
delivered, clicks, conversion, unsubscribe and bounce. Baselines come from the
account's observed data; do not fabricate benchmark promises or attribute all
orders to email. State clearly what remains disabled, manual or unconfigured.

## Try it

“Design a three-email welcome sequence for consented new subscribers. Use
HubSpot and Shopify context, exclude existing customers, and exit after a first
purchase. Prepare Mailchimp drafts for review without enrolling or sending.”


## License

MIT — see [LICENSE](../LICENSE).
