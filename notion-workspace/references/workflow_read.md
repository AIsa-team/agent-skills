# Workflow: Read and search Notion

**Prerequisite:** `connected_account_id` + `user_id` — see `workflow_connect.md`.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

Intent map: `notion_intent_to_tool.md` | Pitfalls: `notion_gotchas.md`

---

## Search

### Search pages or databases by query

**Tool:** `NOTION_SEARCH_NOTION_PAGE`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_SEARCH_NOTION_PAGE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "query": "Roadmap",
      "filter_value": "page"
    }
  }'
```

Get exact fields from `GET /tools/NOTION_SEARCH_NOTION_PAGE`. Common `filter_value`: `page`, `database`.

**Use response:** `id` for `page_id` or `database_id` in later calls.

### List workspace data (broader discovery)

**Tool:** `NOTION_FETCH_DATA`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_FETCH_DATA" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "fetch_type": "databases"
    }
  }'
```

Inspect `input_parameters` for `fetch_type` options (`pages`, `databases`, etc.).

---

## Content — read pages

### Markdown export (preferred for full text)

**Tool:** `NOTION_GET_PAGE_MARKDOWN`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_GET_PAGE_MARKDOWN" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "page_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

### Page properties and metadata

**Tool:** `NOTION_RETRIEVE_PAGE` — properties only, not block body.

### Child blocks

**Tool:** `NOTION_FETCH_BLOCK_CONTENTS`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_FETCH_BLOCK_CONTENTS" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "block_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

Page UUID can be used as `block_id`.

### From Notion URL

**Tool:** `NOTION_FETCH_ALL_BLOCK_CONTENTS` — pass `page_url` or `block_id`. Do not use database view URLs containing `?v=`.

---

## Content — read databases

### 1. Fetch schema first

**Tool:** `NOTION_FETCH_DATABASE`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_FETCH_DATABASE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

### 2. Query rows

**Tool:** `NOTION_QUERY_DATABASE`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_QUERY_DATABASE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }'
```

### 3. Filtered query

**Tool:** `NOTION_QUERY_DATABASE_WITH_FILTER` — build `filter` from schema property **types** (see `notion_gotchas.md`).

### Single row

**Tool:** `NOTION_FETCH_ROW` with row `page_id`.

---

## Schema lookup before execute

Always refresh arguments from:

```bash
curl "https://api.aisa.one/apis/v1/composio/tools/NOTION_GET_PAGE_MARKDOWN" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Response field: `input_parameters` (not `inputSchema`).

---

## Read flow summary

```text
Search → NOTION_SEARCH_NOTION_PAGE / NOTION_FETCH_DATA
Page text → NOTION_GET_PAGE_MARKDOWN
Database → NOTION_FETCH_DATABASE → NOTION_QUERY_DATABASE[_WITH_FILTER]
```

Check `successful` on every execute. On false → `notion_gotchas.md`.
