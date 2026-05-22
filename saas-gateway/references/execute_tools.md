# Execute tools

Discover toolkits/tools and run SaaS tool operations through the AISA gateway.

**Base:** `https://api.aisa.one`
**Header:** `Authorization: Bearer $AISA_API_KEY`

Prerequisite: a **connected account** (`connected_account_id`) for the target toolkit — see `./connect_account.md`.

## List toolkits

```bash
curl "https://api.aisa.one/apis/v1/composio/toolkits?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Optional query parameters: `category` (string), `managed_by` (string), `sort_by` (string).

**Response:** `items[]` array, each item has `slug`, `name`, `description`, `logo_url`, `categories[]`, `auth_schemes[]`.

## Get toolkit by slug

```bash
curl "https://api.aisa.one/apis/v1/composio/toolkits/github" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Fetch multiple toolkits

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/toolkits/multi" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "toolkits": ["github", "slack"] }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `toolkits` | string[] | **Yes** | List of toolkit slugs to fetch in bulk |

## List tools

```bash
curl "https://api.aisa.one/apis/v1/composio/tools?toolkit_slug=github&limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Optional query parameters: `toolkit_slug`, `limit`, `cursor`, `tags`.

**Response:** `items[].slug` is used in the execute path.

## List tool enum (compact)

```bash
curl "https://api.aisa.one/apis/v1/composio/tools/enum?toolkit_slug=github" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## Get tool details and schema

**Critical step before execution:** Always retrieve the tool schema to know the required and optional arguments.

```bash
curl "https://api.aisa.one/apis/v1/composio/tools/GITHUB_CREATE_AN_ISSUE" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Response schema location:** `input_parameters` (NOT `inputSchema`, `schema`, or `parameters`). Structure:

```json
{
  "input_parameters": {
    "description": "...",
    "properties": {
      "owner": { "type": "string", "description": "...", "title": "Owner" },
      "repo":  { "type": "string", "description": "..." },
      "title": { "type": "string", "description": "..." }
    },
    "required": ["owner", "repo", "title"]
  }
}
```

`input_parameters.required` is the list of mandatory fields; `input_parameters.properties` contains all available fields. Each property also includes `human_parameter_name` (user-friendly label) and `human_parameter_description`.

---

## POST /tools/execute/{tool_slug}

Execute the specified tool. **Confirm with the user before executing** — this makes a real API call to a third-party service.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GITHUB_CREATE_AN_ISSUE" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "owner": "my-org",
      "repo": "my-repo",
      "title": "Issue from agent"
    }
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connected_account_id` | string | Recommended | Connected account ID to use (`ca_` prefix, from `GET /connected_accounts`). Either this or `user_id` must be provided |
| `user_id` | string | Recommended | User identifier in multi-user scenarios (same value as the `user_id` used when linking the account). Either this or `connected_account_id` must be provided. **Note: `entity_id` is deprecated; use `user_id` instead** |
| `entity_id` | string | Not recommended | Deprecated alias for `user_id`. Still functional but not guaranteed long-term |
| `arguments` | object | Conditionally required | Key-value pairs of tool parameters (mutually exclusive with `text`). Field structure from `GET /tools/{tool_slug}` `input_parameters` |
| `text` | string | Conditionally required | Natural language task description (mutually exclusive with `arguments`). The API converts it to arguments internally |
| `version` | string | No | Tool version; default `"00000000_00"` (latest stable) |
| `custom_auth_params` | object | No | Custom auth parameters for parameterized auth scenarios; includes `base_url`, `parameters`, `body` sub-fields |
| `custom_connection_data` | object | No | Custom connection data (supports OAUTH2, API_KEY, BEARER_TOKEN, etc.) |
| `allow_tracing` | boolean | No | Deprecated. Enable debug tracing (for troubleshooting only) |

**Notes:**
- At least one of `connected_account_id` or `user_id` is required; omitting both returns **Error 1811**
- `arguments` and `text` are mutually exclusive; at least one must be provided
- `entity_id` is a legacy alias for `user_id`; prefer `user_id`

**Troubleshooting `successful: false`:**
- `connected_account_id` does not exist or has expired → refresh or re-link
- Missing required argument → re-check `input_parameters`
- Insufficient permissions → OAuth scope too narrow; re-link with broader scope

---

## POST /tools/execute/{tool_slug}/input

Generate tool arguments from natural language (LLM auto-infers field values), then pass the returned `arguments` to the execute endpoint.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GITHUB_CREATE_AN_ISSUE/input" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create an issue titled Hello in my-org/my-repo"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | **Yes** | Natural language text describing the task to complete |
| `version` | string | No | Tool version; defaults to latest |
| `system_prompt` | string | No | System prompt to control LLM behavior when generating parameters |
| `custom_description` | string | No | Custom tool description to help the LLM generate more accurate parameters |

