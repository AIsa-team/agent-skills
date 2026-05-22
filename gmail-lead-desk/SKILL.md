---
name: gmail-lead-desk
description: 'Gmail Lead Desk — standalone sales/CS Gmail skill via the AISA gateway: OAuth connect, scan unread leads, summarize threads, draft template replies (default draft-only), archive with labels. Keywords: Gmail Lead Desk, Gmail, lead desk, sales, customer support, follow-up, unread, inquiry summary, draft reply, archive, OAuth, AISA, connected account, thread_id'
homepage: https://aisa.one
license: MIT
compatibility: "Standalone skill. Requires curl and AISA_API_KEY. On-demand (no triggers in MVP)."
metadata:
  aisa:
    emoji: 📧
    homepage: https://aisa.one
    requires:
      bins:
      - curl
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---

# Gmail Lead Desk (`gmail-lead-desk`) 📧

**Gmail Lead Desk** — standalone sales and customer-support Gmail workflows via the AISA gateway.

One skill: connect Gmail, run whitelisted tools, triage inbox, draft replies, archive deals — no other skill required.

## Quick start

```bash
export AISA_API_KEY="your-key"   # get at https://aisa.one
```

> **Pre-flight checks (do first, stop if fails):**
> 1. `AISA_API_KEY` is set — if not, ask the user to set it before any API call.
> 2. `user_id` is known — use the Gmail address the user provides. If not yet known, ask: "What Gmail address should I use as your identity?"
> 3. Gmail is `ACTIVE` — run Workflow 0 if `connected_account_id` is missing or not `ACTIVE`.

- **Base URL:** `https://api.aisa.one`
- **Auth:** `Authorization: Bearer $AISA_API_KEY`
- **Windows:** use `curl.exe`

OAuth and `tools/execute`: [`references/connect_and_execute.md`](./references/connect_and_execute.md)

## When to use

- Connect or reconnect **Gmail** via OAuth
- Scan **unread leads** needing follow-up
- **Summarize** inquiry/support threads (CRM format)
- **Draft** replies from sales templates (default: do not send)
- **Archive** won deals with labels
- User mentions: unanswered, follow-up, inquiry, quote, draft, archive, lead, connect Gmail

## When NOT to use

- Non-Gmail apps (Slack, GitHub, etc.) — out of scope
- Proactive new-mail automation — not MVP; see `references/workflows.md` § Future
- Bulk permanent delete, filter creation — disabled unless user explicitly requests

## Intent → Workflow Quick Reference

| User intent | Workflow | Reference |
|-------------|----------|-----------|
| Connect Gmail / OAuth / authorize | **0** Connect Gmail | `references/connect_and_execute.md` |
| Unanswered / follow-up / unread | **A** Unread lead scan | `references/workflows.md` § A |
| Summarize / summary / summarize thread | **B** Thread summary | `references/workflows.md` § B |
| Reply for me / draft reply / write email | **C** Draft (no send) | `references/workflows.md` § C |
| Confirm send / send now | **C-send** Send after confirm | `references/workflows.md` § C-send |
| Archive / deal closed | **D** Label and archive | `references/workflows.md` § D |

> Run **Workflow 0** first if Gmail is not connected (`ACTIVE` `connected_account_id`).

---

## Workflow 0 — Connect Gmail (summary)

1. `GET /auth_configs?toolkit_slug=gmail` → `auth_config_id`
2. `GET /connected_accounts?toolkit_slugs=gmail&user_ids={user_id}` — reuse `ACTIVE` if present
3. Else **confirm**, then `POST /connected_accounts/link` → user opens `redirect_url`
4. Poll every 3–5 s until `status` is `ACTIVE`; save `connected_account_id`
   - **Timeout after ~2 min (24 polls):** stop polling, tell user "OAuth not completed — please try again or check the browser tab."
   - `DISCONNECTED` / `REVOKED`: re-run from step 3.

Full steps: [`references/connect_and_execute.md`](./references/connect_and_execute.md)

---

## Core Workflows (summary)

### A — Unread lead scan

1. Resolve `connected_account_id` (Workflow 0).
2. `GMAIL_FETCH_EMAILS` with sales default query — see `workflows.md`.
3. Table: **Sender | Subject | Days waiting | thread_id | Suggested action**.
4. **Do not send** at end of this workflow.

### B — Thread summary (CRM-ready)

1. `GMAIL_FETCH_MESSAGE_BY_THREAD_ID`; sort by `internalDate`.
2. Fixed sections: customer, need, budget/timeline, next action, attachments (**unverified** when inferred).

### C — Template draft (default: no send)

1. Load thread (B); confirm recipient, tone, quote/link.
2. `GMAIL_REPLY_TO_THREAD` or `GMAIL_CREATE_EMAIL_DRAFT`; **empty subject** when `thread_id` set.
3. Return `draft_id` + preview.

### C-send — Send only on explicit request

- User says **send / confirm send / send now**.
- Show full To/Cc/subject/body; confirm; then `GMAIL_SEND_DRAFT` or `GMAIL_SEND_EMAIL`.

### D — Archive and label

1. `GMAIL_LIST_LABELS` → `Label_*` IDs only.
2. `GMAIL_CREATE_LABEL` if needed (confirm).
3. Sample ≤5 `messageIds` + count → `GMAIL_BATCH_MODIFY_MESSAGES`.

**Never guess `tool_slug`.** Whitelist: [`references/tool_whitelist.md`](./references/tool_whitelist.md).

---

## Safety

| Action | Rule |
|--------|------|
| Default after A/B/C | **Draft only** — no auto-send |
| OAuth link / create auth config | Confirm with user |
| Create draft | Confirm recipient and thread |
| Send | Explicit user request + show To/Cc |
| Batch label/archive | ≤5 sample IDs + total count |
| Batch delete / filters | **Refuse** in MVP unless explicit cleanup request |
| Privacy | No uploading full mailbox externally; attachments need consent |
| Rate limits | Concurrency ≤10; backoff on 429 |

Gmail pitfalls: [`references/gmail_gotchas.md`](./references/gmail_gotchas.md).

---

## Reference routing

| Need | File |
|------|------|
| API key, OAuth, execute | `references/connect_and_execute.md` |
| Sales workflows A–D | `references/workflows.md` |
| message_id, labels, drafts | `references/gmail_gotchas.md` |
| Allowed tool slugs | `references/tool_whitelist.md` |

**Lookup order:** intent → Workflow 0 if needed → `workflows.md` → `tool_whitelist.md` → `GET /tools/{tool_slug}` → `POST /tools/execute/{tool_slug}`.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `AISA_API_KEY` not set | Ask user to run `export AISA_API_KEY="..."` before any API call |
| `user_id` unknown | Ask "What Gmail address should I use as your identity?" |
| No Gmail connection | Workflow 0 in `connect_and_execute.md` |
| OAuth poll timeout (>2 min) | Tell user to check browser tab; re-run Workflow 0 step 3 |
| `Invalid id value` | See `gmail_gotchas.md` |
| Label not applied | Used display name — `GMAIL_LIST_LABELS` for `id` |
| New thread on reply | Subject set on draft — leave subject empty |
| `successful: false` | `connect_and_execute.md` §4 + re-fetch tool schema |
| Deprecated `GMAIL_LIST_MESSAGES` | Use `GMAIL_FETCH_EMAILS` |
