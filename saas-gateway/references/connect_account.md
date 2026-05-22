# Connect accounts

Link end users to third-party apps (Gmail, Slack, GitHub, etc.) via AISA gateway connected accounts.

**Base:** `https://api.aisa.one`
**Header:** `Authorization: Bearer $AISA_API_KEY`

---

## Workflow overview

1. List auth configs → pick `auth_config_id`
2. Create auth link → user opens `redirect_url` in browser
3. Poll until `status` is `ACTIVE`
4. Save `id` (nanoid) as `connected_account_id` for tool execution

## Connected account statuses

| Status | Meaning |
|--------|---------|
| `ACTIVE` | Connection healthy; ready for tool execution |
| `PENDING` | OAuth link created, user has not completed authorization yet |
| `DISCONNECTED` | Token expired or revoked |
| `REVOKED` | Explicitly revoked at the provider or via API |
| `FAILED` | OAuth flow failed (e.g. user denied permission) |

---

## List connected accounts

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Max items per page |
| `cursor` | string | No | Pagination cursor from previous response |
| `toolkit_slugs` | string | No | Comma-separated toolkit slugs to filter (e.g. `github,slack`) |
| `user_ids` | string | No | Comma-separated user IDs to filter |
| `status` | string | No | Filter by status (e.g. `ACTIVE`) |

**Key response fields:** `items[].id` (connected_account_id), `items[].status`, `items[].toolkit.slug`, `items[].user_id`

---

## Create OAuth link (recommended for gateway-managed OAuth)

**Confirm with user before calling** — creates a production connection.

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/link" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config_id": "ac_xxxxxxxx",
    "user_id": "alice@example.com",
    "callback_url": "https://your-app.com/oauth/callback"
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `auth_config_id` | string | **Yes** | ID from `GET /auth_configs` (`items[].id`, format `ac_...`) |
| `user_id` | string | **Yes** | Arbitrary identifier for the end user (email or custom string, e.g. `alice@example.com`). Also used as `entity_id` in tool execution. |
| `callback_url` | string | No | URL the gateway redirects to after OAuth completes. Must be HTTPS. |

**Key response fields:**
- `redirect_url` — send to user; they must open in browser to complete OAuth
- `connected_account_id` — format `ca_...`; usable before OAuth completes (status will be `PENDING`)
- `link_token` — format `lk_...`
- `expires_at` — ISO 8601 timestamp; link expires if unused

**After sending the link:**
- Poll `GET /connected_accounts?user_ids={user_id}&toolkit_slugs={slug}` every 3–5 seconds
- Stop when `status` is `ACTIVE` (success) or `FAILED` (denied)
- If still `PENDING` after ~2 minutes, offer to generate a new link

---

## Create connected account (API key / custom credentials)

For non-OAuth toolkits that use API keys.

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config": { "id": "ac_xxxxxxxx" },
    "connection": {
      "user_id": "alice@example.com",
      "state": {
        "authScheme": "API_KEY",
        "val": { "generic_api_key": "sk-xxxx" }
      }
    }
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `auth_config.id` | string | **Yes** | Auth config ID (`ac_...`) from `GET /auth_configs` |
| `connection.user_id` | string | **Yes** | End-user identifier (same value used as `entity_id` in tool execution) |
| `connection.state.authScheme` | string enum | **Yes** | Auth scheme. Values: `API_KEY`, `BEARER_TOKEN`, `BASIC`, `OAUTH2` |
| `connection.state.val` | object | **Yes** | Credential values. Shape depends on `authScheme` — see below |

**`connection.state.val` by authScheme:**

| authScheme | val fields |
|-----------|-----------|
| `API_KEY` | `generic_api_key` (string) — the API key value |
| `BEARER_TOKEN` | `token` (string) — the bearer token |
| `BASIC` | `username` (string), `password` (string) |

For OAuth schemes, prefer `connected_accounts/link` instead.

---

## Get connected account

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Update connected account

```bash
curl -X PATCH "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "new-user-id"
  }'
```

**Request body:** Send only fields to change.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | No | New user identifier for this connection |

---

## Refresh credentials

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}/refresh" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

No request body fields required. May return a new `redirect_url` if token cannot be refreshed automatically.

---

## Revoke at provider

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}/revoke" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

No request body. Confirm with user — transitions connection to `REVOKED`.

---

## Enable or disable connection

```bash
curl -X PATCH "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoId}/status" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "enabled": true }'
```

**Note:** path uses `{nanoId}` (camelCase) — only endpoint with this casing.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | **Yes** | `true` to enable, `false` to disable the connection |

---

## Delete connected account

```bash
curl -X DELETE "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Confirm with user before deleting.

---

## Consumer permissions (optional)

### Get permissions for a connected account

```bash
curl "https://api.aisa.one/apis/v1/composio/consumer/connected_accounts/{nanoid}/permissions" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Resolve consumer permissions

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/consumer/permissions/resolve" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

No required body fields for basic resolution. Used to check which tools are accessible for a user.

---

## Related

- Auth configs: `./auth_and_session.md`
- Run tools: `./execute_tools.md`
- Full index: `./endpoint_catalog.md`
