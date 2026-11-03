# Native AIsa workflow: MCP first, official CLI for hosts without MCP

This is the default production path for new projects in 1.1.0. The host performs authenticated AIsa operations; the TypeScript runtime validates credential-free records and exact handoffs. It is not an MCP server, OAuth client or automatic REST proxy.

## Establish one connection

Use the shared connection rules in [SKILL.md](../SKILL.md): remote MCP at `https://mcp.aisa.one/mcp`, normally with host-managed browser OAuth; host-configured API-key authentication for headless MCP; official AIsa CLI only when the host has no MCP. Verify with the free MCP account call or CLI balance call. Tools appearing in a list are not sufficient proof of authentication. Never copy tokens or API keys into project records.

`init <brief.json> <project-dir>` records `mcp` by default. `--transport cli` selects the official CLI handoff; `--transport rest` explicitly selects the separate compatibility implementation and requires the shared HTTP fallback gate. Transport remains stable for the project. An uncertain paid operation must be reconciled through its original connection, not resubmitted elsewhere.

No paid operation is required to test connectivity or discover a model. Do not probe a payload-length theory by making repeated paid generation requests.

## Discover the model and complete operation contract

1. After the product-photo gate, search AIsa with the full task: media type, reference-conditioned editing/generation, desired options and target use. Discover the model catalog operation and selected generation/status operations. Names come from the actual discovery response.
2. Obtain the current catalog through the selected interface. Offer all relevant entries, including new models; no local name list decides eligibility. Record the catalog source, observation time and model IDs.
3. Obtain full argument **and response** schemas. Request full schemas when discovery says `has_full_schema: false`; request response schemas explicitly if they are not included by default. Retain session/search context as provided by the interface.
4. Check the selected model's specific contract: supported references/encodings/counts, sizes, durations, audio and other provider options. A shared operation body can accept arbitrary provider fields without proving a particular model accepts them.
5. Put the exact selected model, request template, bindings and response mappings in the playbook before approval. A parameter change after approval requires a revised playbook. A catalog entry is discovery evidence, not a claim that the model has been live-tested or will preserve every product detail.

Reuse complete, fresh schemas in the active session. New generation requires catalog/model-contract evidence less than 24 hours old. Ingesting or recovering an existing paid job uses its frozen approved contract, so a later catalog timestamp does not strand that task. Refresh for a new operation/session, missing or stale data, or an explicit schema/contract mismatch. Do not reload before every call as a ritual or diagnose an undocumented intermittent issue without evidence. The runtime validates draft-07/2020-12 JSON Schemas with Ajv; unsupported dialects or unresolved references require a complete supported schema, not deleting constraints.

`models` gives host discovery instructions by default. It does not send a direct REST request or require `AISA_API_KEY`. Only explicit `models --transport rest` uses the compatibility catalog client.

## Model-specific request plan

Each native generated deliverable has `nativeRequest` with these fields; see the exact TypeScript definition in [`scripts/native-contract.ts`](../scripts/native-contract.ts):

| Field | Evidence or role |
| --- | --- |
| `tool` | Exact discovered operation identifier |
| `catalog` | `{source, checkedAt, modelIds}` from actual model discovery |
| `modelContract` | `{source, checkedAt, supportsReferences}` from the selected model contract |
| `argumentsTemplate` | Complete operation arguments with explicit placeholder locations for model, prompt and product references; all other selected options are literal approved values |
| `argumentsSchema`, `responseSchema` | Complete discovered JSON schemas, not summaries or invented permissive replacements |
| `modelPointer`, `promptPointer` | JSON pointers to existing template values that the runtime replaces with the approved model and prompt |
| `referenceBindings` | `{referenceId, pointer, encoding}` entries; `encoding` is `data-uri` or `https`, as allowed by the selected model |
| `result` | Response mapping for images, text or a video task, described below |
| `poll` | Async status operation plan with its own tool, argument template/schema, response schema/result mapping and `taskIdPointer` |