**Note:** This endpoint returns `error code: 1010` (Cloudflare block) on some API key tiers. If that occurs, read `GET /tools/{tool_slug}` `input_parameters` and construct the arguments manually.

---

## POST /tools/execute/proxy

Bypass the gateway's tool execution layer and send a raw HTTP request to a third-party API using the connected account's credentials.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/proxy" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "endpoint": "https://api.github.com/user",
    "method": "GET"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint` | string | **Yes** | Target API URL (absolute URL, or path relative to the connected account base URL) |
| `method` | string | **Yes** | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `connected_account_id` | string | Recommended | Connected account ID for authentication. Uses project default if omitted |
| `body` | any | No | Request body (for POST/PUT/PATCH) |
| `parameters` | array | No | Additional HTTP headers or query parameters |
| `binary_body` | object | No | Binary upload body. URL form: `{"url": "https://...", "content_type": "..."}`; base64 form: `{"base64": "..."}` |
| `custom_connection_data` | object | No | Custom connection data, overrides the connected account's credentials |

---

## POST /tools/scopes/required

Query the OAuth permission scopes required by a set of tools, to verify scope coverage before linking an account.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/scopes/required" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "tools": ["GITHUB_CREATE_AN_ISSUE", "GITHUB_LIST_REPOS"] }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tools` | string[] | **Yes** | List of tool slugs to query. **All tools must belong to the same toolkit** |
| `version` | string | No | Toolkit version; defaults to the pinned HTTP version |

**Note:** Field name is `tools`, not `tool_slugs` (older docs are incorrect).

---

## Tool Router Session

A persistent MCP-style session for multi-tool access or building MCP integrations.

### POST /tool_router/session — Create session

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-alice-001",
    "toolkits": { "enable": ["github", "slack"] }
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | **Yes** | Unique identifier of the user the session belongs to (recommend using a database user ID) |
| `toolkits` | object | No | Toolkit configuration. Use `enable` (whitelist array) or `disable` (blacklist array); mutually exclusive |
| `tools` | object | No | Per-toolkit tool-level configuration; can enable/disable specific tools or filter by tag |
| `connected_accounts` | object | No | Per-toolkit override of the default connected account (value is a nano-ID array) |
| `auth_configs` | object | No | Per-toolkit override of the default auth config |
| `tags` | array/object | No | Global MCP tool annotation filter. Array form treated as enable list; object form supports `enabled`/`disabled` arrays |
| `manage_connections` | object | No | Connection management config; includes `enabled` (boolean), `callback_url` (string) sub-fields |
| `multi_account` | object | No | Multi-account config: `enable` (boolean), `max_accounts_per_toolkit` (integer), `require_explicit_selection` (boolean) |
| `preload` | object | No | Preload config. `tools` field takes a tool slug array or `"all"` to dynamically expose all tools |
| `search` | object | No | Search assistant config; includes `enable` (boolean) |
| `execute` | object | No | Execution assistant config; includes `enable_multi_execute` (boolean) |
| `workbench` | object | No | Workbench config: `enable`, `proxy_execution_enabled`, `auto_offload_threshold`, `sandbox_size` |
| `experimental` | object | No | Experimental feature config; unstable, may change or be removed in future versions |

**Response:** `session_id` (session ID), and optionally an `mcp` connection URL.

---

### PATCH /tool_router/session/{session_id} — Update session configuration

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkits": { "enable": ["github", "slack", "notion"] }
  }'
```

**Request body fields:** Same as POST /tool_router/session, but all fields are **optional** (only provided fields are updated).

---

### GET /tool_router/session/{session_id} — Get session

```bash
curl "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

### POST /tool_router/session/{session_id}/attach — Attach to session

Used to mount an existing session in a new request context (e.g. passing inline custom tools).

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/attach" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `experimental` | object | No | Inline custom tools and toolkits (v3.1 sessions do not persist custom content; must be re-supplied each request) |

---

### POST /tool_router/session/{session_id}/execute — Execute tool

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/execute" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_slug": "GITHUB_LIST_REPOSITORIES_FOR_A_USER",
    "arguments": {}
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_slug` | string | **Yes** | Unique slug of the tool to execute; supports meta tools and app tools |
| `arguments` | object | No | Key-value pairs of tool parameters |
| `account` | string | No | In multi-account scenarios, specifies which connected account to use (account ID, e.g. `coup_hXXX`) |
| `enable_auto_workbench_offload` | boolean | No | If true, automatically switches to workbench offload preview when the response exceeds the configured threshold |
| `experimental` | object | No | Inline custom tools (v3.1 does not persist; must be supplied each request) |

---

### POST /tool_router/session/{session_id}/execute_meta — Execute meta tool

Meta tools are session-level operations (e.g. listing connected accounts within the session).

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/execute_meta" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "COMPOSIO_SEARCH_TOOLS",
    "arguments": {}
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | **Yes** | Unique slug identifier of the meta tool |
| `arguments` | object | No | Parameters required by the meta tool |
| `experimental` | object | No | Inline custom tools (v3.1 does not persist; must be supplied each request) |

---

### POST /tool_router/session/{session_id}/search — Search tools

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/search" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["create github issue", "send slack message"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queries` | string[] | **Yes** | List of search queries to execute in parallel (supports multiple simultaneous queries) |
| `model` | string | No | Optional model hint that influences search/planning behavior (e.g. `"gpt-4o"`) |
| `experimental` | object | No | Inline custom tools |

