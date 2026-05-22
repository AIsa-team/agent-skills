# Workflow: Connect Notion

Link an end user to Notion via Composio. **Toolkit slug:** `notion`.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

More HTTP patterns: `api_basics.md`

---

## Prerequisites

- Valid `AISA_API_KEY`

---

## Step 1 — List auth configs

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs?toolkit_slug=notion&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

**Use:** `items[].id` as `auth_config_id` (format `ac_...`).

If empty, **ask user** then create:

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/auth_configs" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit": { "slug": "notion" },
    "auth_config": { "type": "use_composio_managed_auth" }
  }'
```

Use `auth_config.id` from response.

---

## Step 2 — Check existing connection

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?user_ids=alice@example.com&toolkit_slugs=notion&status=ACTIVE" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

If `items[].status` is `ACTIVE`, reuse `items[].id` as `connected_account_id` — skip OAuth unless user wants re-auth.

---

## Step 3 — Create OAuth link

**Confirm with user** before POST.

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/link" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config_id": "ac_xxxxxxxx",
    "user_id": "alice@example.com"
  }'
```

Send user the **`redirect_url`** — they must open it in a browser.

Notion-specific: after OAuth, user should connect the integration under **Settings & Members → Connections** and share target pages with the integration.

---

## Step 4 — Poll until ACTIVE

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?user_ids=alice@example.com&toolkit_slugs=notion" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

- Poll every **3–5 seconds**, up to **~2 minutes**
- Success: `status` = `ACTIVE` → save `items[].id` (`ca_...`)
- Still `PENDING` after 2 min → offer new link
- `FAILED` / `REVOKED` → diagnose and re-link

---

## Alternative — API key connection

For integrations using Notion internal integration token:

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
        "val": { "generic_api_key": "secret_xxxxxxxx" }
      }
    }
  }'
```

See `api_basics.md` for refresh/revoke and API key field shapes.

---

## After connect

Store for all Notion tool calls:

- `connected_account_id` — `ca_...`
- `user_id` — same string used in link (e.g. `alice@example.com`)

Next: `workflow_read.md`, `workflow_write_page.md`, or `workflow_database.md`.