Bindings must point to existing placeholders, must not overlap, and must use approved reference IDs. The runtime inserts the actual inspected photo bytes for `data-uri` and builds the production prompt from the approved instruction, facts and requirements; for `https` it verifies that the supplied remote URL matches the local photo. Every approved image/video reference must be bound, and the selected operation/model must support references. Copy can use the approved facts without sending photos, but the intake photo gate still applies.

For example, if the **discovered contract for the selected model** accepts `body.image` as data URLs, its template may have `/body/model`, `/body/prompt` and `/body/image/0` placeholders. Another model may require a content array, such as `/body/content/0/text` and `/body/content/1/image_url/url`. These examples explain pointers; they are not universal provider schemas. Do not assign a Seedance content structure to another video model without checking its contract.

Keep model options in the approved template and final-export requirements in the deliverable. The runtime does not infer arbitrary provider dimensions/audio options from a model name. The host must check that the template's requested generation size, duration and other options satisfy the approved output plan.

For results, pointers address the **operation response object**, not the outer MCP batch envelope:

- `result.images`: `pointer` selects the image array; `urlPointer` and/or `base64Pointer` are relative to each entry. Empty pointer means the entry itself. Use only encodings the returned schema documents.
- `result.textPointer`: points to the generated text. Ask the chosen text model for the required copy JSON fields and validate the saved output.
- `result.task`: defines `idPointer`, `statusPointer`, `urlsPointer` and explicit nonoverlapping `pending`, `succeeded`, `failed` status arrays. A video needs this task mapping; asynchronous jobs also need a `poll` plan. The successful-output mapping must expose usable media URLs.

The validated handoff currently supports data-URI/HTTPS photo bindings and these result forms. If a discovered model requires a different encoding, upload operation or response shape, explain that specific implementation gap. Do not hide the model from discovery, pretend a different request is equivalent, or bypass validation to claim full support.

## Prepare, quote and dispatch exactly once

Complete `research-import`, `playbook-import`, `report`, the user's explicit confirmation and `approve` first. A quote or a menu selection is not playbook approval. Connection verification can happen before those stages without generation.

The native sequence is:

1. Import the successful connection-check receipt with `connection-import`.
2. Run `build-native-request <project-dir> <deliverable-id>`. It writes the complete arguments JSON and its canonical SHA-256 hash; no authenticated call is made.
3. Quote the exact discovered tool and complete arguments through the selected interface. Keep returned quote request/session IDs, timestamp and price; when CLI omits an ID, use the explicitly local evidence-correlation convention below. Follow the shared spending rule, including any tighter user limit. Neither an estimate nor the local budget is a provider billing cap.
4. Run `prepare-native` with the actual quote receipt and connection/session context. This validates the approved plan, current evidence, argument hash and spending allowances and produces the handoff.
5. Run `mark-native-dispatched` **immediately before** the host sends that exact call. Then execute it once through MCP or the official CLI.
6. Save and ingest the actual execution result using `ingest-native-result`. Preserve task/request IDs, costs and errors before continuing. Recover/materialize the saved output or prepare a status check; do not submit a replacement merely because the media is not yet ready.

Read the generated argument file in a host tool that can load JSON reliably, then pass that parsed object to the native call. In MCP batches, `calls[].arguments` is an **object** and an operation's `body` remains an **object**. If the host's outer invocation format requires serialized JSON text, serialize that outer layer once. Never manually copy abbreviated tool output, truncate base64, stringify the nested arguments twice or put a filesystem path where the provider expects actual reference bytes.

Use the official CLI's current `aisa search` → `aisa schema` → `aisa quote` → `aisa call` contract for CLI transport. Inspect its current help for file/object argument options; do not invent flags or interpolate untrusted JSON into shell code. Preserve equivalent operation, exact arguments and evidence in the same native receipt format. The skill does not itself spawn the official CLI.

Quote metadata may not include a field literally named `argumentsHash`. The runtime computes that hash from the exact arguments file. A normalized quote receipt records that locally computed hash and the real per-call `request_id` when returned. For an interface that omits a request/session ID, apply the local correlation convention below; never represent a locally assigned value as a provider-returned ID. Use only parameters exposed by the actual native schema: a header shown in underlying REST documentation does not mean MCP accepts a max-price or idempotency parameter.

## Receipt JSON shapes

