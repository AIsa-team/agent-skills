---
name: content-calendar
description: "Plan and maintain a multi-channel content calendar from real product information, brand assets and past content through AIsa Connect. Use for weekly editorial plans, repurposing, channel briefs and draft copy; not lifecycle email enrollment or automatic publishing."
license: MIT
metadata:
  version: "0.1.1"
---

# Content Calendar

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

Content, social media, brand and e-commerce marketing teams. Work across the app accounts the user connects through AIsa.

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

“Which apps hold your product or brand information, approved assets and
existing content calendar? Where should I prepare drafts and track reviews?
You can provide source material here instead of connecting an app for it.”

## App roles

These are examples of app roles, not a preselected or required stack. Use the
user's named apps and verify their live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| Shopify | Verified product descriptions, images, prices and availability |
| Canva; Figma as an asset alternative | Existing designs and supported creation/export actions |
| Notion; Trello or a project tool as alternatives | One persistent content calendar and review status |
| HubSpot or Mailchimp | Supported content staging or email draft destinations |
| Google Drive or Google Docs (optional) | Product briefs, approved examples and reusable assets |
| Slack, Teams or Feishu; Asana, ClickUp or Monday (optional) | Editorial feedback, owners and review work |

## Continue the calendar already in use

Resolve the brand/product, audience, channels, date range, timezone and calendar
destination. Read existing entries, approvals and published items before adding
new ones. For a simple weekly request, propose three to five entries for the
next week rather than assuming a daily cadence. Learn voice from approved
examples; if absent use a neutral tone and say the voice still needs review.

## Build usable content, not empty slots

1. Read actual product facts, approved claims, imagery, campaign dates and
   reusable assets. Keep each source reference. Do not invent prices, stock,
   discounts, customer quotes, endorsements or product capabilities.
2. Propose the editorial mix: product education, proof with permission,
   practical tips and behind-the-scenes where relevant. Each row needs an
   audience need, angle, channel, format, source asset and intended outcome.
3. Draft a channel-specific hook, core copy and CTA. Repurpose an approved
   asset instead of treating every placement as a new creative project.
   For visual work, specify source images, design dimensions and text slots.
   Inspect current Canva/Figma actions before promising template autofill,
   resizing or export. Missing functionality becomes a creative brief.
4. If assets are actually generated/exported, budget the exact discovered
   operations; poll existing jobs, keep returned design/asset IDs and inspect
   the result for wrong product, placeholder text or missing image slots.
   “Job succeeded” alone is not editorial approval.
5. Present the calendar and copy for review, then save or stage the authorized
   entries in the selected destination. Match existing rows by calendar ID,
   date, channel and content key to avoid duplicates. Recheck dates before
   staging: a date that passed during review must not be silently rescheduled.

## Review the calendar, assets and copy

Before asset generation, present the calendar and each row's route: visual
creative or text-only. Email rows in this workflow remain copy-only; do not send
them through Canva. When generation is requested, agree on the calendar first,
then inventory every required image/text slot against actual source assets.
Resolve missing slots by reusing an approved image, requesting an asset or using
a simpler design, not by silently inserting generic imagery. Budget the discovered
operations, present one selected design per row and obtain the requested design
and copy review before staging. Apply already-given approvals without asking the
same question again. Preserve the selected calendar's destination ID so the next
run extends the same home.

## Deliverable

An editable calendar with date/time/timezone, channel, theme, format, hook,
copy, CTA, asset reference, owner, review status and destination ID/link.
Use explicit states such as draft, approved, staged and published only when
verified. HubSpot plan restrictions or missing staging actions fall back to
a CSV or paste-ready rows. Saving to Notion is not scheduling publication.
Public posting requires its own requested target, content and action.

## Try it

“Build next week's content calendar for this Shopify product. Reuse our approved
Canva assets, draft Instagram and LinkedIn copy in our brand voice, and show the
calendar before saving it to Notion. Do not publish anything.”


## License

MIT — see [LICENSE](../LICENSE).
