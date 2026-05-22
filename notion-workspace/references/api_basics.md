# AISA gateway API basics

Self-contained HTTP reference for this skill. All Notion calls use these patterns.

**Base URL:** `https://api.aisa.one`  
**Path prefix:** `/apis/v1/composio/...`  
**Header:** `Authorization: Bearer $AISA_API_KEY`  
**Toolkit slug:** `notion`

**Windows:** Use `curl.exe` in PowerShell.

---

## Verify API key

```bash
curl "https://api.aisa.one/apis/v1/composio/auth/session/info" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Auth configs (Notion)

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs?toolkit_slug=notion&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Create (confirm with user):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/auth_configs" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit": { "slug": "notion" },
    "auth_config": { "type": "use_composio_managed_auth" }
  }'
```

---

## Connected accounts

List:

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?toolkit_slugs=notion&user_ids=alice@example.com" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

OAuth link (confirm with user):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/link" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config_id": "ac_xxxxxxxx",
    "user_id": "alice@example.com"
  }'
```

Refresh credentials:

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/{nanoid}/refresh" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Tools — schema and execute

List Notion tools:

```bash
curl "https://api.aisa.one/apis/v1/composio/tools?toolkit_slug=notion&limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Get schema (`input_parameters` field):

```bash
curl "https://api.aisa.one/apis/v1/composio/tools/NOTION_GET_PAGE_MARKDOWN" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Execute (confirm before writes):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_GET_PAGE_MARKDOWN" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": { "page_id": "..." }
  }'
```

| Field | Required | Notes |
|-------|----------|-------|
| `connected_account_id` | One of ca/user | `ca_...` from connected_accounts |
| `user_id` | One of ca/user | Same as OAuth link; not `entity_id` (deprecated) |
| `arguments` | Yes* | From `input_parameters`; mutually exclusive with `text` |

Check response `successful`. On false, read `error`.

NL argument generation (may return 1010 on some tiers):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/{tool_slug}/input" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "text": "..." }'
```

---

## Triggers (Notion)

List types:

```bash
curl "https://api.aisa.one/apis/v1/composio/triggers_types?limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Upsert (confirm with user):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/trigger_instances/NOTION_PAGE_ADDED_TO_DATABASE/upsert" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "trigger_config": { "database_id": "..." }
  }'
```

Active list: `GET /trigger_instances/active`  
Enable/disable: `PATCH /trigger_instances/manage/{triggerId}`  
Delete: `DELETE /trigger_instances/manage/{triggerId}`

---

## Webhooks

```bash
curl "https://api.aisa.one/apis/v1/composio/webhook_subscriptions/event_types" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Create subscription (confirm with user): `POST /webhook_subscriptions`  
List: `GET /webhook_subscriptions`, `GET /webhook_endpoints`

---

## MCP (Notion)

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Notion MCP",
    "auth_config_ids": ["ac_xxxxxxxx"]
  }'
```

Generate URL: `POST /mcp/servers/generate`

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| 401 / quota | Renew `AISA_API_KEY` at aisa.one |
| 429 | Slow down; retry with delay |
| Error 1811 | Add `user_id` or `connected_account_id` on execute |
| Empty auth_configs | Create auth config for `notion` |
| PENDING OAuth >2 min | New `connected_accounts/link` |
| `successful: false` | Read `error`; fix arguments; see `notion_gotchas.md` |
| 404 on Notion resource | Share page/DB with integration in Notion |

Replace `{nanoid}`, `{triggerId}` with real IDs from prior responses. Never use placeholder test IDs in production.
