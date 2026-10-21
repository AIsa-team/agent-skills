---
name: kol-creator-discovery
description: Use this skill when a user needs KOL or influencer research, creator email lookup, similar-creator discovery, outreach-list building, influencer prospecting, or a contact table from TikTok, Instagram, or YouTube profile URLs. It uses AIsa's WaveInflu APIs to find verified creator emails, match similar YouTube or TikTok creators, enrich each recommended profile with contact emails, and return an outreach-ready Markdown table without inventing missing data.
license: MIT
compatibility: "Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, curl, and AISA_API_KEY."
metadata:
  version: "1.0.1"
  short-description: AIsa-powered KOL email and creator discovery
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
        - curl
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

# KOL Creator Discovery

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

Build a contact-ready creator list from one social profile. Use AIsa WaveInflu to look up the seed creator's email, find similar creators, enrich every recommended profile with its own email lookup, and return one evidence-based table.

## Requirements

Set an AIsa API key:

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit API keys. If the key is missing, ask the user to set `AISA_API_KEY`.

## Compatibility

Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes, and other runtimes that support skill folders.

Requires Python 3, curl, and `AISA_API_KEY`. Get a key at `https://aisa.one`.

## Quick Start

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research \
  "https://www.youtube.com/@mkbhd" \
  --limit 10 \
  --out kol-report.md \
  --json-out kol-report.json
```

With explicit content direction and audience filters:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research \
  "https://www.tiktok.com/@creator" \
  --platform tiktok \
  --content-direction "consumer AI apps and productivity tools" \
  --regions US,GB \
  --languages en \
  --min-followers 10000 \
  --max-followers 500000 \
  --limit 15 \
  --out kol-report.md
```

## Core Workflow

### 1. Validate the brief

Collect or infer:

- One seed TikTok, Instagram, or YouTube creator profile URL
- Target discovery platform: `youtube` or `tiktok`
- Number of recommendations; default to 10
- Optional content direction, regions, languages, follower range, and average-view range

Infer the target platform from a YouTube or TikTok seed URL. If the seed is Instagram, ask for both the target platform and a content-direction description because WaveInflu similarity matching does not accept Instagram seed profiles.

Do not call an API until the input is a creator profile URL. Do not use individual post or video URLs as seeds.

### 2. Look up the seed creator's contact data

Call `POST /apis/v1/waveinflu/email-lookup` with the submitted profile URL. Preserve the returned platform, username, normalized profile link, region, emails, contacts, and quota metadata.

Treat returned email values as API-sourced contact data. Never infer an email pattern or manufacture a missing address.

### 3. Find similar creators

Call `POST /apis/v1/waveinflu/similar` with:

- `platform`: `youtube` or `tiktok`
- `seedProfileUrl`: include only for YouTube or TikTok seeds
- `contentDirection`: include when supplied; require it for Instagram seeds
- `limit`: default 10, maximum 100
- `filters`: include only the filters requested by the user

The API returns creators sorted by `similarityScore`. Preserve that order after removing duplicates and the seed creator.

### 4. Enrich every recommendation with an email lookup

For each returned creator profile URL, call `POST /apis/v1/waveinflu/email-lookup`. Use the primary `email` when present; otherwise use the first unique value in `emails`. If no email is returned, write `Not found` rather than guessing.

Default to 10 email enrichments. Before enriching more than 25 creators, tell the user how many email-lookup calls will be made and confirm the scope because each lookup can consume quota.

Continue when one creator lookup fails. Record `Lookup failed` for that row and finish the remaining list.

### 5. Normalize and rank

- Deduplicate by normalized profile URL, platform user ID, or channel ID.
- Keep WaveInflu's descending similarity order.
- Preserve exact follower and average-view counts in JSON.
- Use compact display values such as `125K` only in Markdown.
- Mark absent region, language, metrics, or emails as `—` or `Not found`.
- Separate API facts from any operator recommendation.

### 6. Return the deliverable

Use `references/report-template.md`. The main output must include:

- Seed creator and resolved discovery scope
- Number of similar creators returned and email coverage
- One Markdown table containing the seed and all similar creators
- Role, rank, creator, platform, profile URL, similarity score, followers, average views, region/language, email, and lookup status
- Quota or API limitations that materially affect completeness

Do not expose raw API payloads unless requested. Do not initiate outreach, send email, or upload the list to another system without separate user authorization.

## Helper Script

Run the complete workflow:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py research PROFILE_URL \
  --platform youtube \
  --content-direction "AI productivity creators" \
  --limit 10 \
  --out report.md \
  --json-out report.json
```

Run only email lookup:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py lookup \
  "https://www.instagram.com/onkimia/"
```

Run only similar-creator discovery:

```bash
python3 {baseDir}/scripts/kol_creator_discovery.py similar \
  --platform youtube \
  --seed-profile-url "https://www.youtube.com/@mkbhd" \
  --limit 10
```

Read `references/api-reference.md` before changing payload fields or interpreting response fields.

## Quality Rules

- Use only `https://api.aisa.one/apis/v1/waveinflu/...` endpoints.
- Never call WaveInflu directly or ask for a separate WaveInflu credential.
- Never invent, pattern-match, or infer email addresses.
- Do not claim that every creator has a public or deliverable email.
- Distinguish `Not found` from `Lookup failed`.
- Preserve profile URLs so an operator can verify every row.
- State when the target platform or content direction was assumed.
- Keep the result table concise and sort recommendations by API similarity score.
- Treat contact data as sensitive operational data; do not publish it or transmit it elsewhere without authorization.

## API Reference

This skill calls these AIsa endpoints directly:

- [WaveInflu Email Lookup](https://aisa.one/docs/api-reference/waveinflu/post_waveinflu-email-lookup) — retrieve creator emails and normalized profile details from TikTok, Instagram, or YouTube profile URLs.
- [WaveInflu Similar Creators](https://aisa.one/docs/api-reference/waveinflu/post_waveinflu-similar) — match similar YouTube or TikTok creators from a seed profile and/or content direction.

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
