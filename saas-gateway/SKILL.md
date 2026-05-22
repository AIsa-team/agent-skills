---
name: saas-gateway
description: 'Unified SaaS integration gateway via api.aisa.one (AISA gateway, v3.1): manage OAuth auth for third-party SaaS apps (Gmail/Slack/GitHub/Notion etc.), tool execution, tool-router sessions, triggers, webhooks, MCP servers, and usage stats. Use when connecting third-party SaaS accounts, running cross-SaaS tools, managing MCP servers, setting up triggers, or checking usage. Keywords: SaaS gateway, connect app, OAuth link, run tool, auth config, tool router, MCP server, trigger, webhook, connected account, usage stats'
homepage: https://aisa.one
license: MIT
compatibility: "Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires curl and AISA_API_KEY."
metadata:
  aisa:
    emoji: 🔌
    homepage: https://aisa.one
    requires:
      bins:
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

# SaaS Gateway (`saas-gateway`) 🔌

**Unified SaaS integration gateway (v3.1) for autonomous agents. Powered by AISA.**

One API key. Connect third-party SaaS apps and run tools through the AISA gateway (`api.aisa.one`).

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills specification](https://agentskills.io/specification)

Requires `curl` and `AISA_API_KEY` (get one at [aisa.one](https://aisa.one)).

## When to use

- Integrate Gmail, Slack, GitHub, or other third-party SaaS toolkits via `api.aisa.one`
- Create OAuth links, list connected accounts, or refresh credentials
- Discover and execute SaaS tools or tool-router sessions
- Manage triggers and webhooks (with user confirmation for writes)
- Create and manage MCP servers for session-scoped tool access
- Upload/download files, check usage statistics, or manage projects

## When NOT to use

- The user needs direct access to the upstream provider's API without going through the AISA gateway
- The task only needs generic web search (use a search skill instead)
- No `AISA_API_KEY` is available

## Quick Start

**Linux / macOS:**

```bash
export AISA_API_KEY="your-key"
```

**Windows (PowerShell):**

```powershell
$env:AISA_API_KEY = "your-key"
```

All requests use:

- **Base URL:** `https://api.aisa.one`
- **Path prefix:** `/apis/v1/composio/...` (literal AISA gateway path — do not modify)
- **Auth header:** `Authorization: Bearer $AISA_API_KEY`

**Windows note:** Use `curl.exe` instead of `curl` in PowerShell (the built-in `curl` is an alias for `Invoke-WebRequest` and has different syntax). Or use CMD rather than PowerShell.

Replace `{param}` in paths with real IDs from previous responses. Never use mock IDs like `test_nanoid_001` in production.

## What Can You Do?

```text
"Check my AISA project session and list auth configs for GitHub"
"Create an OAuth link so user alice can connect Slack"
"Run the GitHub create-issue tool for a connected account"
"List active triggers and webhook subscriptions"
"Set up an MCP server so my agent can use GitHub tools in a session"
"Upload a file and check my project usage this month"
```

## Intent → Workflow Quick Reference (Agent Entry Point)

Map the user's request to a workflow before reading further:

| User intent keywords | Workflow |
|----------------------|---------|
| connect / authorize / OAuth / link a third-party app | **→ Workflow 2** |
| run tool / execute / create issue / send email | **→ Workflow 3** (resolve `connected_account_id` first) |
| MCP server / tool session / session-scoped access | **→ Workflow 3 tool-router** or **Workflow 5** |
| trigger / webhook / event subscription | **→ Workflow 4** |
| usage stats / call count / billing | **→ Workflow 6 Usage** |
| file upload / file list | **→ Workflow 6 Files** |
| project management / API key reset | **→ Workflow 6 Projects** |
| verify session / list auth configs | **→ Workflow 1** |
| notion / Notion workspace / page / database / wiki / task DB | **→ use notion-workspace skill** |

> When intent is unclear, run Workflow 1 to confirm session context, then ask the user what they need.

---

## Core Workflows

### 1. Verify session and project context

```bash
curl "https://api.aisa.one/apis/v1/composio/auth/session/info" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Key fields: `project`, `org_member`, `api_key` (nested IDs may appear under `api_key`).

If the user also asks for auth configs (e.g. GitHub), in the same flow:

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs?toolkit_slug=github&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Use:** `items[].id` as `auth_config_id` for OAuth linking.

Details: `references/auth_and_session.md`

### 2. Connect a user to a third-party app (OAuth)

1. `GET /apis/v1/composio/auth_configs?toolkit_slug={slug}` — find `items[].id` as `auth_config_id`
   - If empty: **ask the user** whether to create an auth config, then `POST /apis/v1/composio/auth_configs` with `{"toolkit": {"slug": "{slug}"}, "auth_config": {"type": "use_composio_managed_auth"}}` — use `auth_config.id` from response as `auth_config_id`
2. **Confirm with user** before `POST /apis/v1/composio/connected_accounts/link` — body: `auth_config_id`, `user_id` (email or arbitrary string, e.g. `alice@example.com`); `callback_url` is optional
3. Send the user to `redirect_url` from the response — the **human must open this URL in a browser** to complete OAuth
4. Poll `GET /apis/v1/composio/connected_accounts?user_ids={user_id}&toolkit_slugs={slug}` until `status` is no longer `PENDING`
   - **Poll interval:** wait 3–5 seconds between checks, up to ~2 minutes
   - **Possible statuses:** `ACTIVE` (connected), `PENDING` (user has not completed OAuth yet), `DISCONNECTED` / `REVOKED` (link failed or expired)
   - If still `PENDING` after 2 minutes, tell the user the link may have expired and offer to create a new link
5. On success, save `items[].id` (nanoid) as `connected_account_id` for tool execution

**If an ACTIVE connection already exists:** If `GET connected_accounts` already returns an `ACTIVE` connection for the given `user_id` + `toolkit_slug`, **reuse that `connected_account_id` directly — no re-OAuth needed**. Only create a new link when the user explicitly requests re-authorization (the old link is not automatically removed; ask the user whether to keep it).

Details: `references/connect_account.md`

### 3. Discover and execute tools

**Direct execution (one-off tool call):**

1. Resolve `connected_account_id`:
   - User already connected → `GET /apis/v1/composio/connected_accounts?toolkit_slugs={slug}` (add `user_ids=` if multiple accounts exist) and use `items[].id`
   - Not connected → run Workflow 2 first
2. Find the tool slug:
   - `GET /apis/v1/composio/tools?toolkit_slug={slug}` — map user intent (e.g. "create issue") to actual `items[].slug` (e.g. `GITHUB_CREATE_AN_ISSUE`)
   - **Never guess `tool_slug`** — always list tools first if unsure
3. Get the tool's argument schema:
   - `GET /apis/v1/composio/tools/{tool_slug}` — inspect `input_parameters.required` (mandatory fields) and `input_parameters.properties` (all fields with types and descriptions)
   - Alternatively, use natural-language input generation: `POST /apis/v1/composio/tools/execute/{tool_slug}/input` with `{"text": "Create an issue titled Hello in my-org/my-repo"}` — may return `error code: 1010` on restricted tiers, in which case use the schema from `GET /tools/{tool_slug}` instead
4. **Confirm with user** before `POST /apis/v1/composio/tools/execute/{tool_slug}` — body requires:
   - `connected_account_id`: from step 1
   - `entity_id`: the user identifier string (same value used as `user_id` when linking the account, e.g. `alice@example.com`)
   - `arguments`: matching the tool's `input_parameters` schema
5. Check the response: `successful` field indicates if the tool call worked. If `successful` is false, inspect `error` or `data` for details and retry with corrected arguments

**Tool router (session-scoped, MCP-style access):**

Use tool router when you need a persistent session for multiple tool calls, or when building an MCP integration.

1. `POST /apis/v1/composio/tool_router/session` — body: `{"user_id": "user-id", "toolkits": ["github"]}`
2. Save `session_id` from the response
3. Search for tools: `POST .../tool_router/session/{session_id}/search` — body: `{"query": "create issue"}`
4. List available tools: `GET .../tool_router/session/{session_id}/tools`
5. **Confirm with user** before `POST .../tool_router/session/{session_id}/execute` — body: `{"tool_slug": "GITHUB_CREATE_AN_ISSUE", "arguments": {...}}`
6. Other session operations:
   - `GET .../session/{session_id}` — check session status
   - `GET .../session/{session_id}/toolkits` — list session's toolkits
   - `POST .../session/{session_id}/link` — add a toolkit connection to the session
   - `POST .../session/{session_id}/proxy_execute` — raw HTTP proxy within session
   - `GET .../session/{session_id}/config_history` — view past config changes

Details: `references/execute_tools.md`

### 4. Triggers and webhooks (read-first)

1. `GET /apis/v1/composio/trigger_instances/active` — list active triggers (read-only, no confirmation needed)
2. `GET /apis/v1/composio/triggers_types` — browse available trigger types
3. **Confirm with user** before any create/update/delete on triggers or webhook subscriptions
4. `GET /apis/v1/composio/webhook_endpoints` — list registered webhook URLs
5. `GET /apis/v1/composio/webhook_subscriptions` — list active subscriptions
6. `GET /apis/v1/composio/webhook_subscriptions/event_types` — see available event types before creating a subscription

Details: `references/triggers_webhooks.md`

### 5. MCP servers

Create and manage MCP (Model Context Protocol) servers for agent tool access.

1. List existing MCP servers: `GET /apis/v1/composio/mcp/servers` (optional: `category`, `search` filters)
2. Create an MCP server for a single app: **Confirm with user**, then `POST /apis/v1/composio/mcp/servers` — body: `{"app": {"slug": "github"}, "name": "My GitHub MCP"}`
3. Create a custom MCP server with multiple apps: **Confirm with user**, then `POST /apis/v1/composio/mcp/servers/custom` — body: `{"apps": [{"slug": "github"}, {"slug": "slack"}], "name": "My Multi-App MCP"}`
4. Generate an MCP URL: `POST /apis/v1/composio/mcp/servers/generate` — produces a connection URL for the agent
5. Manage instances: `GET /apis/v1/composio/mcp/servers/{serverId}/instances`, `POST ...` to create, `DELETE .../instances/{instanceId}` to remove
6. Get/update/delete a server: `GET/PATCH/DELETE /apis/v1/composio/mcp/{id}`

Details: `references/endpoint_catalog.md` (group: `mcp`)

### 6. Files, projects, and usage

**Files:**
- List uploaded files: `GET /apis/v1/composio/files/list?limit=10`
- Upload: `POST /apis/v1/composio/files/upload/request` — get a presigned S3 URL, then PUT the file content to that URL

**Projects:**
- List projects: `GET /apis/v1/composio/org/owner/project/list`
- Create project: **Confirm with user**, then `POST /apis/v1/composio/org/owner/project/new`
- Get/update/delete: `GET/DELETE /apis/v1/composio/org/owner/project/{nano_id}`
- Regenerate API key: **Confirm with user**, then `POST /apis/v1/composio/org/owner/project/{nano_id}/regenerate_api_key`

**Usage statistics:**
- Org-level summary: `POST /apis/v1/composio/org/usage/summary` — body: `{}`
- Org-level breakdown by entity: `POST /apis/v1/composio/org/usage/{entity_type}` — common `{entity_type}` values: `tool_calls`, `sessions`; body accepts `group_by`, `limit`, `order_by`, `order_direction`
- Project-level: `POST /apis/v1/composio/project/usage/summary` — body: `{}`; `POST /apis/v1/composio/project/usage/{entity_type}` — same fields as above

**Response:** Usage summary root field is `entities` (contains `tool_calls` and `sessions` sub-objects); breakdown root field is `groups` (aggregated by the `group_by` dimension)

**Tool execution logs:**
- Search logs: `POST /apis/v1/composio/logs/tool_execution` — body: `{"limit": 10}`; response root field is **`logs`** (not `items`), pagination key is **`next_cursor`**
- Get single log: `GET /apis/v1/composio/logs/tool_execution/{id}`
- Key log entry fields: `metadata.tool.slug`, `metadata.user_id`, `metadata.connected_account_id`, `metrics.duration_ms`, `status` (`success`/`error`)

Details: `references/execute_tools.md` (logs section), `references/mcp_projects_usage.md` (usage section)

## Reference routing

| User intent | Read this file |
|-------------|----------------|
| Session, auth configs | `references/auth_and_session.md` |
| Connect accounts, OAuth link | `references/connect_account.md` |
| Toolkits, tools, tool router | `references/execute_tools.md` |
| Triggers, webhooks | `references/triggers_webhooks.md` |
| MCP servers, projects, usage, file upload | `references/mcp_projects_usage.md` |
| Exact path or HTTP method | `references/endpoint_catalog.md` |

**Lookup order:** intent → reference (curl examples) → `endpoint_catalog.md` → [upstream API docs](https://docs.composio.dev) for semantics only. **Request URLs must use AISA `inner_uri` paths.**

## Path parameters

| Placeholder | Example source | Naming note |
|-------------|----------------|-------------|
| `{nanoid}` | `items[].id` from list responses (auth configs, connected accounts, webhooks) | Most endpoints |
| `{nanoId}` | Same as `{nanoid}` — **camelCase** per API convention | `connected_accounts/{nanoId}/status` only |
| `{nano_id}` | Same as `{nanoid}` — **snake_case** | `webhook_endpoints/{nano_id}`, `org/owner/project/{nano_id}` |
| `{slug}` | `toolkits[].slug` or user-stated toolkit name (e.g. `github`, `slack`) | |
| `{tool_slug}` | `tools` list: `items[].slug` (e.g. `GITHUB_CREATE_AN_ISSUE`) | |
| `{session_id}` | `tool_router/session` create response | |
| `{serverId}` | MCP server list/create response | camelCase |
| `{triggerId}` | `trigger_instances/active` list response | camelCase |
| `{id}` | Context-dependent: log ID, MCP server ID, etc. | |

**Important:** Use the exact casing shown in the endpoint path. The API is case-sensitive.

## Safety

- Confirm with the user before **POST / PATCH / DELETE** that change production data (including `connected_accounts/link`, `tools/execute`, `tool_router/session/{id}/execute`, MCP server create/delete, auth config create/update, trigger upsert/delete, webhook create/delete)
- **DELETE** may soft-delete configs, connections, or webhooks
- OAuth `redirect_url` must be opened by a human in a browser
- Read-only **GET** calls (session, list configs, list tools) do not require confirmation unless the user asked you to avoid network calls
- **Rate limiting:** if you receive 429 responses, wait briefly and retry. Avoid rapid-fire API calls in loops without delays

## Troubleshooting

| Symptom | Action |
|---------|--------|
| 401 + quota exhausted | Renew or replace `AISA_API_KEY` |
| Empty `items` on auth_configs | Ask user to create auth config or verify toolkit slug |
| Empty `items` on connected_accounts | Run OAuth link workflow; connection may still be `PENDING` |
| 404 on PATCH with path ID | Use a real ID from a prior GET/POST list response; check casing (`{nanoid}` vs `{nanoId}`) |
| 500 on path with fake ID | Do not use test placeholders |
| SSL timeout on large lists | Retry with smaller `limit` or narrower filters |
| Multiple GitHub connections returned | Re-query with `user_ids=` filter or ask user which account |
| User says "create issue" but slug unknown | List tools first; never guess `tool_slug` |
| Tool execution returns `successful: false` | Inspect `error` field; common causes: wrong `connected_account_id`, missing required arguments, insufficient permissions — get tool schema via `GET /tools/{tool_slug}` and retry |
| Error 1811: entity_id required | Add `user_id` to `tools/execute` body — use the same value as `user_id` when the account was linked. `entity_id` is the deprecated alias for `user_id` |
| Error 10400: Invalid discriminator on auth_config | `auth_config.type` is required; use `use_composio_managed_auth` or `use_custom_auth` |
| Error 1151: MCP server name already exists | MCP server names must be unique per project; choose a different `name` |
| `x-org-api-key` required error on project list | Project list requires an org-level API key, not a project-level `AISA_API_KEY`; use session/info to confirm which key you have |
| OAuth link expires before user completes | Create a new link with `POST connected_accounts/link` |
| Token refresh returns `redirect_url` with status `INITIATED` | OAuth cannot auto-refresh; user must re-authorize at the returned URL |
| `logs/tool_execution` response has no `items` | Response root field is `logs` (not `items`); pagination key is `next_cursor` (not `cursor`) |
| 429 Too Many Requests | Slow down; add delays between API calls; reduce `limit` parameter |

