---
name: perplexity-search
description: Perplexity Sonar search and answer generation through AIsa. Use when the task is specifically to call Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, or Sonar Deep Research for citation-backed web answers, analytical reasoning, or long-form research reports.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🔎
    homepage: https://aisa.one
    requires:
      bins:
      - curl
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---
# Perplexity-Search

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

Use this skill when the user specifically wants Perplexity-powered search answers instead of structured scholar/web retrieval.

This skill covers four AIsa endpoints:
- `/perplexity/sonar`
- `/perplexity/sonar-pro`
- `/perplexity/sonar-reasoning-pro`
- `/perplexity/sonar-deep-research`

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## Requirements

- Set `AISA_API_KEY`
- Use the bundled client at `{baseDir}/scripts/perplexity_search_client.py`

## Model Selection

- Use `sonar` for fast, lightweight answers with citations
- Use `sonar-pro` for stronger synthesis and comparison tasks
- Use `sonar-reasoning-pro` for analytical or multi-step reasoning questions
- Use `sonar-deep-research` for exhaustive reports; expect slower responses and occasional timeouts

## Python Client

```bash
python3 {baseDir}/scripts/perplexity_search_client.py sonar --query "What changed in AI this week?"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-pro --query "Compare coding agents with citations"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-reasoning-pro --query "Analyze whether vertical AI agents can defend against general copilots"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-deep-research --query "Create a deep research report on AI coding agents in 2026"
```

Add a system message when you want a more specific output format:

```bash
python3 {baseDir}/scripts/perplexity_search_client.py sonar-pro \
  --query "Map the top coding agent products" \
  --system "Respond in markdown with an executive summary first."
```

## Curl Examples

### Sonar

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [
      {"role": "user", "content": "What changed in the AI agent ecosystem this week?"}
    ]
  }'
```

### Sonar Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [
      {"role": "user", "content": "Compare the top coding agents and cite the key differences."}
    ]
  }'
```

### Sonar Reasoning Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-reasoning-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-reasoning-pro",
    "messages": [
      {"role": "user", "content": "Analyze whether vertical AI agents can defend against general copilots."}
    ]
  }'
```

### Sonar Deep Research

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-deep-research" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-deep-research",
    "messages": [
      {"role": "user", "content": "Create a deep research report on AI coding agents in 2026."}
    ]
  }'
```

## Timeout Behavior

- `sonar-deep-research` uses a longer timeout and automatic retries in the bundled client
- If it still times out, narrow the query or retry later
- If the user wants a faster answer, fall back to `sonar-pro` or `sonar-reasoning-pro`

## References

- [Sonar](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar)
- [Sonar Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-pro)
- [Sonar Reasoning Pro](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-reasoning-pro)
- [Sonar Deep Research](https://aisa.one/docs/api-reference/perplexity/post_perplexity-sonar-deep-research)
