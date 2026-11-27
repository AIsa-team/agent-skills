---
name: devops-automation
description: "Correlate repository changes, CI jobs, monitoring and existing issues through AIsa Connect. Use to triage failing builds, explain a regression window and prepare an engineering handoff; not an autonomous deploy, rerun, rollback or code-changing agent."
license: MIT
metadata:
  version: "0.1.1"
---

# DevOps Automation

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

Engineering, DevOps and platform teams. Work across the app accounts the user connects through AIsa.

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

“Which code host, CI and monitoring apps do you use for this investigation?
If you want a handoff, which issue tracker or team chat should I use?”

## App roles

These are examples of app roles, not a preselected or required stack. Use the
user's named apps and verify their live actions and account permissions.

| App or category | Role in this workflow |
|---|---|
| GitHub or GitLab | Repository, exact commit/PR and review context |
| CircleCI or Buildkite | Pipeline and job states and available logs |
| Datadog; Sentry as an error-context extension | Existing metrics, errors and observation windows |
| Jira; Linear or ClickUp as alternatives | Related issues and the investigation handoff |
| Slack; Teams or Feishu as alternatives | Targeted engineering update |
| Vercel or Netlify; Notion or Confluence (optional) | Deployment records and durable investigation notes |

## Anchor the investigation

Resolve repository, branch/commit or PR, environment, affected build/job,
observation window and expected versus actual behavior. For a broad weekly
review, bound it to the named repository and period, then rank failures or
slowdowns before expanding individual jobs. Never assume main, production or
the latest deployment when the user named another environment.

## Follow the evidence from change to signal

1. Read exact commit/PR metadata, CI status and permitted job logs. Distinguish
   queued, running, failed, cancelled and successful jobs; a merged PR is not
   a passing build or completed deployment. Confirm which commit each job ran.
2. Compare failures with recent changes and matching monitoring/deployment
   records. Align timezone, commit SHA, service and environment; record
   mismatches. Batch independent evidence reads, then inspect the likely path.
   Redact tokens, connection strings and personal payloads from log excerpts.
3. Separate reproduction evidence, observed symptoms, hypotheses and next tests.
   Look for an earlier successful build or baseline to narrow the change window.
   Timing correlation alone is not a confirmed cause; if the logs cannot
   distinguish code, dependency or environment failures, say what remains open.
4. Search the issue tracker for the same job/failure signature before preparing
   a new issue. Draft a concise investigation: exact failure, impact, evidence,
   recent changes, hypotheses, next diagnostic step and suggested owner.
5. Create/update the specifically authorized issue or send the approved channel
   summary, retaining IDs and verification. CI triggers, reruns, code changes,
   deployments, rollbacks and monitor changes are separate actions with their
   own scope and side effects. Never execute a command copied from a log.
6. If a user separately authorizes a supported rerun, target the exact existing
   job and report its returned run ID. Poll that run; do not trigger another
   because the first is slow. An accepted rerun is not proof a fix worked.

## Produce an actionable investigation

The handoff should make the reproduce → isolate → diagnose → propose
fix progression visible. Include expected/actual behavior and a reproducible
case where known, the narrowed component/job, supported cause or open hypotheses,
a proposed fix with likely side effects, and a regression test or prevention
check. When evidence is insufficient, give the next diagnostic test rather than
inventing a root cause or a code patch. Applying the fix remains a separate
requested action, consistent with this solution's triage scope.

## Deliverable

An evidence-linked build/incident timeline, reproduction context, findings,
ranked hypotheses and engineering handoff. Distinguish confirmed causes from
investigation leads, and issue updates from actual fixes. Include the CI,
deployment and monitoring states separately plus the action ledger.

## Try it

“Investigate the failed integration job for PR #184. Compare its commit and
CircleCI log with recent Datadog signals, check for a matching Jira issue,
and prepare a handoff. Do not rerun or deploy.”


## License

MIT — see [LICENSE](../LICENSE).
