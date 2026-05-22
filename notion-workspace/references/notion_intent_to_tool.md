# Notion intent → tool_slug

**Toolkit slug:** `notion` | **Never guess slugs** — confirm with `GET /tools/{tool_slug}` before execute.

Base execute path: `POST /apis/v1/composio/tools/execute/{tool_slug}`

---

## Search and discovery

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Search pages/databases by title or filter | `NOTION_SEARCH_NOTION_PAGE` | Use `filter_value`: `page`, `database`, etc. |
| List pages, databases, or mixed data | `NOTION_FETCH_DATA` | `fetch_type` controls scope |
| Who am I / workspace bot user | `NOTION_GET_ABOUT_ME` | |
| List workspace users | `NOTION_LIST_USERS` | |
| Get another user's profile | `NOTION_GET_ABOUT_USER` | |

---

## Read pages and content

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Export page as Markdown | `NOTION_GET_PAGE_MARKDOWN` | Preferred for reading full page text |
| Get page metadata/properties | `NOTION_RETRIEVE_PAGE` | Not full body; use block tools for content |
| List child blocks | `NOTION_FETCH_BLOCK_CONTENTS` | Requires `block_id` (page ID OK) |
| Fetch all block content from URL | `NOTION_FETCH_ALL_BLOCK_CONTENTS` | `page_url` or `block_id`; no database view URLs with `?v=` |
| Block metadata only | `NOTION_FETCH_BLOCK_METADATA` | |
| Get one page property (25+ refs) | `NOTION_GET_PAGE_PROPERTY_ACTION` | |

---

## Databases — schema and query

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Get database schema | `NOTION_FETCH_DATABASE` | **Required before insert row** |
| Query all rows (simple) | `NOTION_QUERY_DATABASE` | `database_id` only — not page_id |
| Query with filters/sorts | `NOTION_QUERY_DATABASE_WITH_FILTER` | Call `NOTION_FETCH_DATABASE` first for property types |
| Query data source (v3 API) | `NOTION_QUERY_DATA_SOURCE` | When working with data sources |
| Get one row (page) | `NOTION_FETCH_ROW` | Row = page in Notion |
| Database property definition | `NOTION_RETRIEVE_DATABASE_PROPERTY` | |
| List data source templates | `NOTION_LIST_DATA_SOURCE_TEMPLATES` | |

---

## Databases — write

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Insert row | `NOTION_INSERT_ROW_DATABASE` | `properties` = list of `{name,type,value}` |
| Upsert row | `NOTION_UPSERT_ROW_DATABASE` | Insert or update by match |
| Update row (database) | `NOTION_UPDATE_ROW_DATABASE` | |
| Insert row from natural language | `NOTION_INSERT_ROW_FROM_NL` | May fail on restricted tiers; fallback manual properties |
| Update page/row properties | `NOTION_UPDATE_PAGE` | |
| Update database schema | `NOTION_UPDATE_SCHEMA_DATABASE` | Confirm with user |
| Create database under a page | `NOTION_CREATE_DATABASE` | `parent_id` must be **page_id** |
| Move page to new parent | `NOTION_MOVE_PAGE` | Use `data_source_id` when moving into DB |

---

## Write pages and blocks

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Create new page | `NOTION_CREATE_NOTION_PAGE` | |
| Add content (auto-split long text) | `NOTION_ADD_MULTIPLE_PAGE_CONTENT` | Max 100 blocks; markdown supported |
| Add single content block | `NOTION_ADD_PAGE_CONTENT` | |
| Replace entire page body | `NOTION_REPLACE_PAGE_CONTENT` | Destructive — confirm |
| Append text blocks | `NOTION_APPEND_TEXT_BLOCKS` | |
| Append tasks (to-do) | `NOTION_APPEND_TASK_BLOCKS` | |
| Append code | `NOTION_APPEND_CODE_BLOCKS` | |
| Append media (image/video/pdf) | `NOTION_APPEND_MEDIA_BLOCKS` | |
| Append layout (divider, columns) | `NOTION_APPEND_LAYOUT_BLOCKS` | |
| Append table | `NOTION_APPEND_TABLE_BLOCKS` | |
| Update a block | `NOTION_UPDATE_BLOCK` | |
| Delete (archive) block | `NOTION_DELETE_BLOCK` | |
| Archive page | `NOTION_ARCHIVE_NOTION_PAGE` | Not workspace root pages |
| Duplicate page | `NOTION_DUPLICATE_PAGE` | |

---

## Comments

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Create comment | `NOTION_CREATE_COMMENT` | |
| List comments on page/block | `NOTION_FETCH_COMMENTS` | Page must be shared; may need re-auth for comment scope |
| Get single comment | `NOTION_RETRIEVE_COMMENT` | |

---

## Files

| User intent | tool_slug | Notes |
|-------------|-----------|-------|
| Request upload URL | `NOTION_CREATE_FILE_UPLOAD` | Then upload to presigned URL |
| Send/upload file bytes | `NOTION_SEND_FILE_UPLOAD` | |
| List uploads | `NOTION_LIST_FILE_UPLOADS` | |
| Retrieve upload status | `NOTION_RETRIEVE_FILE_UPLOAD` | |

---

## Avoid / deprecated

| Do not use | Use instead |
|------------|-------------|
| `NOTION_APPEND_BLOCK_CHILDREN` | `NOTION_APPEND_TEXT_BLOCKS`, `NOTION_APPEND_CODE_BLOCKS`, etc. |
| page_id in `NOTION_QUERY_DATABASE` | Resolve `database_id` via search/fetch |
| Guessed tool_slug | `GET /tools?toolkit_slug=notion` then `GET /tools/{slug}` |

---

## Discover all tools dynamically

```bash
curl "https://api.aisa.one/apis/v1/composio/tools?toolkit_slug=notion&limit=50" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Use `items[].slug` and paginate with `cursor` if needed.
