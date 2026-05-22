# Auth and session

Auth/session and `auth_configs` APIs via the AISA gateway.

**Base:** `https://api.aisa.one`
**Header:** `Authorization: Bearer $AISA_API_KEY`

---

## Get current session

```bash
curl "https://api.aisa.one/apis/v1/composio/auth/session/info" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Key response fields:** `project.id`, `org_member.email`, `api_key.name`, `api_key.project_id`

**Use:** Confirm the key is valid and identify which project is active before other calls.

---

## List auth configs

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs?toolkit_slug=github&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `toolkit_slug` | string | No | Filter by toolkit (e.g. `github`, `slack`) |
| `limit` | integer | No | Max items per page (default 10) |
| `cursor` | string | No | Pagination cursor from previous response |
| `is_composio_managed` | boolean | No | Filter by managed vs custom auth |
| `search` | string | No | Text search on config name |
| `show_disabled` | boolean | No | Include disabled configs (default false) |

**Key response fields:** `items[].id` (use as `auth_config_id`), `items[].is_composio_managed`, `items[].auth_scheme`

---

## Create auth config

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/auth_configs" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit": { "slug": "github" },
    "auth_config": { "type": "use_composio_managed_auth" }
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `toolkit.slug` | string | **Yes** | Toolkit identifier (e.g. `github`, `slack`, `gmail`) |
| `auth_config.type` | string enum | **Yes** | Auth mode. Values: `use_composio_managed_auth` (the AISA gateway hosts the OAuth app, no credentials needed) or `use_custom_auth` (bring your own OAuth client_id/secret) |
| `auth_config.client_id` | string | No | OAuth client ID. Required only when `type` is `use_custom_auth` |
| `auth_config.client_secret` | string | No | OAuth client secret. Required only when `type` is `use_custom_auth` |

**Key response fields:** `auth_config.id` (use as `auth_config_id` in subsequent calls), `auth_config.is_composio_managed`, `auth_config.auth_scheme`

Requires user confirmation — creates project-level configuration.

---

## Get auth config by ID

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Replace `{nanoid}` with `items[].id` from the list response.

---

## Update auth config

```bash
curl -X PATCH "https://api.aisa.one/apis/v1/composio/auth_configs/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config": { "client_id": "new-client-id" }
  }'
```

**Request body:** Send only the fields to change. Same shape as create body — all fields optional.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `auth_config.client_id` | string | No | Updated OAuth client ID |
| `auth_config.client_secret` | string | No | Updated OAuth client secret |

Confirm with user before PATCH.

---

## Enable or disable auth config

```bash
curl -X PATCH "https://api.aisa.one/apis/v1/composio/auth_configs/{nanoid}/enabled" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "enabled": true }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | **Yes** | `true` to enable, `false` to disable the auth config |

---

## Delete auth config

```bash
curl -X DELETE "https://api.aisa.one/apis/v1/composio/auth_configs/{nanoid}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Soft-delete. Confirm with user first.

---

## Related

- OAuth connections: `./connect_account.md`
- Full index: `./endpoint_catalog.md` (groups `auth`, `auth_configs`, `org`)
