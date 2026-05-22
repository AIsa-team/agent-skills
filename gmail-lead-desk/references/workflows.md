# Gmail Lead Desk Workflows

Step-by-step Gmail operations for sales and customer support.

**Base:** `https://api.aisa.one`  
**Header:** `Authorization: Bearer $AISA_API_KEY`  
**Prerequisite:** `connected_account_id` for `gmail` — see [`connect_and_execute.md`](./connect_and_execute.md) (Workflow 0: OAuth + execute).

**Execute pattern (all workflows):**

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/{TOOL_SLUG}" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": { }
  }'
```

Always `GET /apis/v1/composio/tools/{TOOL_SLUG}` first if argument names are uncertain (`input_parameters`).

---

## Workflow A — Unread lead scan

**Goal:** List inbox threads that likely need a sales follow-up.

### Step 1 — Ensure Gmail is connected

```bash
curl "https://api.aisa.one/apis/v1/composio/connected_accounts?toolkit_slugs=gmail&user_ids=rep@company.com" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

Use `items[].id` where `status` is `ACTIVE`. If empty, run OAuth in `connect_and_execute.md` §1.

### Step 2 — Fetch unread inbox (metadata first)

Default sales query (excludes promo/social noise):

```text
in:inbox is:unread -category:promotions -category:social
```

Optional filters (ask user):

| Intent | Add to query |
|--------|----------------|
| Specific customer | `from:client@corp.com` |
| Older than 3 days | `older_than:3d` |
| Has attachment | `has:attachment` |
| Starred only | `is:starred` |

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_FETCH_EMAILS" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "query": "in:inbox is:unread -category:promotions -category:social",
      "max_results": 20,
      "include_payload": false
    }
  }'
```

**Notes:**

- Prefer `GMAIL_FETCH_EMAILS` — `GMAIL_LIST_MESSAGES` is deprecated.
- Results are not sorted by recency; sort by `internalDate` client-side when presenting.
- Null-check `messages` — empty is valid (no leads).

### Step 3 — Hydrate top threads (optional)

For the top 5–10 rows by age or importance, fetch full thread:

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_FETCH_MESSAGE_BY_THREAD_ID" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "thread_id": "19bf77729bcb3a44"
    }
  }'
```

### Step 4 — Present output table

| Sender | Subject | Days waiting | thread_id | Suggested action |
|--------|---------|--------------|-----------|------------------|
| ... | ... | N | hex id | Summarize (B) / Draft reply (C) / Archive (D) |

Compute **days waiting** from newest inbound message `internalDate` vs today.

**End state:** Do **not** call send tools. Offer next step: B, C, or D.

---

## Workflow B — Thread summary (CRM-ready)

**Goal:** Structured summary before replying or logging to CRM.

### Step 1 — Fetch thread

Use `thread_id` from Workflow A or user input.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_FETCH_MESSAGE_BY_THREAD_ID" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "thread_id": "19bf77729bcb3a44"
    }
  }'
```

Sort `messages` by `internalDate` ascending for timeline.

### Step 2 — Output template (fixed sections)

```markdown
## Opportunity Summary — {subject or "(no subject)"}

**thread_id:** {thread_id}

### Customer / Company
- {name or email from From header} (unverified if inferred from domain only)

### Requirements & Pain Points
- {bullet points from latest customer messages}

### Budget / Quantity / Timeline
- {values from email or "not provided"}

### Our Next Actions
- [ ] Quote / [ ] Sample / [ ] Meeting / [ ] Other: ___

### Timeline
| Date | Direction | Summary |
|------|-----------|---------|
| ... | Customer/Us | one line |

### Attachments
- {filename} (attachmentId: …) — download requires user confirmation → `GMAIL_GET_ATTACHMENT`

### Suggested Next Step
- Workflow C: draft reply / Workflow D: archive (if deal closed)
```

### Step 3 — Attachments (optional)

Only after user confirms download:

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_GET_ATTACHMENT" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "message_id": "19b11732c1b578fd",
      "attachment_id": "ANGjdJ8s..."
    }
  }'
```

Obtain `attachment_id` from `attachmentList` on a full-format message fetch (`GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID` with `format=full` if needed).

---

## Workflow C — Template draft (default: no send)

**Goal:** Create a reply draft for user review. **Never send** unless Workflow C-send.

### Step 1 — Load context

Run Workflow B on the same `thread_id`.

### Step 2 — Confirm with user

- Recipient(s) — default: last customer From address
- Tone: formal / brief
- Include: quote link / meeting link / attachment (file upload via `connect_and_execute.md` §5 if needed)

### Step 3 — Choose tool

| Situation | Tool |
|-----------|------|
| Reply in existing thread | `GMAIL_REPLY_TO_THREAD` (preferred) |
| New draft with full control | `GMAIL_CREATE_EMAIL_DRAFT` |

