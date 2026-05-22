# Notion triggers and MCP

Notion automation via the AISA gateway.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

Trigger/webhook HTTP reference: `api_basics.md`

**Prerequisite:** `connected_account_id` for the Notion account used in `trigger_config`.

---

## Trigger types (13)

| Slug | Type | When it fires |
|------|------|---------------|
| `NOTION_ALL_PAGE_EVENTS_TRIGGER` | poll | Any page created/updated in workspace |
| `NOTION_PAGE_CREATED` | webhook | New page created |
| `NOTION_PAGE_ADDED_TRIGGER` | webhook | New page added (workspace scope) |
| `NOTION_PAGE_UPDATED_TRIGGER` | poll | Page updated |
| `NOTION_PAGE_PROPERTIES_UPDATED` | webhook | Page properties changed |
| `NOTION_PAGE_CONTENT_UPDATED` | webhook | Page body content updated |
| `NOTION_PAGE_ADDED_TO_DATABASE` | poll | New row added to a database |
| `NOTION_DATABASE_CREATED` | webhook | New database container created |
| `NOTION_DATASOURCE_CREATED` | webhook | New data source in existing database |
| `NOTION_DATASOURCE_SCHEMA_UPDATED` | webhook | Data source schema changed |
| `NOTION_COMMENT_CREATED` | webhook | New comment (optional `page_id` scope) |
| `NOTION_COMMENTS_ADDED_TRIGGER` | poll | New comment on specific `block_id` |
| `NOTION_VIEW_CREATED` | webhook | New Notion view created |

**Discover current slugs:**

```bash
curl "https://api.aisa.one/apis/v1/composio/triggers_types?limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Filter results for `notion` in name or slug. Get config schema:

```bash
curl "https://api.aisa.one/apis/v1/composio/triggers_types/{slug}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## List active triggers (read-only)

```bash
curl "https://api.aisa.one/apis/v1/composio/trigger_instances/active?limit=20" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Optional: `user_ids`, `connected_account_ids`, `trigger_names`.

---

## Create or update a trigger

**Confirm with user** before POST.

Example — new row in database (slug may vary; confirm via `triggers_types`):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/trigger_instances/NOTION_PAGE_ADDED_TO_DATABASE/upsert" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "trigger_config": {
      "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

**Body fields:**

| Field | Description |
|-------|-------------|
| `connected_account_id` | Notion connected account (`ca_...`) |
| `trigger_config` | Keys depend on trigger type — from `GET /triggers_types/{slug}` |
| `toolkit_versions` | Optional; `"latest"` or version map |

Poll triggers often accept `interval` (minutes) in `trigger_config`.

**Comment triggers:** require **Read comments** on the Notion integration; old connections may need re-authorization (`workflow_connect.md`).

---

## Manage triggers

| Action | Method | Path |
|--------|--------|------|
| Enable/disable | PATCH | `/trigger_instances/manage/{triggerId}` |
| Delete | DELETE | `/trigger_instances/manage/{triggerId}` |

`{triggerId}` from `trigger_instances/active` list (`items[].id`).

---

## Webhooks (delivery)

Gateway-managed Notion may use a provisioned ingress. Custom OAuth apps: complete the Notion verification token flow (see the Notion API docs).

List and create subscriptions (`api_basics.md`):

- `GET /webhook_endpoints`
- `POST /webhook_subscriptions`
- `GET /webhook_subscriptions/event_types`

---

## MCP — Notion-only server

Let an agent use Notion tools via MCP URL. **Confirm with user** before create.

### Single-app MCP server

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Notion MCP",
    "auth_config_ids": ["ac_xxxxxxxx"]
  }'
```

Use `auth_config_ids` from `GET /auth_configs?toolkit_slug=notion`.

### Custom server (Notion in multi-toolkit setup)

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers/custom" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Notion Agent MCP",
    "toolkits": ["notion"],
    "auth_config_ids": ["ac_xxxxxxxx"]
  }'
```

### Generate connection URL

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/mcp/servers/generate" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "server_id": "xxxxxxxx" }'
```

List/update/delete server: `GET/PATCH/DELETE /mcp/{id}`  
Instances: `GET/POST /mcp/servers/{serverId}/instances`, `DELETE .../instances/{instanceId}`

**Error 1151:** MCP server name must be unique per project — pick another `name`.

---

## Tool router (session-scoped Notion)

Alternative to MCP for multi-step Notion calls in one session:

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tool_router/session" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice@example.com",
    "toolkits": ["notion"]
  }'
```

Then `POST .../session/{session_id}/search` and `.../execute`. See `api_basics.md` for session create pattern.
