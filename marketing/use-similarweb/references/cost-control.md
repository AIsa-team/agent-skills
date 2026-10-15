# Quotes, authorization, and charge tracking

Use the current [AIsa pricing guide](https://aisa.one/docs/guides/pricing) for billing semantics.
This skill contains no fixed prices or pricing formulas. Obtain an estimate for the exact request before
execution, then report the actual charge from response evidence when available.

## Quote the intended request

`quote ROUTE name=value …` sends `X-AISA-Cost-Mode: quote`. It estimates cost without executing the
upstream request. A quote can include `estimated_cost_micros_usd` and `may_exceed_estimate`.
One million micro-USD equals one USD; keep currency comparisons exact at micro-USD precision.

A successful quote is not a guarantee of data availability or execution success. Quotes need not exercise
all provider validation. If wider scope is useful, quote the proposed variant too and compare the result
against the original question and budget. Do not infer a pricing formula from one quote.

## Authorization and the admission threshold

Honor the budget and scope the user already authorized. Ask only when that authorization is absent or
insufficient for the intended request. Do not request approval again for every call that stays within it.

Without `--max-usd`, `call` only quotes. With a nonnegative USD amount of at most six decimal places, it
compares the quote with that threshold and sends `X-AISA-Max-Price-USD` if the request can proceed. This header limits the
**estimate accepted for admission**, not the final charge. The actual charge can exceed the estimate;
neither this flag nor the task ledger can guarantee an absolute final-charge ceiling.

When the user requires a hard final spending limit, do not present an estimate threshold as satisfying it.
Resolve that limitation before executing variable-cost requests. Inspect `may_exceed_estimate` and the
current pricing terms instead of assuming the estimate is exact.

## Tracking a task budget

For multiple calls under one task budget, use one ledger consistently:

```bash
python3 scripts/similarweb_client.py call ROUTE name=value … \
  --max-usd "$APPROVED_REQUEST_USD" \
  --task-ledger task-spend.json \
  --task-budget-usd "$APPROVED_TASK_USD"
```

Set `--task-budget-usd` when creating the ledger. On later calls, omit it or repeat the same total; a
different total is rejected. The ledger accounts for recorded actual charges and compares the next quote
with the remaining task budget. Use the same file for every paid call in the task. A timeout, incomplete
request, or response with unknown cost blocks further ledger spending until the outcome is resolved. Starting another ledger would
lose that protection. The ledger does not include calls made outside it or guarantee that a request's
final charge will fit the remaining budget.

## Request records and idempotency

Before dispatch, the client persists a request record under the cache's `requests` directory and updates
it with the full response afterward. The result includes `idempotency_key` and `request_record` so the logical request remains identifiable after an
interruption. `--idem KEY` allows an explicit idempotency key.

The client never automatically retries a paid request. If execution times out or its outcome is ambiguous,
inspect the saved record and establish what happened before retrying. A fresh key can admit a second paid
execution; do not use one to bypass an unresolved request or duplicate-key rejection. A provider hint such
as `retryable: true` does not establish that the previous attempt was uncharged. A completed successful
request must not be repeated merely to obtain missing billing metadata.

When request-specific Usage & Logs evidence establishes the charge, record it locally:

```bash
python3 scripts/similarweb_client.py reconcile REQUEST_RECORD \
  --charged-usd "$VERIFIED_CHARGE_USD" --evidence "Request-specific Usage & Logs evidence"
```

`reconcile` records the supplied amount and evidence without an API call; it does not independently verify
the claim or re-execute the request. Use zero only when the evidence establishes no charge. The ledger then
uses the reconciled charge when deciding whether another request fits. If a process interruption left an
execution lock, establish that the process is no longer active and obtain evidence of its outcome before
removing the lock and recording the reconciliation.

## Actual cost and errors

The `x-aisa-customer-cost-micros-usd` response header provides the charged amount. Report it as `cost_usd`
when valid. A missing or invalid cost header means **unknown**, not zero and not the quoted estimate.
Retain the raw response, request ID, and saved record when the result is incomplete.

Read the actual error body to distinguish validation, entitlement, estimate-threshold refusal, duplicate
admission, and upstream failure. HTTP status alone is insufficient to declare that a request was uncharged.
In particular, do not label every 400, 402, 409, or 503 as free, and do not apply a blanket new-key retry rule.

## Aggregate usage

`usage --days N` reads `GET /v1/usage` for a time interval. These are aggregate totals for the API key,
potentially including other tasks. Use them as supporting billing evidence, not as exact reconciliation
of this task or proof of a particular request's outcome. Keep task-specific records for attribution.
