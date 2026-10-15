# Request costs and recovery

Follow the current [AIsa billing guide](https://aisa.one/docs/guides/pricing).
Budgets compare admission estimates, not guaranteed final charges. Never describe
`--budget-usd` or `X-AISA-Max-Price-USD` as an absolute final-charge cap.

## Authorization

Use only the scope and budget the user authorized. Do not treat a documentation
example, a saved credential, or the historical watchlist default as authorization.
Reuse an existing task ledger instead of resetting spending by creating new ones.

```bash
bash scripts/run-last30days.sh "$TOPIC" \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json
```

USD must be a nonnegative plain decimal with at most six decimal places. A ledger
stores its immutable approved budget and exact integer micro-USD charges. An
existing ledger can be reused without repeating `--budget-usd`; a different
amount is rejected. Without an explicit ledger, a new budget creates a ledger
under `~/.local/state/last30days/costs/`, whose path is reported in the result.

If the quote says `may_exceed_estimate`, execution requires
`--allow-variable-cost`. Supply that flag only when the user has accepted that
possibility. For a hard final spending limit, this admission mechanism is
insufficient. Do not silently enlarge the budget or relax its interpretation.

## Verified routes and accounting

The client supports quotes only for the exact X search, YouTube search, Tavily
search, and Polymarket public-search methods/paths verified in their official
contracts. It sends the same request body and URL for quote and execution.
Unsupported routes fail before any speculative quote. In particular, the
current chat contract does not declare quote support; optional reasoning uses
local fallbacks. Authenticated redirects are rejected.

Hosted dispatch is serialized against one process/file-locked ledger. Before
execution, a durable pending record stores the local request ID, method, URL,
body hash, estimate, and admission limit. The client never automatically retries
a paid request. Idempotency support is route-specific; a local record is not a
promise of provider response replay.

The response's `X-AISA-Customer-Cost-Micros-USD` supplies actual cost. Actual
charges can exceed estimates and are recorded in full. Missing or malformed
costs remain unknown, including on HTTP failures. A known charge is retained
even when the response body is truncated or cannot be decoded. Unknown charges
and an exceeded budget block subsequent paid requests while public/local work
can still produce a partial evidence report.

JSON includes `artifacts.costs`, with ledger totals and separate per-run totals.
Markdown displays known ledger charges and unresolved requests. Failed CLI runs
also print a cost summary to stderr; the ledger remains the durable evidence.
Never add cumulative ledger totals together as if they were per-run charges.

## Reconciliation

Inspect the ledger and request-specific Usage & Logs evidence. Do not infer zero
from a timeout or status code, and do not substitute account-wide usage totals
for proof of an individual request's charge.

```bash
python3 scripts/lib/costs.py show research-costs.json
python3 scripts/lib/costs.py reconcile research-costs.json "$REQUEST_ID" \
  --charged-usd "$VERIFIED_CHARGE_USD" --evidence "$REQUEST_SPECIFIC_EVIDENCE"
```

Reconciliation records the supplied external evidence locally. It does not
verify the claim against the provider or execute the request again.

## Watchlists

Watchlist work requires an explicitly configured daily budget; the old implicit
$5 default is not authorization. Daily ledgers use UTC and account across topic
runs. Unresolved earlier-day requests block later paid watchlist work until
reconciled. Per-run SQLite costs are reporting data; durable request ledgers are
the authority for admission. Configuring or running a watchlist does not by
itself authorize creating a schedule or sending external notifications.
