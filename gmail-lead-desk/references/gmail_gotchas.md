# Gmail API Gotchas

Rules agents must follow to avoid silent failures, `Invalid id value`, and irreversible mistakes.

Source: Gmail toolkit reference and AISA execute experience.

---

## ID types — never mix

| ID | Format | Used by | How to obtain |
|----|--------|---------|---------------|
| `message_id` / `messageId` | 15–16 char **hex** (e.g. `19b11732c1b578fd`) | `GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID`, batch modify, delete | `GMAIL_FETCH_EMAILS` response `messageId` |
| `thread_id` | Hex string | `GMAIL_FETCH_MESSAGE_BY_THREAD_ID`, reply/draft in thread | Same fetch/list responses `threadId` |
| `draft_id` | Often `r…` prefix (e.g. `r99885592323229922`) | `GMAIL_SEND_DRAFT`, `GMAIL_GET_DRAFT`, `GMAIL_DELETE_DRAFT` | `GMAIL_LIST_DRAFTS`, `GMAIL_CREATE_EMAIL_DRAFT` |
| `label_id` | System: `INBOX`, `UNREAD`, … Custom: `Label_N` | All label modify tools | `GMAIL_LIST_LABELS` → field `id` |
| `filter_id` | From filter APIs | Delete/get filter only | `GMAIL_LIST_FILTERS` |

**Invalid (will error or no-op):**

- UUIDs (32-char), internal CRM IDs, email subjects, dates
- Using `thread_id` where `message_id` is required
- Using `draft_id` in `GMAIL_BATCH_DELETE_MESSAGES`

Legacy Gmail web UI thread IDs (long alphanumeric bundles) are **not** supported — use API `thread_id` from fetch/list.

---

## Labels — display name ≠ ID

- Tools such as `GMAIL_BATCH_MODIFY_MESSAGES` require **label IDs**, not Chinese/English display names.
- Calling with `"deal-closed"` instead of `"Label_42"` → silent failure or API error.
- **Always** run `GMAIL_LIST_LABELS` before modify; refresh IDs if you get conflict errors.
- Gmail search box accepts `label:DisplayName`, but **tool `query` / `labelIds` parameters need IDs** for custom labels.
- System labels are case-sensitive: `INBOX`, `UNREAD`, `CATEGORY_PROMOTIONS`, etc.
- `INBOX`, `SPAM`, `TRASH` are read-only for some modify operations — check toolkit docs before remove.

---

## Threading and replies

- **`GMAIL_CREATE_EMAIL_DRAFT` / reply with `thread_id`:** leave **`subject` empty** to stay in the same thread. Setting a new subject starts a **new thread**.
- Prefer `GMAIL_REPLY_TO_THREAD` for in-thread sales replies.
- For new outbound (not a reply), use `GMAIL_SEND_EMAIL` or draft without `thread_id`.

---

## Draft vs send

| Tool | Behavior |
|------|----------|
| `GMAIL_CREATE_EMAIL_DRAFT` | Creates draft; reversible |
| `GMAIL_REPLY_TO_THREAD` | Creates draft reply in thread |
| `GMAIL_SEND_DRAFT` | Sends **as-is** — cannot add/change To/Cc/Bcc |
| `GMAIL_SEND_EMAIL` | Immediate send — **irreversible** |

**Sales default:** stop after draft unless user explicitly requests send.

`GMAIL_SEND_DRAFT` requires recipients already on the draft. If missing, recreate draft with `recipient_email` / cc / bcc or use `GMAIL_SEND_EMAIL`.

**No scheduled send** in the Gmail toolkit — schedule externally if needed.

---

## Fetch and search

- Use **`GMAIL_FETCH_EMAILS`** — `GMAIL_LIST_MESSAGES` is **deprecated**.
- `GMAIL_FETCH_EMAILS` results are **not** guaranteed sorted by date — sort by `internalDate` when showing "oldest first".
- `messages` may be absent or empty — valid zero-result state.
- Large mailboxes: `include_payload: false` first, then hydrate selected threads/messages.
- Body in payload is **base64url** in `payload.parts` — decode with URL-safe base64 rules.

Default sales noise filter:

```text
-category:promotions -category:social
```

---

## Rate limits and batching

- Gmail may return **429** `rateLimitExceeded` or **403** `userRateLimitExceeded`.
- High-volume: cap concurrent thread fetches at **~10**; exponential backoff **1s → 2s → 4s**.
- `GMAIL_BATCH_MODIFY_MESSAGES`: max **1000** `messageIds` per request.
- `GMAIL_BATCH_DELETE_MESSAGES`: permanent, no trash — **MVP disabled** in gmail-lead-desk unless user explicitly requests cleanup with confirmation.

---

## Attachments

- `attachment_id` is an internal token (e.g. `ANGjdJ8s…`), **not** the filename.
- Get IDs from `attachmentList` on a **full** message payload (`GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID` with full format).
- Message size limit ~**25 MB** after encoding for send.

---

## Triggers (future)

- `GMAIL_NEW_GMAIL_MESSAGE` and `GMAIL_EMAIL_SENT_TRIGGER` are **poll**-based (~1 min default).
- Not used in gmail-lead-desk MVP; document for proactive extensions only.

---

## Send quotas

- Personal Gmail: ~**500** recipients/day; Workspace higher (~2000/day).
- Bulk Bcc campaigns are out of scope for this skill.

---

## Quick diagnostic table

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Invalid id value | Wrong ID type | Re-fetch from `GMAIL_FETCH_EMAILS` |
| Label not applied | Used display name | `GMAIL_LIST_LABELS` → use `id` |
| Reply in new thread | Subject set on draft | Empty subject + `thread_id` |
| Send draft no recipients | Draft missing To | Recreate draft or `GMAIL_SEND_EMAIL` |
| Empty tool result | Wrong query/label ID in search | Fix query; list labels |
| 429 | Too many parallel calls | Backoff, reduce batch |