**Thread rule:** When `thread_id` is set, **leave `subject` empty** — setting subject creates a **new thread**.

Example — reply in thread:

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_REPLY_TO_THREAD" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "thread_id": "19bf77729bcb3a44",
      "message_body": "Hello, thank you for your inquiry...",
      "is_html": false
    }
  }'
```

Example — create draft:

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_CREATE_EMAIL_DRAFT" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "thread_id": "19bf77729bcb3a44",
      "recipient_email": "client@corp.com",
      "body": "Hello, thank you for your inquiry...",
      "is_html": false
    }
  }'
```

**Confirm with user before POST** (see SKILL.md Safety).

### Step 4 — Return to user

- `draft_id` from response
- Full draft body preview
- Message: "Please review in Gmail, then say 'confirm send' to have it sent on your behalf."

### Sales reply templates (placeholders — customize per team)

**First response to inquiry**

```text
Hi {customer name},

Thank you for your inquiry about {product/service}. We have received your requirements: {one-line summary of needs}.

I will prepare a formal quote and send it within {timeframe}. If you need it urgently or have specific requirements, please reply to this email.

Best regards,
{signature}
```

**Quote sent · Follow-up for feedback**

```text
Hi {customer name},

I wanted to follow up on the quote I sent last week (subject: {original subject}). Would it be possible to share your thoughts or questions this week so we can align on timing?

Thank you,
{signature}
```

**Meeting time proposal**

```text
Hi {customer name},

To align on requirements more efficiently, I'd like to schedule a 30-minute online call. My available time slots are:
- {slot 1}
- {slot 2}

Please let me know which time works for you, or suggest an alternative.

{signature}
```

**Polite decline / referral**

```text
Hi {customer name},

Thank you for reaching out. Unfortunately, we are currently unable to take on this type of request in {region/product line}. You may want to reach out to our partner {name} ({email}), or please feel free to contact us again if your requirements change.

Best wishes,
{signature}
```

---

## Workflow C-send — Send after explicit confirmation

**Trigger phrases:** confirm send, send now, go ahead and send

1. Show **To, Cc, Bcc, Subject, Body** in full.
2. User confirms once more.
3. If draft exists:

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_SEND_DRAFT" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "draft_id": "r99885592323229922"
    }
  }'
```

**Warning:** `GMAIL_SEND_DRAFT` sends to recipients **already on the draft** — it cannot add To/Cc. If draft has no recipients, use `GMAIL_SEND_EMAIL` or recreate draft with `GMAIL_CREATE_EMAIL_DRAFT`.

4. Check response `successful`; irreversible once sent.

---

## Workflow D — Label and archive

**Goal:** Move won deals out of INBOX and tag for reporting.

### Step 1 — List labels (required)

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_LIST_LABELS" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {}
  }'
```

Map display name → `id` (e.g. `Label_42`). System labels use names like `INBOX`, `UNREAD`.

### Step 2 — Create label if missing

Example: `deal-closed` — **confirm name with user first**.

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_CREATE_LABEL" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "label_name": "deal-closed"
    }
  }'
```

### Step 3 — Collect message IDs

From `GMAIL_FETCH_EMAILS` with user filter, e.g.:

```text
from:client@corp.com in:inbox
```

Collect `messageId` (15–16 char hex) for each message to archive. Max 1000 per batch request.

### Step 4 — Confirm batch

Show:

- Total count
- ≤5 sample subjects + `messageId`
- Labels to add/remove

### Step 5 — Batch modify

```bash
curl.exe -X POST "https://api.aisa.one/apis/v1/composio/tools/execute/GMAIL_BATCH_MODIFY_MESSAGES" \
  -H "Authorization: Bearer $env:AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "connected_account_id": "ca_xxxxxxxx",
    "user_id": "rep@company.com",
    "arguments": {
      "messageIds": ["18c5f5d1a2b3c4d5", "19a1b2c3d4e5f6a7"],
      "addLabelIds": ["Label_42"],
      "removeLabelIds": ["INBOX", "UNREAD"]
    }
  }'
```

**Do not** overlap the same label in `addLabelIds` and `removeLabelIds`.

---

## Future (not MVP)

Proactive automation using Gmail triggers (not in this skill's MVP; configure via AISA trigger APIs):

| Trigger | Use case |
|---------|----------|
| `GMAIL_NEW_GMAIL_MESSAGE` | New inquiry → auto-summarize → notify Slack |
| `GMAIL_EMAIL_SENT_TRIGGER` | Log outbound for CRM |

Poll interval ~1 minute by default; not suitable for sub-minute SLA without Pub/Sub.

CRM export: map Workflow B sections to HubSpot/Notion fields in agent output JSON — no extra tools in MVP.
