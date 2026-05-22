# Gmail Tool Whitelist (MVP)

Only these `tool_slug` values may be used by **gmail-lead-desk**. For any other Gmail tool, ask the user and default to **refuse** unless they explicitly need advanced mailbox admin.

**Schema:** `GET https://api.aisa.one/apis/v1/composio/tools/{tool_slug}`  
**Execute:** `POST https://api.aisa.one/apis/v1/composio/tools/execute/{tool_slug}` — see [`connect_and_execute.md`](./connect_and_execute.md).

---

## Read

GET/list calls do not require user confirmation unless the user asked to avoid network calls.

| Slug | Purpose in gmail-lead-desk |
|------|------------------------|
| `GMAIL_FETCH_EMAILS` | Inbox/unread lead scan (Workflow A) |
| `GMAIL_FETCH_MESSAGE_BY_THREAD_ID` | Thread timeline (B, C) |
| `GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID` | Single message / full payload for attachments |
| `GMAIL_LIST_THREADS` | Alternative thread discovery |
| `GMAIL_LIST_LABELS` | **Required** before any label modify (D) |
| `GMAIL_GET_ATTACHMENT` | Download attachment after user consent (B) |
| `GMAIL_GET_PROFILE` | Confirm mailbox identity / connectivity |
| `GMAIL_LIST_DRAFTS` | Find `draft_id` before send |
| `GMAIL_GET_DRAFT` | Inspect draft before `GMAIL_SEND_DRAFT` |

---

## Write (confirm with user — draft-first rules in SKILL.md)

| Slug | Purpose | Rule |
|------|---------|------|
| `GMAIL_CREATE_EMAIL_DRAFT` | New draft / reply body | Default for Workflow C |
| `GMAIL_REPLY_TO_THREAD` | Reply draft in thread | Preferred for Workflow C |
| `GMAIL_SEND_DRAFT` | Send existing draft | Workflow C-send only |
| `GMAIL_SEND_EMAIL` | Send new mail immediately | C-send only; double confirm |
| `GMAIL_CREATE_LABEL` | Create e.g. `deal-closed` | Workflow D; confirm name |
| `GMAIL_BATCH_MODIFY_MESSAGES` | Archive + label batch | Workflow D; show samples |
| `GMAIL_ADD_LABEL_TO_EMAIL` | Single-message label | When batch not needed |

---

## Explicitly disabled in MVP

Do **not** call unless the user explicitly requests destructive or advanced admin and confirms risks:

| Slug | Reason |
|------|--------|
| `GMAIL_BATCH_DELETE_MESSAGES` | Permanent delete |
| `GMAIL_DELETE_MESSAGE` | Permanent delete |
| `GMAIL_DELETE_THREAD` | Permanent delete |
| `GMAIL_DELETE_DRAFT` | Only if user asks to discard draft |
| `GMAIL_DELETE_LABEL` | Label removal from account |
| `GMAIL_DELETE_FILTER` | Filter admin |
| `GMAIL_CREATE_FILTER` | Easy to misconfigure automation |
| `GMAIL_MOVE_TO_TRASH` | Cleanup — confirm separately |
| `GMAIL_LIST_MESSAGES` | **Deprecated** — use `GMAIL_FETCH_EMAILS` |

All other `GMAIL_*` tools (settings, forwarding, CSE, import, etc.) are out of scope for this skill unless the user explicitly requests and accepts the risk.

---

## Triggers (future — not MVP)

| Slug | Type |
|------|------|
| `GMAIL_NEW_GMAIL_MESSAGE` | poll — new inbound |
| `GMAIL_EMAIL_SENT_TRIGGER` | poll — sent mail |

Configure via AISA `trigger_instances` APIs when enabling proactive mode.

---

## Deprecated alias

| Do not use | Use instead |
|------------|-------------|
| `GMAIL_LIST_MESSAGES` | `GMAIL_FETCH_EMAILS` |
