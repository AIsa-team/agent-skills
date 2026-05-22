# SaaS Gateway

Unified **SaaS integration gateway (v3.1)** through AISA (`https://api.aisa.one`, path prefix `/apis/v1/composio/` is a literal AISA gateway route). One API key to connect and operate third-party SaaS apps (Gmail / Slack / GitHub / Notion / etc.).

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others that implement the [Agent Skills specification](https://agentskills.io/specification).

Requires `curl` and `AISA_API_KEY`.

## Prerequisites

```bash
export AISA_API_KEY="your-aisa-api-key"
```

## Contents

| File | Purpose |
|------|---------|
| [SKILL.md](./SKILL.md) | Agent skill specification |
| [references/auth_and_session.md](./references/auth_and_session.md) | Session and auth configs |
| [references/connect_account.md](./references/connect_account.md) | Connected accounts and OAuth link |
| [references/execute_tools.md](./references/execute_tools.md) | Toolkits, tools, tool router |
| [references/triggers_webhooks.md](./references/triggers_webhooks.md) | Triggers and webhooks |
| [references/endpoint_catalog.md](./references/endpoint_catalog.md) | Full API index (95 operations) |

## Links

- [AISA](https://aisa.one) — gateway provider
- Underlying upstream API docs are referenced inside each `references/*.md` only when needed for field semantics; all request URLs go through `api.aisa.one`.
