# Gmail Lead Desk

**Gmail Lead Desk** — standalone sales and customer-support Gmail workflows via the AISA gateway. Does not require any other agent skill.

## Prerequisites

- `AISA_API_KEY` from [aisa.one](https://aisa.one)
- `curl` (use `curl.exe` on Windows PowerShell)

## Contents

| File | Purpose |
|------|---------|
| [SKILL.md](./SKILL.md) | Agent entry: Workflow 0 + A–D, safety |
| [references/connect_and_execute.md](./references/connect_and_execute.md) | API key, Gmail OAuth, tool execute |
| [references/workflows.md](./references/workflows.md) | Sales workflows and query templates |
| [references/gmail_gotchas.md](./references/gmail_gotchas.md) | Gmail ID, label, draft pitfalls |
| [references/tool_whitelist.md](./references/tool_whitelist.md) | MVP-allowed `GMAIL_*` slugs |

## Workflows

- **0** — Connect Gmail (OAuth)
- **A** — Unread lead scan
- **B** — Thread summary (CRM format)
- **C** — Draft reply (default: no send)
- **D** — Label and archive won deals

## Links

- [Gmail toolkit reference](https://docs.composio.dev/toolkits/gmail)
- [AISA](https://aisa.one)
