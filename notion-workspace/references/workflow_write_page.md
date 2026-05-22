# Workflow: Write Notion pages and blocks

**Prerequisite:** `connected_account_id` + `user_id` — see `workflow_connect.md`.

**Confirm with user** before any execute that creates or modifies Notion content.

**Base:** `https://api.aisa.one` | **Header:** `Authorization: Bearer $AISA_API_KEY`

---

## Before every write

1. `GET /tools/{tool_slug}` — read `input_parameters.required` and `properties`
2. Never guess `tool_slug` — see `notion_intent_to_tool.md`
3. `POST /tools/execute/{tool_slug}` with `connected_account_id`, `user_id`, `arguments`
4. Verify `successful` in response

---

## Create a new page

**Tool:** `NOTION_CREATE_NOTION_PAGE`

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_CREATE_NOTION_PAGE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "parent_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "title": "New page title"
    }
  }'
```

`parent_id` is typically a page or database parent — check schema for allowed parent types.

Save returned page `id` for follow-up content calls.

---

## Add content to an existing page

### Multiple blocks (recommended for long/markdown text)

**Tool:** `NOTION_ADD_MULTIPLE_PAGE_CONTENT`

- Auto-splits text over **2000** characters per Notion limit
- Supports markdown: bold, italic, code, links
- Up to **100** blocks per call

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_ADD_MULTIPLE_PAGE_CONTENT" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": {
      "parent_block_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "content_blocks": [
        { "content": "## Summary", "block_property": "heading_2" },
        { "content": "First paragraph.", "block_property": "paragraph" },
        { "content": "Task item", "block_property": "to_do" }
      ]
    }
  }'
```

> **Parameter note:** The target page/block is `parent_block_id`, **not** `page_id`. Using `page_id` will return a missing-field error. Always verify via `GET /tools/NOTION_ADD_MULTIPLE_PAGE_CONTENT`.

### Single block

**Tool:** `NOTION_ADD_PAGE_CONTENT`

---

## Append typed blocks

Prefer specialized append tools over deprecated `NOTION_APPEND_BLOCK_CHILDREN`:

| Intent | Tool |
|--------|------|
| Paragraphs, headings, lists | `NOTION_APPEND_TEXT_BLOCKS` |
| To-do items | `NOTION_APPEND_TASK_BLOCKS` |
| Code | `NOTION_APPEND_CODE_BLOCKS` |
| Images, video, PDF | `NOTION_APPEND_MEDIA_BLOCKS` |
| Divider, columns | `NOTION_APPEND_LAYOUT_BLOCKS` |
| Tables | `NOTION_APPEND_TABLE_BLOCKS` |

Simplified block shape (verify per tool schema):

```json
{ "content": "Text here", "block_property": "paragraph" }
```

Each append call needs `block_id` (parent page or block UUID).

---

## Replace entire page body

**Tool:** `NOTION_REPLACE_PAGE_CONTENT`

**Destructive** — replaces existing content. Extra user confirmation recommended.

---

## Update or remove blocks

| Action | Tool |
|--------|------|
| Update block | `NOTION_UPDATE_BLOCK` |
| Delete (archive) block | `NOTION_DELETE_BLOCK` |
| Archive whole page | `NOTION_ARCHIVE_NOTION_PAGE` |
| Duplicate page | `NOTION_DUPLICATE_PAGE` |

Workspace-level root pages often cannot be archived via API — see `notion_gotchas.md`.

---

## Natural language arguments (optional)

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_CREATE_NOTION_PAGE/input" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "text": "Create a page titled Weekly Notes under parent page X" }'
```

If error `1010`, build `arguments` manually from `GET /tools/{tool_slug}`.

---

## Write flow summary

```text
New page → NOTION_CREATE_NOTION_PAGE
Add body → NOTION_ADD_MULTIPLE_PAGE_CONTENT (or NOTION_APPEND_* )
Replace all → NOTION_REPLACE_PAGE_CONTENT (confirm)
```

Database rows: use `workflow_database.md`, not page content tools.
