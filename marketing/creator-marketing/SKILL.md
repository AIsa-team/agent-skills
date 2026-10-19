---
name: creator-marketing
description: Plan creator, influencer and ambassador partnerships for a brand or agency client. Find and assess candidates, structure compensation and usage rights, draft outreach and creative briefs, and measure qualified outcomes. Use for creator sourcing, gifting, sponsorships and UGC programs; connected-account diagnosis and campaign execution use their specialist workflows.
compatibility: "Requires Python 3.10+ and the AISA_API_KEY environment variable."
metadata:
  author: aisa.one
  version: "0.0.2"
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# Creator Marketing

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify

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

Help the user choose creators and design a feasible partnership pilot. Use information from the current conversation and materials the user explicitly provides. Clarify only missing details that affect the plan: product, audience and market, objective, channels, budget, timing, team capacity and constraints. Do not assume a predefined brand file or workspace layout.

## Choose the partnership model

Select the model by the job: a sponsored placement borrows distribution; commissioned UGC buys content and may not include posting; gifting has no guaranteed post; an affiliate deal needs commission/tracking terms; an ambassador program adds recurring responsibilities and relationship management. A small aligned creator is not automatically cheaper per sale than a larger one. Avoid universal tier, engagement-rate or compensation benchmarks. Treat actual quotes and comparable sourced evidence as inputs, not guarantees.

For detailed deal, brief and measurement guidance read [partnership-playbook.md](references/partnership-playbook.md). For a recurring high-volume UGC network also read [ugc-program.md](references/ugc-program.md); do not default every campaign to a creator network.

## Research and shortlist

Proactively use external evidence when it can improve candidate choice, creative fit, deal assumptions or current practices. Do not wait for a specific request to search. Skip external research when explicitly prohibited or supplied evidence already answers the decision. A planning-only request does not require finding named creators.

Before fetching, read [aisa-contract.md](references/aisa-contract.md) and [capabilities.md](references/capabilities.md). Use only the bundled helper through Router schema → quote → use, with fixed tools. Do not use direct vendors, arbitrary browser/MCP research or paid nested workflows. Reuse supplied account findings. Audience-demographic or fraud checks require evidence from an actually available tool; do not assume one is installed. This skill adds partnership design. No Similarweb is needed for this workflow.

For YouTube/TikTok discovery use similar creators by content direction, seed or both. Start with 3–5 matches (helper maximum 10), apply the requested market/language filters in one query and state remaining fit gaps. Do not create broader unfiltered or alternative queries unless the user asks for a comparison. For YouTube content evidence use a focused YouTube search. Instagram profile/posts can assess known handles; similar creators does not support Instagram. General search/extract can verify case studies, public evidence or current official disclosure guidance. Look up a missing business email only for a selected candidate when contact preparation is part of the request; reuse an email already returned. No bulk enrichment by default.

Never label similarityScore as audience overlap, real follower quality, purchase intent or expected ROI. Creator region/language are not audience demographics. Distinguish provider-returned facts, source dates, content-based hypotheses, and media-kit verification needed. Named recommendations need actual source/profile links. Inspect evidence relevant to the brief rather than claiming a full audit from one page; sparse/private/empty results are gaps, not proof of fraud. Do not infer sensitive personal traits of creators or audiences.

For a shortlist, provide candidate/platform/profile, observed category and content fit, relevant returned metrics with time/denominator if known, uncertainties/conflicts, and why to advance or reject. Use unknown for unreturned fields and price TBD for missing quotes. Do not fabricate candidates to fill the requested count. Keep returned contact details scoped to the user's legitimate partnership task; lookup is not permission to send outreach.

## Produce a feasible partnership pilot

