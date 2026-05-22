# Notion gotchas (via AISA gateway)

Notion-specific rules. Generic HTTP/OAuth errors: `api_basics.md` Troubleshooting.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

---

## 1. Integration must access the page or database

Notion uses **page-level sharing**, not broad OAuth scopes alone.

- In Notion: **Settings & Members → Connections** — ensure your integration is connected
- Share each target page/database with the integration (⋯ → Connect to → your integration)
- **404** on fetch/execute often means "not shared with integration", not a wrong API key

---

## 2. ID types — never interchange

| ID | Used for | How to obtain |
|----|----------|---------------|
| `page_id` | Single page/row, retrieve page, comments, markdown | `NOTION_SEARCH_NOTION_PAGE`, `NOTION_FETCH_DATA`, query row `items[].id` |
| `database_id` | Query database, insert row, fetch schema | Search with `filter_value=database`, or URL UUID (32 hex) |
| `block_id` | Block children, append blocks, some comments | Page ID works for many block APIs (pages are blocks) |
| `data_source_id` | `NOTION_MOVE_PAGE` parent when moving into a database | From `NOTION_FETCH_DATABASE` response — not the same as `database_id` |

**Common API errors:**

| Message | Fix |
|---------|-----|
| Provided ID is a **page**, not a **database** | Use `database_id` from search; don't pass page URL to `NOTION_QUERY_DATABASE` |
| Can't create databases parented by a **database** | `NOTION_CREATE_DATABASE` parent must be a **page_id** |
| Database view URL with `?v=` | Not a page ID — use database query tools, not block fetch |

---

## 3. Database properties (insert/update rows)

Before `NOTION_INSERT_ROW_DATABASE` or `NOTION_UPDATE_PAGE`:

1. Call `NOTION_FETCH_DATABASE` with the real `database_id`
2. Read exact property **names** and **types** from the schema
3. Build `properties` as a **list** of objects: `{ "name": "...", "type": "...", "value": "..." }`

Rules:

- Names and types are **case-sensitive**
- Each database has exactly one property of type **`title`** (primary name column)
- Other text fields are usually **`rich_text`**, not `title`
- **`select` / `status` / `multi_select`** option values must match Notion **exactly** (case-sensitive)
- Property name `Status` in UI might be type `status` or `select` — trust schema, not the label

**Unsupported:** databases with **multiple data sources** (synced/combined views) — `NOTION_INSERT_ROW_DATABASE` returns validation errors. Use a single-source database.

---

## 4. Page content and blocks

- Notion limits **2000 characters** per `text.content` field
- Long content: use `NOTION_ADD_MULTIPLE_PAGE_CONTENT` (auto-splits) or append via `NOTION_APPEND_TEXT_BLOCKS` etc.
- **Deprecated:** `NOTION_APPEND_BLOCK_CHILDREN` — use typed append tools (`NOTION_APPEND_TEXT_BLOCKS`, `NOTION_APPEND_CODE_BLOCKS`, …)
- Do not use block types `child_page` / `child_database` in content blocks — use `NOTION_CREATE_NOTION_PAGE` / `NOTION_CREATE_DATABASE`
- `NOTION_REPLACE_PAGE_CONTENT` replaces existing body — confirm with user

Simplified block shape (many append tools):

```json
{ "content": "Hello", "block_property": "paragraph" }
```

`block_property` examples: `paragraph`, `heading_1`, `heading_2`, `heading_3`, `bulleted_list_item`, `numbered_list_item`, `to_do`, `quote`, `callout`, `divider`.

---

## 5. Workspace and archive limits

- **Workspace root pages** (no parent page/database) often **cannot be archived** via API — only nested pages
- Linked database views are not supported for some fetch paths — use source `database_id`

---

## 6. Tool execution checklist

When `successful: false`:

1. Read `error` in response
2. Verify `connected_account_id` status is `ACTIVE` (`GET /connected_accounts?toolkit_slugs=notion`)
3. Re-fetch `GET /tools/{tool_slug}` and fix `arguments`
4. Re-check ID type (page vs database)
5. Confirm integration sharing on target resource
6. For token issues: `POST /connected_accounts/{nanoid}/refresh` or new OAuth link (`workflow_connect.md`)

**Error 1811:** missing `user_id` / `connected_account_id` on execute — use same `user_id` as OAuth link.

---

## 7. Auth modes for Notion

| Mode | When |
|------|------|
| OAuth2 (gateway-managed) | Default; `POST /connected_accounts/link` |
| API Key | `POST /connected_accounts` with `generic_api_key` — see `workflow_connect.md` |

Comment triggers may require **Read comments** capability; connections created before enabling it may need **re-authorization**.

---

## 8. Non-ASCII / Chinese property names — encoding bug
