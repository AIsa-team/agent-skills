# Notion Workspace

**Standalone** [Agent Skill](https://agentskills.io) for managing a **Notion workspace** (pages, databases, content, triggers) via AISA gateway.

## Requires

- `AISA_API_KEY` from [aisa.one](https://aisa.one)
- `curl` (use `curl.exe` on Windows PowerShell)

## Contents

| File | Purpose |
|------|---------|
| [SKILL.md](./SKILL.md) | Agent entry: workflows N1–N5, intent routing |
| [references/api_basics.md](./references/api_basics.md) | Gateway, OAuth, execute, triggers |
| [references/notion_gotchas.md](./references/notion_gotchas.md) | Notion-specific pitfalls |
| [references/notion_intent_to_tool.md](./references/notion_intent_to_tool.md) | Intent → tool_slug |
| [references/workflow_*.md](./references/) | Connect, read, write, database |
| [references/notion_triggers.md](./references/notion_triggers.md) | Triggers + MCP |

## Related docs

- [AISA](https://aisa.one) — gateway homepage & API key issuance
- [Notion API](https://developers.notion.com/) — upstream reference for IDs, property types, and limits
