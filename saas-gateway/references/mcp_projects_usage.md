# MCP servers, projects, and usage

Manage MCP (Model Context Protocol) servers, org projects, and usage statistics.

**Base:** `https://api.aisa.one`
**Header:** `Authorization: Bearer $AISA_API_KEY`

---

## MCP Servers

### GET /mcp/servers — List MCP servers

```bash
curl "https://api.aisa.one/apis/v1/composio/mcp/servers?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Optional query parameters: `category` (category filter), `search` (keyword search).

### GET /mcp/app/{appKey} — Get MCP server for a specific app

```bash
curl "https://api.aisa.one/apis/v1/composio/mcp/app/github" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

`{appKey}` is the toolkit slug (e.g. `github`, `slack`).

---

### POST /mcp/servers — Create MCP server (single auth config)

Creates an MCP server bound to one or more existing auth configs. **Confirm with the user before executing.**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My GitHub MCP",
    "auth_config_ids": ["ac_xxxxxxxx"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | MCP server name (4–30 characters; letters, numbers, spaces, and hyphens allowed) |
| `auth_config_ids` | string[] | **Yes** | List of existing auth config IDs (`ac_` prefix). The MCP server uses these auth configs |
| `allowed_tools` | string[] | No | Whitelist of tool slugs to enable. If omitted, all available tools are allowed |
| `managed_auth_via_composio` | boolean | No | Whether the AISA gateway manages authentication (default `false`) |
| `no_auth_apps` | string[] | No | Apps that should be enabled but require no authentication (NO_AUTH type apps) |

**Response:** `id` (server ID for subsequent operations), `mcp_url` (MCP connection URL).

---

### POST /mcp/servers/custom — Create custom MCP server (multiple toolkits)

Creates a custom MCP server that includes multiple toolkits. **Confirm with the user before executing.**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers/custom" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Multi-App MCP",
    "toolkits": ["github", "slack", "notion"],
    "auth_config_ids": ["ac_xxxxxxxx", "ac_yyyyyyyy"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Server name (4–30 characters; letters, numbers, spaces, and hyphens allowed) |
| `toolkits` | string[] | No | List of toolkit slugs to enable (e.g. `["github", "slack"]`) |
| `auth_config_ids` | string[] | No | List of auth config IDs (`ac_` prefix) |
| `allowed_tools` | string[] | No | Whitelist of additional tool slugs not in the standard toolkits |
| `managed_auth_via_composio` | boolean | No | Whether the AISA gateway manages authentication (default `false`) |
| `custom_tools` | string[] | No | Deprecated — use `allowed_tools` instead |

---

### POST /mcp/servers/generate — Generate MCP URL

Generates a personalized MCP connection URL for a specified server and user.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers/generate" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_server_id": "mcp_xxxxxxxx",
    "user_ids": ["user-alice-001"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mcp_server_id` | string | **Yes** | Unique ID of the MCP server to generate a URL for |
| `user_ids` | string[] | No | List of target user IDs to generate URLs for |
| `connected_account_ids` | string[] | No | Associated connected account ID list |
| `managed_auth_by_composio` | boolean | No | Whether the AISA gateway manages authentication |

**Response:** Contains a URL ready to use directly with an MCP client.

---

### GET /mcp/{id} — Get MCP server details

```bash
curl "https://api.aisa.one/apis/v1/composio/mcp/{id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

`{id}` is the MCP server ID from a list or create response.

### PATCH /mcp/{id} — Update MCP server

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/mcp/{id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated MCP Name",
    "toolkits": ["github", "slack", "notion"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Updated server name (4–30 characters) |
| `auth_config_ids` | string[] | No | Updated list of associated auth config IDs |
| `toolkits` | string[] | No | Updated list of toolkit slugs for the server |
| `allowed_tools` | string[] | No | Updated list of enabled tool slugs |
| `managed_auth_via_composio` | boolean | No | Whether the AISA gateway manages authentication |

### DELETE /mcp/{id} — Delete MCP server

**Confirm before executing** — deletion is irreversible.

```bash
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/mcp/{id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

---

### MCP Server Instances

An instance is a user-level instance of an MCP server, linked to the user's connected accounts.

```bash
# List instances
curl "https://api.aisa.one/apis/v1/composio/mcp/servers/{serverId}/instances" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### POST /mcp/servers/{serverId}/instances — Create instance

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers/{serverId}/instances" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-alice-001"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | **Yes** | Unique user identifier (also used as the instance ID) |

```bash
# Delete instance (confirm before executing — also removes associated connected accounts)
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/mcp/servers/{serverId}/instances/{instanceId}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

**Note:** Both `{serverId}` and `{instanceId}` are camelCase format IDs.

---

## Projects

### GET /org/owner/project/list — List projects

```bash
curl "https://api.aisa.one/apis/v1/composio/org/owner/project/list" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### POST /org/owner/project/new — Create project

**Confirm with the user before executing.**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/org/owner/project/new" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-awesome-project",
    "should_create_api_key": true
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Unique project name (3–75 characters; letters, numbers, `_`, `-` only; pattern `^[a-zA-Z0-9_-]+$`) |
| `should_create_api_key` | boolean | No | Whether to create an API key at the same time. If `true`, the API key is returned in the response (default `false`) |
| `config` | object | No | Initial project configuration; see config sub-fields below |

**`config` sub-fields (optional at creation; for updates see PATCH /org/project/config):**

| Sub-field | Type | Required at creation | Description |
|-----------|------|----------------------|-------------|
| `is_2FA_enabled` | boolean | **Yes** | Whether to enable two-factor authentication |
| `mask_secret_keys_in_connected_account` | boolean | **Yes** | Whether to mask secret keys in connected accounts (security compliance) |
| `log_visibility_setting` | string | **Yes** | Log visibility setting. Enum: `show_all` (show all), `dont_store_data` (do not store data) |
| `display_name` | string | No | Project display name |
| `logo_url` | string | No | Project logo URL |
| `require_mcp_api_key` | boolean | No | Whether MCP connections require an API key |
| `signed_url_file_expiry_in_seconds` | number | No | Presigned URL expiry in seconds (range 1–86400) |

### GET /org/owner/project/{nano_id} — Get project details

```bash
curl "https://api.aisa.one/apis/v1/composio/org/owner/project/{nano_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### DELETE /org/owner/project/{nano_id} — Delete project

**Confirm before executing.**

```bash
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/org/owner/project/{nano_id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

### POST /org/owner/project/{nano_id}/regenerate_api_key — Regenerate API key

**Confirm before executing — the old API key is immediately invalidated.** No request body.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/org/owner/project/{nano_id}/regenerate_api_key" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### GET /org/project/config — Get project configuration

```bash
curl "https://api.aisa.one/apis/v1/composio/org/project/config" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### PATCH /org/project/config — Update project configuration

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/org/project/config" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "log_visibility_setting": "dont_store_data",
    "require_mcp_api_key": true
  }'
```

**Request body fields (all optional; only provided fields are updated):**

| Field | Type | Description |
|-------|------|-------------|
| `is_2FA_enabled` | boolean | Whether to enable two-factor authentication |
| `display_name` | string | Project display name |
| `logo_url` | string | Project logo URL |
| `mask_secret_keys_in_connected_account` | boolean | Whether to mask secret keys in connected accounts |
| `log_visibility_setting` | string | Log visibility. Enum: `show_all`, `dont_store_data` |
| `require_mcp_api_key` | boolean | Whether MCP connections require an API key |
| `signed_url_file_expiry_in_seconds` | number | Presigned URL expiry in seconds (range 1–86400) |
| `is_composio_link_enabled_for_managed_auth` | boolean | Toggle the gateway-managed auth link (deprecated; not recommended) |

---

## Usage Statistics

All usage endpoints use POST method with a JSON body.

### POST /org/usage/summary — Org-level usage summary

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/org/usage/summary" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": 1700000000000,
    "to": 1710000000000
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | number | No | Query start time (Unix millisecond timestamp). Defaults to 30 days before `to` |
| `to` | number | No | Query end time (Unix millisecond timestamp, exclusive). Defaults to current time |
| `entity_types` | string[] | No | Filter by specific metering entity types. Returns all types if omitted |
| `filters` | object | No | Additional filter conditions |

### POST /org/usage/{entity_type} — Org-level usage breakdown

Common `{entity_type}` values: `tool_calls` (tool invocations), `sessions` (sessions).

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/org/usage/tool_calls" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": 1700000000000,
    "group_by": "tool_slug",
    "limit": 50
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | number | No | Query start time (Unix millisecond timestamp) |
| `to` | number | No | Query end time (Unix millisecond timestamp) |
| `group_by` | string | No | Grouping dimension. Default for `tool_calls` is `tool_slug`; default for `sessions` is `user_id` |
| `limit` | integer | No | Maximum number of groups to return. Default 100, max 1000 |
| `order_by` | string | No | Sort field. Enum: `key`, `total_quantity`, `event_count` (default `total_quantity`) |
| `order_direction` | string | No | Sort direction. Enum: `asc`, `desc` (default `desc`) |
| `filters` | object | No | Additional filter conditions |

### POST /project/usage/summary — Project-level usage summary

Same fields as `POST /org/usage/summary`, but scoped to the current project.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/project/usage/summary" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### POST /project/usage/{entity_type} — Project-level usage breakdown

Same fields as `POST /org/usage/{entity_type}`, but scoped to the current project.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/project/usage/tool_calls" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "group_by": "user_id",
    "limit": 100
  }'
```

---

## Path parameter reference

| Parameter | Format | Source |
|-----------|--------|--------|
| `{id}` | MCP server ID | `items[].id` from `GET /mcp/servers` |
| `{serverId}` | camelCase MCP server ID | Same as above |
| `{instanceId}` | camelCase instance ID | `GET /mcp/servers/{serverId}/instances` |
| `{appKey}` | Toolkit slug (lowercase) | Toolkit list |
| `{nano_id}` | Project ID (snake_case) | `items[].id` from `GET /org/owner/project/list` |
| `{entity_type}` | `tool_calls` or `sessions` | Usage endpoint path parameter |

---

## Related

- `./endpoint_catalog.md` — grouped index: `mcp`, `org`, `project`
- `./execute_tools.md` — tool execution (Tool Router Session and MCP integration)
- `./auth_and_session.md` — auth configs (source of `auth_config_ids`)