---

### POST /tool_router/session/{session_id}/proxy_execute — Proxy request within session

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/proxy_execute" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit_slug": "github",
    "endpoint": "https://api.github.com/user",
    "method": "GET"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint` | string | **Yes** | Target API URL (absolute URL or relative path) |
| `method` | string | **Yes** | HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) |
| `toolkit_slug` | string | **Yes** | Toolkit slug used for request authentication |
| `body` | any | No | Request body (for POST/PUT/PATCH) |
| `parameters` | array | No | Additional HTTP headers or query parameters |
| `binary_body` | object | No | Binary upload body (same as proxy execute) |
| `custom_connection_data` | object | No | Custom connection data |

---

### GET /tool_router/session/{session_id}/tools — List session tools

```bash
curl "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/tools" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### GET /tool_router/session/{session_id}/toolkits — List session toolkits

```bash
curl "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/toolkits" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### GET /tool_router/session/{session_id}/config_history — Configuration history

```bash
curl "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/config_history" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## POST /tool_router/session/{session_id}/link — Link toolkit to session

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/link" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit_slug": "github",
    "auth_config_id": "ac_xxxxxxxx"
  }'
```

---

## Session File Mounts

```bash
# List files in a mount
curl "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/items" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get presigned upload URL
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/upload_url" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "file_name": "report.csv" }'

# Get presigned download URL
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/download_url" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "file_name": "report.csv" }'

# Delete file
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session/{session_id}/mounts/{mount_id}/delete" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "file_name": "report.csv" }'
```

---

## POST /files/upload/request — File upload (project-level)

Two-step process: first get a presigned URL, then PUT directly to S3.

**Step 1 — Get presigned URL:**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/files/upload/request" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "data.csv",
    "mimetype": "text/csv",
    "md5": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "tool_slug": "GMAIL_SEND_EMAIL",
    "toolkit_slug": "gmail"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | **Yes** | Original file name, e.g. `"quarterly_report.pdf"` |
| `mimetype` | string | **Yes** | File MIME type, e.g. `"application/pdf"`, `"image/png"`, `"text/csv"` |
| `md5` | string | **Yes** | MD5 hash of the file (used for deduplication and integrity verification), e.g. `"a1b2c3d4e5f6..."` |
| `tool_slug` | string | **Yes** | Slug of the tool the file belongs to, e.g. `"GMAIL_SEND_EMAIL"`, `"SLACK_UPLOAD_FILE"` |
| `toolkit_slug` | string | **Yes** | Slug of the toolkit the file belongs to, e.g. `"gmail"`, `"slack"`, `"github"` |

**Step 2 — PUT file content to the presigned URL (standard S3 upload; no AISA auth header required):**

```bash
curl.exe -X PUT "<presigned_url>" \
  -H "Content-Type: text/csv" \
  --data-binary @data.csv
```

## GET /files/list — List files

```bash
curl "https://api.aisa.one/apis/v1/composio/files/list?limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## POST /logs/tool_execution — Query tool execution logs

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/logs/tool_execution" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "limit": 10 }'
```

**Response structure (confirmed from live testing):**
- Root field is `logs` (not `items`); pagination field is `next_cursor` (not `cursor`)
- Each record contains: `id`, `type` (`tool.execution`), `status` (`success`/`error`), `timestamp`, `metadata.tool.slug`, `metadata.user_id`, `metadata.connected_account_id`, `metrics.duration_ms`

```json
{
  "logs": [
    {
      "id": "log_oqM_n2jqUo1l",
      "type": "tool.execution",
      "status": "success",
      "timestamp": "2026-05-20T09:59:08.489Z",
      "metadata": {
        "tool": { "slug": "GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER" },
        "user_id": "jordan@aisa.one",
        "connected_account_id": "ca_FS_MUjkSQpDm",
        "toolkit": { "slug": "github" }
      },
      "metrics": { "duration_ms": 609 }
    }
  ],
  "next_cursor": "..."
}
```

```bash
curl "https://api.aisa.one/apis/v1/composio/logs/tool_execution/{id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Related

- Connections: `./connect_account.md`
- Triggers: `./triggers_webhooks.md`
- MCP / Projects / Usage: `./mcp_projects_usage.md`
- Full index: `./endpoint_catalog.md` (groups `toolkits`, `tools`, `tool_router`, `files`, `logs`)
