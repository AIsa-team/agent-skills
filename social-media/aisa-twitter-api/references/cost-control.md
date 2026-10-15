# Quotes, budgets, and request recovery

Use the [current AIsa billing contract](https://aisa.one/docs/guides/pricing).
Quotes and `X-AISA-Max-Price-USD` concern the execution estimate. Neither is a
guaranteed limit on the final settled charge.

## Quote and execute

`--quote` sends the exact supported operation with `X-AISA-Cost-Mode: quote`.
It does not execute the upstream operation or create a ledger. A quote does not
supply tweets, create an authorization link, upload media, or publish a post.

For execution, use the budget authorized for the task:

```bash
python3 scripts/twitter_client.py search --query "$QUERY" \
  --budget-usd "$APPROVED_BUDGET_USD" --cost-ledger research-costs.json
```

Only use `--allow-variable-cost` if the user accepted quotes marked
`may_exceed_estimate`. A requirement for a hard final-charge ceiling cannot be
fulfilled by this estimate-admission mechanism.

USD values are exact plain decimals with at most six places. A new ledger needs
`--budget-usd`; an existing ledger retains its immutable budget and can be reused
with `--cost-ledger`. Do not reset task spending by creating a new ledger. When a
budget is supplied without a path, a new ledger is created under
`~/.local/state/aisa-twitter-api/costs/`; its path is reported in `_aisa.costs`.

Only the explicitly verified operation allowlist can be quoted or executed.
Spaces detail currently has no declared quote/admission capabilities and is
blocked before a request is sent. No speculative quote is sent to an unsupported
operation. Reference prices in documentation are not substitutes for exact quotes.

## Accounting

Each quote/execution pair shares a process/file lock. The exact method, URL, and
body bytes are retained between quote and execution, including multipart upload
boundaries. Before execution, a durable pending record saves the request ID,
method, redacted URL, body hash, quote, and remaining estimate budget. Auth headers,
keys, media bytes, and full response bodies are not stored in the ledger.

The client records `X-AISA-Customer-Cost-Micros-USD` as actual integer micro-USD,
including for HTTP failures and malformed/truncated bodies. Missing or invalid
billing headers remain unknown. Unknown outcomes or exceeded budgets block
subsequent execution. A zero-priced description is not evidence that an individual
request settled at zero.

Successful provider objects retain their fields with reserved `_aisa` HTTP and
cost metadata. Failures set `success: false` and `ok: false`, return nonzero from
the CLI, and retain available billing information. Per-run costs and cumulative
ledger totals are separate; do not add cumulative totals as per-request charges.

Paid requests, posts, and uploads are never automatically retried. Idempotency
headers are declared for supported routes, but generic Twitter replay/duplicate
semantics are not documented. Local request IDs do not guarantee remote replay.
Authenticated redirects are rejected.

## Reconcile

```bash
python3 scripts/costs.py show research-costs.json
python3 scripts/costs.py reconcile research-costs.json "$REQUEST_ID" \
  --charged-usd "$VERIFIED_CHARGE_USD" --evidence "$REQUEST_SPECIFIC_EVIDENCE"
```

Reconciliation records externally verified evidence locally; it does not verify
billing with the provider, execute a request, or prove whether a post was published.
Use request-specific Usage & Logs evidence for charges. For ambiguous writes,
inspect the X account and confirmed IDs as well. Do not infer zero from a timeout
or retry an entire partially published thread.
