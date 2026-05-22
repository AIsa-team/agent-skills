# Connect Gmail and execute tools

Platform API v3.1 via the AISA gateway — **Gmail only**. This skill is self-contained; no other skill required.

**Base:** `https://api.aisa.one`  
**Path prefix:** `/apis/v1/composio/...`  
**Header:** `Authorization: Bearer $AISA_API_KEY`

**Windows:** Use `curl.exe` in PowerShell.

```bash
# Linux / macOS
export AISA_API_KEY="your-key"

# Windows PowerShell
$env:AISA_API_KEY = "your-key"
```

Replace `{param}` with real IDs from API responses. Never use placeholder IDs in production.

---

## 0. Verify API key (optional)

```bash
curl "https://api.aisa.one/apis/v1/composio/auth/session/info" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Confirms the key is valid before OAuth or tool calls.

---

## 1. Connect Gmail (OAuth)

### 1a. List auth configs for Gmail

```bash
curl "https://api.aisa.one/apis/v1/composio/auth_configs?toolkit_slug=gmail&limit=10" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Use `items[].id` as `auth_config_id` (`ac_...`). If empty, ask the user to create one (step 1b).

### 1b. Create auth config (if none exists)

**Confirm with user** before POST.

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/auth_configs" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "toolkit": { "slug": "gmail" },
    "auth_config": { "type": "use_composio_managed_auth" }
  }'
```

Use `auth_config.id` from the response as `auth_config_id`.

### 1c. Check existing connection

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?toolkit_slugs=gmail&user_ids=rep@company.com" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

| Status | Meaning |
|--------|---------|
| `ACTIVE` | Ready — use `items[].id` as `connected_account_id` (`ca_...`) |
| `PENDING` | OAuth not finished |
| `DISCONNECTED` / `REVOKED` | Re-link required |

**Reuse ACTIVE accounts** — no re-OAuth unless the user asks to reconnect.

### 1d. Create OAuth link

**Confirm with user** before POST.

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/connected_accounts/link" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "auth_config_id": "ac_xxxxxxxx",
    "user_id": "rep@company.com"
  }'
```

- Send user `redirect_url` — **human must open in browser**
- Poll every **3–5 s** (max ~2 min):

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?user_ids=rep@company.com&toolkit_slugs=gmail" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Stop when `status` is `ACTIVE`. Save `items[].id` as `connected_account_id`.

---

## 2. Discover Gmail tool schema

Never guess argument names.

```bash
curl "https://api.aisa.one/apis/v1/composio/tools/GMAIL_FETCH_EMAILS" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Use `input_parameters.properties` and `input_parameters.required`.

List tools (if slug unknown):

```bash
curl "https://api.aisa.one/apis/v1/composio/tools?toolkit_slug=gmail&limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Only use slugs from [`tool_whitelist.md`](./tool_whitelist.md) unless the user explicitly needs another Gmail tool.

---

## 3. Execute a Gmail tool

**Confirm with user** before POST for writes (draft, send, label modify, batch).

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_FETCH_EMAILS" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "query": "in:inbox is:unread",
      "max_results": 20
    }
  }'
```

| Field | Required | Description |
|-------|----------|-------------|
| `connected_account_id` | One of ca / user_id | From `connected_accounts` list (`ca_...`) |
| `user_id` | One of ca / user_id | Same value used when linking OAuth |
| `arguments` | Yes* | Tool parameters from schema (*or `text` for NL generation) |

- Omitting both `connected_account_id` and `user_id` → **Error 1811**
- Check response `successful`; if false, inspect `error` and re-fetch schema

**Optional — NL argument generation:**

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_FETCH_EMAILS/input" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "text": "List 10 unread inbox emails" }'
```

If error `1010`, build `arguments` manually from `GET /tools/{tool_slug}`.

---

## 4. Troubleshooting

| Symptom | Action |
|---------|--------|
| 401 | Invalid or expired `AISA_API_KEY` |
| Empty `auth_configs` | Create config (1b) with `toolkit.slug=gmail` |
| Empty `connected_accounts` | Run OAuth link (1d) |
| `successful: false` | Wrong `connected_account_id`, missing required arg, or narrow OAuth scope — re-link |
| Error 1811 | Add `user_id` or `connected_account_id` to execute body |
| Error 10400 on auth_config | `auth_config.type` required: `use_composio_managed_auth` |
| 429 | Backoff 1s → 2s → 4s; reduce `max_results` and batch size |

---

## 5. File attachments (optional)

Upload via the AISA gateway files API when a draft needs an attachment:

1. `POST /apis/v1/composio/files/upload/request` with `tool_slug` + `toolkit_slug` for the target send tool
2. PUT file to presigned URL
3. Pass file reference in draft/send `arguments` per tool schema

Details: [Composio docs — Gmail](https://docs.composio.dev/toolkits/gmail).