The following shapes describe normalized local records; values must come from the actual run. They are not complete command inputs or evidence that a call happened. Keep original sanitized native outputs alongside the normalized records. Exact interfaces live in [`scripts/native.ts`](../scripts/native.ts).

**Connection receipt** for `connection-import`:

```json
{
  "transport": "mcp",
  "server": "https://mcp.aisa.one/mcp",
  "connected": true,
  "checkedAt": "ACTUAL_SUCCESSFUL_CHECK_ISO_TIMESTAMP",
  "receiptId": "local-check-UUID_LINKED_TO_SAVED_SUCCESSFUL_CHECK"
}
```

`receiptId` identifies the **connection-check record**, not necessarily a provider request. A successful MCP `account` response may contain no request/receipt ID. In that case, assign a local ID such as `local-check-<uuid>` and save the sanitized actual successful account/balance output alongside it, with the check time, transport and an explicit note that the identifier was assigned locally. If the provider or host supplies an actual check ID, retain it with its source instead. Do not copy API keys, tokens or unneeded account/key details into the evidence. A local ID links the record to observed evidence; it cannot replace a real successful check.

Use `transport: "cli"` for an explicitly selected CLI project; `server` identifies the AIsa service, not a claim that the CLI itself uses MCP. The check must be successful and less than 24 hours old. The runtime stores this record in `connection.json`; it does not authenticate by importing it. After a `401`, perform a **new actual successful account/balance check** and save its new evidence before importing a new record ID. Merely changing the ID or timestamp on old evidence does not satisfy recovery. The ordinary retry/approval rules still apply.

**Identifier provenance:** MCP `sessionId` and `searchId` use the actual identifiers returned by discovery. The official CLI may omit a server session ID; if so, assign a stable `local-session-<uuid>` for this host execution sequence and keep it consistent across the local quote/preparation/result records. If a CLI quote or execution omits a request ID, use its real host invocation ID, or assign a `local-capture-<uuid>` linked to the saved sanitized command output. Record `local`, `host` or `provider` origin in the evidence alongside the record. These values are local correlation identifiers, not fabricated server receipts; do not pass them as server session/request parameters or claim the provider returned them. Provider **task IDs** always come from actual provider results and must never be assigned locally.

**Preparation record** for `prepare-native` (or a saved-task poll):

```json
{
  "deliverableId": "APPROVED_DELIVERABLE_ID",
  "sessionId": "ACTIVE_EXECUTION_SESSION_ID",
  "searchId": "DISCOVERY_SEARCH_ID_IF_RETURNED",
  "connectionReceiptId": "IMPORTED_CONNECTION_CHECK_RECEIPT_ID",
  "quote": {
    "requestId": "QUOTE_PROVIDER_OR_EVIDENCE_CORRELATION_ID",
    "tool": "EXACT_DISCOVERED_OPERATION",
    "sessionId": "SAME_EXECUTION_SESSION_ID",
    "argumentsHash": "CANONICAL_SHA256_FROM_BUILD_NATIVE_REQUEST",
    "quotedAt": "ACTUAL_QUOTE_ISO_TIMESTAMP",
    "currency": "USD",
    "estimatedCostUsd": 0.0,
    "estimateKind": "exact",
    "mayExceedEstimate": false,
    "maxCostUsd": 0.0,
    "source": { "replaceWithActualSuccessfulQuoteExcerpt": true }
  }
}
```

Omit `searchId` when the interface does not return one. Replace the illustrative zero price and `source` placeholder with the actual successful quote and its preserved sanitized excerpt. The placeholder is not evidence of a successful quote. A quote expires after one hour locally; its tool, session and exact argument hash must match. Preserve its billing semantics: `estimateKind: "exact"` has `mayExceedEstimate: false` and `maxCostUsd` equal to `estimatedCostUsd`; `upper_bound` has `mayExceedEstimate: false` and a finite ceiling; `estimate` has `mayExceedEstimate: true` and `maxCostUsd: null`. Do not convert an unbounded estimate into a ceiling. The quoted amount, or the finite upper bound when provided, cannot exceed the approved per-attempt allowance. Estimates can still be exceeded by actual billing and must be disclosed under the shared spending rules. `retry: true` is only for a confirmed failed or reviewed-rejected attempt within the allowance, after telling the user; it cannot override an unresolved submission. Preparation records a job and its operation before dispatch. The saved request at `operation.requestPath` contains `calls[0].arguments`, including full reference data; use that exact object.

