---
name: aisa
description: "Discover and invoke published AIsa tools with unified MCP or the AIsa CLI (search, schema, quote, call). Use when the user wants AIsa tools or sign-in, or needs current web, company, or social data AIsa tools can fetch—even if they do not name AIsa. Do not use for OpenClaw Chinese model provider setup (aisa-provider), installing other catalog skills, or work that does not need live AIsa data."
license: MIT
metadata:
  version: "1.0.1"
---

# AIsa

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

If you are already reading this skill, continue the current task. Do not reinstall it, reread setup docs, or relogin a working connection.

If the user named another tool, or a dedicated local tool already covers the job, do not force AIsa.

First-time install and connect: https://aisa.one/docs/agent-quickstart.md

## Reuse

Reuse a working official `aisa` skill, `@aisa-one/cli` **0.5.0 or later**, stored CLI credentials, or a unified MCP session. An explicit user transport choice or a still-authorized connection wins. Otherwise default to MCP at `https://tools.aisa.one/mcp` wherever this client can add the connector — user-local or cloud, with or without a terminal. Use the CLI only when this client has no MCP mechanism, for non-interactive automation with an existing key, or by explicit user choice; Node.js must already be installed, and do not install Node, build a private runtime, or redirect `HOME` to reach the CLI — use MCP or ask the user instead. `AISA_API_KEY` overrides the stored key; if they conflict, explain the sources and leave custom setup alone. Never print credentials. `aisa whoami` is local only. Search and schema may be anonymous — they are not auth proof.

## Sign-in

Prove CLI auth with `aisa balance`; an MCP session is proven by completed OAuth plus the four tools instead. Before replying to a sign-in message or writing to its terminal, read `aisa login --help`. Follow it to interpret the CLI prompt and relay only the requested authorization result through the existing process. No credit → top up, not “missing key”.

## Workflow

`search` → `schema` when `has_full_schema` is false → `quote` → `call` inside authorized scope and spend. `quote` and `call` share the saved credentials and the same `calls` JSON shape. Take tool IDs and arguments from search/schema. Do not invent IDs or prices. Runtime help, schema, and quote are authoritative. `--input` is inline JSON:

```sh
aisa search --input '{"query":"<user goal>"}' --json
aisa quote --input '{"calls":[{"call_id":"c1","tool":"<name from search>","arguments":{}}]}' --json
```

Quote does not execute and is not approval to execute. A missing, failed, or partial quote is not free and is not a full-batch total or cap. Estimated cost is not a cap. Setup is not paid execution permission. Reuse a still-valid explicit authorization; do not invent confirmation loops for search, schema, or install. Re-quote if tools, arguments, or scope change. Do not silently retry or expand the batch.

## MCP

Use native remote Streamable HTTP MCP with OAuth at `https://tools.aisa.one/mcp`. No CLI, npm, npx, or Skill installation is required; already-installed guidance may be used. The client owns browser sign-in and tokens. Do not treat domain MCP or `aisa connect`’s default web-search server as this router. Discovery or a 401 is not a protected call. If a connector cannot be added, give the user that endpoint and one next action; do not claim connected.

| MCP tool | CLI command |
| --- | --- |
| `AISA_SEARCH_TOOL` | `aisa search` |
| `AISA_BATCH_GET_SCHEMA` | `aisa schema` |
| `AISA_BATCH_QUOTE` | `aisa quote` |
| `AISA_BATCH_USE` | `aisa call` |

## License

MIT — see [LICENSE](LICENSE).
