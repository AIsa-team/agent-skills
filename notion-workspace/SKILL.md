---
name: notion-workspace
description: 'Manage Notion workspace: search pages and databases, read markdown, create pages, insert rows, triggers, MCP. Powered by AISA gateway (Notion toolkit). Requires AISA_API_KEY and curl. Keywords: notion, workspace, page, database, block, markdown, wiki, task board, insert row, OAuth'
homepage: https://aisa.one
license: MIT
compatibility: "Standalone skill. Requires curl and AISA_API_KEY. Works with any agentic harness that supports shell execution (Qoder, VS Code agents, etc.)."
metadata:
  aisa:
    emoji: 📝
    homepage: https://aisa.one
    requires:
      bins:
      - curl
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# Notion Workspace (`notion-workspace`)

**Standalone** skill for Notion pages, databases, and workspace automation via AISA. No other skill required.

Covers: OAuth connect, tool discovery/execute, Notion ID rules, triggers, and MCP for Notion only.

## Quick Start

```bash
export AISA_API_KEY="your-key"   # Linux/macOS
# $env:AISA_API_KEY = "your-key"  # Windows PowerShell
```

- **Base URL:** `https://api.aisa.one`
- **Path prefix:** `/apis/v1/composio/...`
- **Toolkit slug:** `notion`
- **Header:** `Authorization: Bearer $AISA_API_KEY`

**Windows:** Use `curl.exe` in PowerShell.

HTTP patterns (session, OAuth, execute, triggers): `references/api_basics.md`

## When to use

- Search, read, or write Notion pages and databases
- Connect a user/workspace to Notion (OAuth or API key)
- Insert or update database rows, append page content, export Markdown
- Notion triggers, webhooks, or Notion-only MCP server

## When NOT to use

- No `AISA_API_KEY` — get one at [aisa.one](https://aisa.one)
- Direct upstream provider endpoints without the AISA gateway
- Official Notion API only (no AISA gateway)
- Other toolkits (GitHub, Slack, Gmail, etc.) — use a different skill

## What Can You Do?

```text
"Connect user alice to Notion via OAuth"
"Search for pages titled Roadmap and export Markdown"
"Add a row to my Tasks database with status In Progress"
"Create a child page under X and append bullet content"
"Set up a trigger when a new row is added to database Y"
```

## Intent → Workflow

| User intent | Read this |
|-------------|-----------|
| API key / session / generic curl | `references/api_basics.md` |
| connect / OAuth / authorize Notion | `references/workflow_connect.md` |
| search / find page or database | `references/workflow_read.md` § Search |
| read markdown / page content / blocks | `references/workflow_read.md` § Content |
| query database / filter rows | `references/workflow_database.md` § Query |
| create page / write content / append blocks | `references/workflow_write_page.md` |
| insert row / update properties | `references/workflow_database.md` § Write |
| comments / file upload | `references/notion_intent_to_tool.md` |
| page updated / trigger / webhook / MCP | `references/notion_triggers.md` |
| errors / 404 / wrong ID type | `references/notion_gotchas.md` |
| non-ASCII / Chinese field names / mojibake | `references/notion_gotchas.md` § 8 |
| which tool slug? | `references/notion_intent_to_tool.md` |

> Unclear intent: `GET auth/session/info`, ensure `connected_account_id` (N1), then ask read vs write.

---

## Core Workflows

### N1 — Connect Notion

1. `GET /auth_configs?toolkit_slug=notion` → `auth_config_id`
2. **Confirm with user** → `POST /connected_accounts/link` with `user_id`
3. User opens `redirect_url` in browser
4. Poll `GET /connected_accounts?user_ids={user_id}&toolkit_slugs=notion` every 3–5s until `ACTIVE` (~2 min max)
5. Save `items[].id` as `connected_account_id`

If `ACTIVE` already exists for same `user_id` + `notion`, reuse it.

Details: `references/workflow_connect.md`

### N2 — Discover and read

1. Resolve `connected_account_id` (N1 if missing)
2. Discover IDs: `NOTION_SEARCH_NOTION_PAGE` or `NOTION_FETCH_DATA`
3. Read page: `NOTION_GET_PAGE_MARKDOWN` or `NOTION_FETCH_BLOCK_CONTENTS`
4. Read database: `NOTION_FETCH_DATABASE` → `NOTION_QUERY_DATABASE` or `NOTION_QUERY_DATABASE_WITH_FILTER`

Details: `references/workflow_read.md`

### N3 — Write pages and blocks

1. Resolve `connected_account_id` (N1 if missing)
2. `GET /tools/{tool_slug}` — **never guess slug**; see `references/notion_intent_to_tool.md`
3. **Confirm with user** before any write
4. Create page: `NOTION_CREATE_NOTION_PAGE` (`parent_id`, `title`) → save returned `id`
5. Add body: `NOTION_ADD_MULTIPLE_PAGE_CONTENT` (`parent_block_id`, `content_blocks[]`)
6. Check `successful` in response; on false read `error`

> Key param: `NOTION_ADD_MULTIPLE_PAGE_CONTENT` uses `parent_block_id` (not `page_id`) and `content_blocks` (not `child_blocks`).

Details: `references/workflow_write_page.md`

### N4 — Database rows

1. **Check sharing**: Confirm the target database (and its parent page chain up to workspace root) is shared with the AISA integration in Notion UI (⋯ → Connections). A 404 on execute almost always means the integration cannot see the resource.
2. **Always** `NOTION_FETCH_DATABASE` first
3. **Confirm with user** → `NOTION_INSERT_ROW_DATABASE` (`properties` as list of `{name, type, value}`)
4. Update: `NOTION_UPDATE_PAGE`; filter: `NOTION_QUERY_DATABASE_WITH_FILTER`

Details: `references/workflow_database.md`

### N5 — Troubleshoot

`references/notion_gotchas.md` + `references/api_basics.md` Troubleshooting table.

---

## Execute pattern (all Notion tools)

```bash
curl -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/NOTION_SEARCH_NOTION_PAGE" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "alice@example.com",
    "arguments": { }
  }'
```

Schema: `GET /tools/{tool_slug}` → `input_parameters`.  
List tools: `GET /tools?toolkit_slug=notion&limit=50`

---

## Safety

- **Confirm** before POST that writes to Notion or changes triggers/webhooks/MCP
- Read-only GET/list/search need no confirmation unless user forbids network
- OAuth `redirect_url` must be opened by a human
- Never use mock IDs (`test_nanoid_001`)

---

## Reference routing

| Topic | File |
|-------|------|
| Gateway, OAuth, execute, triggers HTTP | `references/api_basics.md` |
| Notion pitfalls | `references/notion_gotchas.md` |
| Intent → tool_slug | `references/notion_intent_to_tool.md` |
| Connect | `references/workflow_connect.md` |
| Read / search | `references/workflow_read.md` |
| Write pages | `references/workflow_write_page.md` |
| Database | `references/workflow_database.md` |
| Triggers, MCP | `references/notion_triggers.md` |
