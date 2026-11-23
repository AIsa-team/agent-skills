---
name: marketing-analytics
description: "Analyze acquisition, funnel conversion, sales outcomes and customer feedback across connected marketing apps with AIsa. Use for weekly marketing performance reviews, channel comparisons and evidence-based growth experiments; not campaign activation or budget changes."
license: MIT
metadata:
  version: "0.1.0"
---

# Marketing Analytics

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

Marketing, growth leads and business owners. Work across the app accounts the user connects through AIsa.

Before reading or changing connected app data, read
[references/connect-runtime.md](references/connect-runtime.md). It defines account
selection, capability discovery, execution and recovery for this workflow.

## App roles

Choose the user's available stack; alternatives in a row are choices, not a
requirement to connect every app. Verify live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| HubSpot | Leads, opportunities, lifecycle definitions and sales outcomes |
| Shopify or Stripe | Orders, payments, refunds and actual revenue evidence |
| Mailchimp; Klaviyo as an alternative | Email delivery, engagement and platform attribution |
| Google Sheets and optional Google Analytics | Existing KPI definitions, targets and site acquisition/conversion |
| Slack; Notion as a report destination | Team context and the reviewed growth brief |
| Intercom or Zendesk (optional) | Customer feedback and recurring conversion objections |

## Define a comparable question

Resolve the business, campaigns/channels, period, comparison period, timezone,
conversion event and metric definitions. A weekly review defaults to the last
seven complete days versus the preceding seven, disclosed in the report.
Honor an existing KPI sheet. Do not change attribution models to make a
channel comparison look complete.

## Analyze the growth path

1. Read the selected channel metrics, site funnel, CRM outcomes and commercial
   results. Fetch relevant feedback separately. Preserve source, currency,
   attribution window, event definition and data freshness for each series.
2. Compare acquisition, engagement, qualified leads, opportunities and payments
   as separate stages. Email opens are not clicks; visits are not people;
   forecast deal value is not revenue. Report provider-attributed revenue
   beside actual orders without adding overlapping claims together.
3. Calculate change with both absolute and relative values. A zero prior
   denominator makes percentage change undefined, not infinite growth. Only
   compute conversion rates when numerator and denominator share a compatible
   population/window. If identity or attribution cannot be joined, show the
   gap instead of deriving a false channel ROI.
4. Identify the largest supported drop-off and compare it with customer themes.
   Separate observed facts, possible explanations and the next validation.
   Use anonymized excerpts; a complaint is evidence of that customer's view,
   not proof of the population's sentiment.
5. Recommend up to three prioritized experiments with hypothesis, change,
   owner, primary metric, baseline, review date and a guardrail. If the data
   supports no change, say so. Budget moves, replies, campaign changes and
   publishing remain separate actions.

## Add customer and market context

Alongside the performance window, use an explicitly stated feedback window
(use 90 days when no feedback window was specified) when feedback is in scope. Cluster observed
customer comments into a few themes with source evidence; keep any public reply
as a separate proposal. If the user supplied or already maintains a competitor
watchlist within this task, compare dated public changes since the last review.
Do not invent competitors or expand a narrow channel report into a new research
project. Where a source is absent or outside scope, omit that leg and name the
coverage limit. Merge the context into the same performance narrative rather
than stapling separate reports together. No campaign, price or public reply is
changed by an analytical finding.

## Deliverable

A concise marketing review: headline, source-labelled metric comparisons,
funnel gaps, customer evidence, uncertainty and prioritized experiments.
Include formulas and inputs for derived metrics. Save/share only as requested;
creating a report does not create recurring monitoring or change ad spend.

## Try it

“Compare last week's email, search and social performance with the previous
week. Connect the traffic to HubSpot outcomes and Shopify sales where possible,
explain the biggest conversion gap, and suggest three experiments.”


## License

MIT — see [LICENSE](../LICENSE).
