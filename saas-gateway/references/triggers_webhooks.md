# Triggers and webhooks

Inspect and manage AISA gateway triggers and webhook configuration.

**Base:** `https://api.aisa.one`
**Header:** `Authorization: Bearer $AISA_API_KEY`

**Safety:** Prefer GET for discovery. POST/PATCH/DELETE can change production automations — confirm with the user.

---

## GET /trigger_instances/active — List active triggers

```bash
curl "https://api.aisa.one/apis/v1/composio/trigger_instances/active?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Optional query parameters: `user_ids` (comma-separated), `connected_account_ids`, `trigger_names`, `cursor`.

**Response:** List of trigger instances. `items[].id` (i.e. `{triggerId}`) is used for subsequent manage operations.

---

## POST /trigger_instances/{slug}/upsert — Create or update a trigger

`{slug}` is the trigger type slug from `GET /triggers_types`. **Confirm with the user before executing.**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/trigger_instances/GITHUB_PULL_REQUEST_EVENT/upsert" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "trigger_config": {
      "owner": "my-org",
      "repo": "my-repo",
      "events": ["opened", "closed"]
    }
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connected_account_id` | string | Recommended | Connected account ID to bind the trigger to (`ca_` prefix). Note: `connectedAuthId` is deprecated, use this field instead |
| `trigger_config` | object | Depends on trigger | Trigger configuration parameters (key-value pairs; structure varies by trigger type). Note: `triggerConfig` is deprecated, use this field instead |
| `toolkit_versions` | string/object | No | Toolkit version spec. Use `"latest"` or a version map like `{"github": "1.0.0"}`. Note: `version` field is deprecated |

**`trigger_config` structure:** Varies by trigger type. Call `GET /triggers_types/{slug}` first to see the required config fields for that trigger.

---

## PATCH /trigger_instances/manage/{triggerId} — Enable/disable a trigger

**Note:** `{triggerId}` is a camelCase ID from the active trigger list.

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/trigger_instances/manage/{triggerId}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "status": "enable" }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | **Yes** | Target state. Enum: `enable` (activate), `disable` (deactivate) |

**Note:** Enum values are `enable`/`disable` (verbs), not `enabled`/`disabled` (adjectives).

## DELETE /trigger_instances/manage/{triggerId} — Delete a trigger

```bash
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/trigger_instances/manage/{triggerId}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

---

## GET /triggers_types — List trigger type catalog

```bash
# Full list (with details)
curl "https://api.aisa.one/apis/v1/composio/triggers_types?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Compact enum (slugs only)
curl "https://api.aisa.one/apis/v1/composio/triggers_types/list/enum" \
  -H "Authorization: Bearer $AISA_API_KEY"

# Get details for a single trigger type (includes trigger_config field definitions)
curl "https://api.aisa.one/apis/v1/composio/triggers_types/{slug}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Response fields:** `slug` (trigger type slug), `name`, `description`, `config` (trigger_config field definitions).

---

## Webhook Endpoints (receivers)

A webhook endpoint is the target URL that receives event payloads.

### GET /webhook_endpoints — List

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_endpoints?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### POST /webhook_endpoints — Create

Registers a webhook receiver for a third-party app (e.g. Slack outgoing webhook). **Confirm before executing.**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/webhook_endpoints" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit_slug": "slack",
    "client_id": "your-oauth-app-client-id"
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `toolkit_slug` | string | **Yes** | Toolkit identifier (e.g. `slack`, `discord`, `github`) |
| `client_id` | string | **Yes** | OAuth app Client ID that identifies which app this endpoint belongs to |

### GET /webhook_endpoints/{nano_id} — Get details

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_endpoints/{nano_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Note: webhook endpoints use `{nano_id}` (snake_case) as the path parameter.

### POST /webhook_endpoints/{nano_id} — Full configuration (PUT semantics)

Use on first-time setup; all required `setup_fields` must be provided.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/webhook_endpoints/{nano_id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "signing_secret": "your-slack-signing-secret",
      "bot_token": "xoxb-..."
    }
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | object | **Yes** | Key-value pairs covering all required `setup_fields` for this toolkit. Unlike PATCH, all required fields must be supplied (PUT semantics) |

### PATCH /webhook_endpoints/{nano_id} — Partial configuration update

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/webhook_endpoints/{nano_id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "signing_secret": "new-secret-value"
    }
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | object | **Yes** | Key-value pairs matching toolkit `setup_fields`. Only include fields to update; omitted fields remain unchanged |

### DELETE /webhook_endpoints/{nano_id} — Delete

```bash
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/webhook_endpoints/{nano_id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

---

## Webhook Subscriptions (event subscriptions)

A subscription defines which events trigger delivery to a webhook endpoint.

### GET /webhook_subscriptions — List

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_subscriptions?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### GET /webhook_subscriptions/event_types — Query available event types

**Call this before creating a subscription** to get valid `event_type` values and `supported_versions`.

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/event_types" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Confirmed event types:

| event_type | Description |
|-----------|-------------|
| `composio.trigger.message` | Fired when a trigger receives data from an external service |
| `composio.connected_account.expired` | Fired when a connected account needs re-authentication |
| `composio.trigger.disabled` | Fired when the gateway automatically disables a trigger |

### POST /webhook_subscriptions — Create subscription

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/webhook_subscriptions" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-app.com/webhooks/composio",
    "enabled_events": ["composio.trigger.message", "composio.connected_account.expired"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `webhook_url` | string | **Yes** | HTTPS URL to receive webhook events |
| `enabled_events` | string[] | **Yes** | Array of event types to subscribe to (valid values from the `/event_types` endpoint) |
| `version` | string | No | Webhook payload version. Enum: `V1`, `V2`, `V3` (defaults to latest) |

### GET /webhook_subscriptions/{id} — Get subscription details

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/{id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Note: webhook subscriptions use `{id}` (not `{nanoid}`).

### PATCH /webhook_subscriptions/{id} — Update subscription

```bash
curl.exe -X PATCH "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/{id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled_events": ["composio.trigger.message"]
  }'
```

**Request body fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `webhook_url` | string | No | Update target URL |
| `enabled_events` | string[] | No | Replacement list of subscribed event types (full replace, not append) |
| `version` | string | No | Webhook payload version. Enum: `V1`, `V2`, `V3` |

### DELETE /webhook_subscriptions/{id} — Delete subscription

```bash
curl.exe -X DELETE "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/{id}" \
  -H "Authorization: Bearer $env:AISA_API_KEY"
```

### POST /webhook_subscriptions/{id}/rotate_secret — Rotate webhook secret

No request body. The old secret is invalidated immediately after rotation; update signature verification logic on the consumer side.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/{id}/rotate_secret" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Path parameter reference

| Parameter | Format | Source |
|-----------|--------|--------|
| `{slug}` | Trigger type slug (uppercase, e.g. `GITHUB_PULL_REQUEST_EVENT`) | `GET /triggers_types` |
| `{triggerId}` | camelCase trigger instance ID | `items[].id` from `GET /trigger_instances/active` |
| `{nano_id}` | snake_case webhook endpoint ID | `items[].id` from `GET /webhook_endpoints` |
| `{id}` | Webhook subscription ID | `items[].id` from `GET /webhook_subscriptions` |

---

## Related

- `./endpoint_catalog.md` — grouped index: `trigger_instances`, `triggers_types`, `webhook_endpoints`, `webhook_subscriptions`
- `./execute_tools.md` — tool execution
- `./connect_account.md` — connected accounts that trigger sources depend on