A polling preparation uses the same receipt shape and the actual saved `job-id`; its quote must be zero. Paid status operations are not dispatched by this runtime. Explain that limitation if discovery returns a paid poll rather than disguising it as free.

If the quote expires **before dispatch**, or the host abandons an unsubmitted preparation, run `cancel-native-prepared <project-dir> <operation-id>`. Only a prepared operation that was never marked dispatched can be canceled. A canceled generation retains its audit history but releases its local estimated-cost and attempt reservations; build fresh arguments, obtain a fresh quote and prepare again without `retry: true`. Canceling a prepared poll preserves the original generation job and provider task ID, so another status check can be prepared. Cancellation does not refund a provider charge, and it is unavailable for dispatched or uncertain operations: reconcile those through their saved evidence instead of canceling or blindly resubmitting them.


**Execution result** for `ingest-native-result`:

| Field | Value |
| --- | --- |
| `tool`, `sessionId`, `argumentsHash` | Match the prepared operation exactly |
| `requestId` | Returned execution ID, or an explicitly identified local/host evidence-correlation ID when the interface omits it; distinct from the quote record |
| `outcome` | `success`, `failed` or `unknown`, based on observed execution evidence |
| `data` | The actual operation response object, matching its approved response schema; do not pass the outer batch wrapper |
| `statusCode`, `error` | Optional observed HTTP status and sanitized diagnostic; no invented cause or credentials |
| `taskId` | Optional actual retained provider task ID, including a documented pending error response |
| `customerCostMicrosUsd` | Settled nonnegative integer micro-USD from native cost metadata, or `null`/omitted when unknown |

The result is saved before interpretation. For a malformed successful response or an uncertain transport result, preserve it and reconcile the saved operation; do not label it a confirmed generation failure just to enable retry. A failed status check retains the original task. Native receipt costs and locally quoted estimates remain separate.

For `import-host-copy`, supply `{ "producedBy": "host", "note": "How this copy was prepared from the approved facts", "text": "JSON text containing the approved copy fields" }`. The deliverable must explicitly use `model: "host-copy"` and zero AIsa generation estimate. It still needs the normal approved playbook and hash-bound copy review.

## Recover and inspect

For an asynchronous saved task, `build-native-request <project-dir> <deliverable-id> --job <job-id>` constructs the status arguments. Quote that status operation, then use `prepare-native-poll <project-dir> <job-id> <request.json>`, mark dispatch and ingest the actual status receipt. The runtime binds the poll to the original task ID. Use bounded checks, not an unending polling loop.

`resume-native` only materializes or recovers saved native results locally. `resume` also routes native projects to local recovery. Neither is permission to create another paid generation. After materialization, inspect actual artifacts, record hash-bound review findings and export only passing content. For an approved `host-copy` deliverable, use `import-host-copy` and the same copy validation/review requirements; this is an explicit playbook choice, never a silent fallback from a failed AIsa call.

Distinguish host JSON/parser failures, AIsa schema validation errors, provider rejection and uncertain transport outcomes. Preserve operation/session/request IDs, argument hash and useful sanitized diagnostics. A clear provider failure is different from an uncertain dispatch. Do not automatically retry paid failures, change models or switch transport. A `401` requires checking/recovering the selected connection; account-check success alone does not prove a media upstream route is authorized. Explain the observed failure without inventing an account entitlement diagnosis.

For AIsa's video route, only the documented `video_submission_pending` error with a valid saved task ID means submission is retained and status should be retrieved. A generic `503` without that evidence does not prove a recoverable task exists. Preserve any returned task/status guidance from the actual batch envelope. A failed status call does not imply the original generation failed or should be resubmitted.

A changed artifact requires another review. A successful response, decodable image or completed task does not prove product identity, truthful motion, typography or platform compliance. No offline fixture or schema check establishes that all current models passed live generation.