Recommend a first pilot or rank alternatives. Specify creators or selection criteria, deliverables, posting vs content-only scope, schedule, cash fees, product cost/shipping, commissions, usage rights, revisions, production and coordination workload. Sum combined-plan costs and peak-week hours; include capped incentive liability rather than excluding it from budget. Preserve the user's cost categories exactly: a product-plus-shipping amount already includes both, so do not relabel it as shipping or assume free inventory. Mark unquoted creator fees as proposed allocations, not agreed rates. If capacity, quotes or margins are unknown, show dependencies and provisional allocations rather than predicted sales.

Draft personalized outreach only when useful, grounded in observed content; do not send it without authorization. A creator brief includes audience/problem, 2–3 substantiated messages, format, CTA, creative freedom, claims to avoid, disclosure requirements to verify, delivery/review dates and agreed usage boundaries. Never imply paid reuse, account access, exclusivity or AI likeness rights are automatically included. Content usage rights alone do not fund or launch paid distribution. When media spend is unallocated, keep the current pilot organic/content-only and describe paid amplification as a separately budgeted, authorized next step. Do not say the pilot tests paid performance merely because the quote includes ad rights.

Explain compensation alternatives and tradeoffs. Ask for a quote with separately priced deliverables, rights and exclusivity; do not prescribe one negotiation anchor universally. Draft a commercial checklist, not a purported legally approved contract. Before stating jurisdiction-specific legal or platform requirements, verify current official sources through the research tools, or identify the specific rule as pending verification. Distinguish source requirements from recommended best practices; do not turn wording such as “likely to notice” into a mandatory legal rule. Match the disclosure to the actual compensation: free-product wording alone is incomplete when cash is also paid. Transparently disclose material brand relationships and avoid fabricated personal experience or claims.

Measure the agreed objective: use creator/placement links and codes, qualified lead definitions and an attribution window, plus surveys when appropriate. Deduplicate code/link conversions, separate attributed revenue from incremental lift, and include total costs and margin when calculating profitability. Paid reuse metrics do not by themselves prove the creator's organic audience converts. If sample size is small, use learning criteria; no unsupported industry averages or sales forecasts.

Deliver a concise shortlist/pilot/brief matching the actual request, with the next action, owner, evidence and unresolved dependencies. Explain how research changed or supplemented the plan; no useful sources is an acceptable finding.

## Runtime and handoff


This skill researches and drafts plans; it does not send messages, sign agreements, transfer money, publish posts or change ad accounts. If the user requests execution, confirm that an appropriate tool is available and that their authorization covers the action. Otherwise, provide the prepared material and next steps.


On `budget_approval_required`, explain the quote and remaining allowance for the requested single scope, then wait for actual authorization before increasing the allowance. Do not recommend arbitrary multiples of the estimate as a new budget. Use always obtains a fresh quote; saved quotes are observations, not execution tokens. Do not switch providers to evade this decision.

## Stateless cost control

Read references/aisa-contract.md before research. Default task data budget is $2 unless the user specifies otherwise. Before Use, fetch a fresh quote and compare it with the remaining budget; exceeding that budget requires user authorization. Each attempted Use consumes its quoted amount from the task budget, even when it fails. Pass the returned remaining_budget_usd_micros on subsequent calls. Actual fees are informational: use a valid header, otherwise the item fee, otherwise null. Missing or differing fees never hide valid results or require billing reconciliation. Estimates may settle higher; quoted budget is not a hard billing cap. No automatic network retries or accounting files. Report concrete request errors; never ask the user to check invoices or billing dashboards.

## Authentication and invocation

Set `AISA_API_KEY` in the process environment; never paste it into a prompt or commit it. If missing, ask the user to configure it. Run commands from this skill directory or resolve `scripts/request.py` against the loaded skill root. The existing direct-API skills use api.aisa.one; this skill intentionally uses the Router at tools.aisa.one for schema, quote and tool execution. It needs Python 3.10+ only.

When the helper returns `budget_approval_required`, end external research for this turn and present that quote. Do not substitute a cheaper capability, provider or reduced input unless the user authorizes a changed scope. A free quote error may be corrected before use. Explain concrete execution failures without creating a billing-reconciliation task.
