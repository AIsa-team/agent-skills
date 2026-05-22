# Workflow: Notion databases (query and write rows)

**Prerequisite:** `connected_account_id` + `user_id` — see `workflow_connect.md`.

**Critical:** Always `NOTION_FETCH_DATABASE` before insert/update — see `notion_gotchas.md`.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

---

## Query

### Step 1 — Resolve database_id

Use `workflow_read.md` § Search:

- `NOTION_SEARCH_NOTION_PAGE` with `filter_value=database`, or
- `NOTION_FETCH_DATA` with `fetch_type=databases`

Do **not** pass a page_id to query endpoints.

### Step 2 — Fetch schema

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

Note property **names** and **types** (`title`, `rich_text`, `select`, `status`, `date`, `checkbox`, `multi_select`, …).

### Step 3 — Query rows

**Simple list:**

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

**With filters/sorts:**

**Tool:** `NOTION_QUERY_DATABASE_WITH_FILTER`

Build `filter` using types from schema — `title` filter key is special (built-in title column). See the Notion API docs for filter object shape; property type keys must match schema (`select` vs `status`).

**Single row:** `NOTION_FETCH_ROW` with `page_id` of the row.

---

## Write

### Insert row — **Confirm with user**

**Tool:** `NOTION_INSERT_ROW_DATABASE`

`properties` must be a **list** of objects (not a flat dict):

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_INSERT_ROW_DATABASE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "properties": [
        { "name": "Name",   "type": "title",     "value": "New task" },
        { "name": "Status", "type": "select",    "value": "In Progress" },
        { "name": "Due",    "type": "date",      "value": "2026-05-21" },
        { "name": "Price",  "type": "number",    "value": "299" }
      ]
    }
  }'
```

> **`number` type:** `value` must be a **string** (`"299"`, not `299`). Passing a JSON number literal returns `Input should be a valid string`.

Replace names/types with values from **your** `NOTION_FETCH_DATABASE` response.

**Common failures:**

| Error | Fix |
|-------|-----|
| not a property | Wrong property `name` — re-fetch schema |
| expected to be X | Wrong `type` for that property |
| multiple_data_sources | Database not supported — pick another DB |

### Insert from natural language

**Tool:** `NOTION_INSERT_ROW_FROM_NL`

Fallback to manual `properties` if tier returns error `1010`.

### Update row properties

**Tool:** `NOTION_UPDATE_PAGE`

Rows are pages in Notion — use row `page_id` and same `properties` list format.

---

## Create database (under a page)

**Tool:** `NOTION_CREATE_DATABASE`

- `parent_id` must be a **page_id**, not a database_id
- **Confirm with user**

---

## Database flow summary

```text
Find DB id → search/fetch
Schema → NOTION_FETCH_DATABASE
Query → NOTION_QUERY_DATABASE or _WITH_FILTER
Insert → NOTION_INSERT_ROW_DATABASE (properties list)
Update → NOTION_UPDATE_PAGE
```

Page body content (blocks) is **not** database insert — use `workflow_write_page.md`.
