# Snapshot collection and comparison

## Local state and commands

Run `python3 scripts/track.py --help` from the installed skill root. Python 3.10+ and its standard SQLite module are sufficient. The database's parent directory must already exist; use a persistent project/data directory, not the installed skill bundle or a disposable job directory.

| Command | Purpose |
| --- | --- |
| `init --db PATH` | Initialize the SQLite database without replacing an existing one. |
| `add --db PATH --asin ASIN --marketplace DOMAIN --label LABEL` | Register an exact ASIN/marketplace. Label is optional; repeated registration preserves the original entry. |
| `list --db PATH` | Return watched ASINs, marketplaces, labels and registration times. |
| `ingest --db PATH --input FILE` | Import saved AIsa execution results for watched products. |
| `report --db PATH --asin ASIN --marketplace DOMAIN` | Return the latest observations and comparisons with a prior observation in each compatible series. |

Although `--marketplace` defaults to `amazon.com`, specify it explicitly after resolving the user's market. Amazon US is the tested, supported market. The domain allowlist validates identifiers; it is not a claim of support for other Amazon markets, which require independent validation. The watchlist stores identity and label, not scheduler settings, budget authorization or source credentials.

All commands return JSON on stdout. Errors go to stderr with exit code 2. Ingest can also return exit code 2 after recording successful calls in a mixed batch: inspect its `rejected_calls`, `ignored_calls`, `inserted_snapshots` and `duplicate_snapshots`. Do not treat partial progress as a complete successful collection or rerun paid API calls automatically.

## Input contract

Ingest accepts saved **execution** output in these forms:

- An AIsa batch object with `results[]`.
- A native MCP envelope containing that object in `structuredContent`.
- An array of either form, or `{ "responses": [ ... ] }` for multiple saved batches.

It does not accept quote responses, schemas, scraped prose, HTML, arbitrary marketplace JSON or model-written observations. Preserve real request/task IDs and status codes. A supported call has `successful: true`, a successful `upstream_status`, `request_id`, and a DataForSEO `data` object with successful top-level and task statuses. Its provider task route must be one of:

```text
v3 / merchant / amazon / products / live / advanced
v3 / merchant / amazon / asin / live / advanced
```

Keep `tasks[].data` (request context), `tasks[].result[]` (including marketplace, locale, time, row count and items), result count and task IDs intact. Search may return unrelated listings; only watched ASINs are recorded. Never change an ASIN or fabricate missing provenance to make a response ingest successfully. An unsupported wrapper requires an explicit, lossless extraction of the actual provider response.

`--collected-at` optionally supplies a timezone-aware ISO timestamp for an accurately known collection time. The default is import time in UTC. Provider `datetime` is preserved as the observation time; a missing provider timestamp is explicitly labelled as collection-time fallback. When importing historical data, do not describe the new import time as fresh market evidence.

The input JSON is saved alongside normalized snapshots for provenance. Keep supplied API responses free of credentials; the adapter needs no authorization headers, keys, cookies or tokens. Store account secrets in the host's supported credential mechanism, outside this database.

## What is stored

The database retains watched identities, immutable input JSON and normalized snapshots. Existing observations are not updated or deleted by these commands. Reports use only current product search/detail snapshots; legacy snapshots outside this scope remain saved but are ignored. Re-importing a known request/task observation is idempotent and must not create a second time point. Distinct provider observations can be kept even when their values are unchanged.

Each product snapshot retains its source family (`search` or `detail`), ASIN/marketplace, locale/query scope, provider observation and collection timestamps, request/task IDs, source URL and any reported customer charge. Amounts in `customer_cost_micros_usd` are **micro-USD**: divide by 1,000,000. Do not sum repeated per-call charges from several snapshots: account for execution costs once per request ID, including calls without usable product data. Missing actual charges remain unknown.

Product rows retain supported identity, source row type, product prices/ranges, currency, availability, ratings and demand fields when returned. Missing fields remain unknown. Normalized reports do not include opaque product-information fields; the original evidence remains in immutable input JSON. The helper does not parse a category Best Sellers Rank series from free-form text.

## Interpret reports

The report has a `product` watch entry, `generated_at`, `series[]` and `limitations`. Each series contains its `latest` product snapshot and a `comparison` with `previous_observed_at`, `rows` and `notes`. Look at the observation time for each series; report generation does not refresh the underlying sources. Seller-level information is outside the skill's scope and is not part of its output.

Compatibility separates source families and location/language/device context. Search also includes the query and collection scope. Organic and sponsored rows are distinguished, and duplicate observations must not create a trend. Changing destination or query can therefore produce a new baseline rather than a comparison.

Product comparison groups preserve endpoint, query, locale and row-type context. Each comparison row includes `row_type`, current/previous row counts and price ranges, `price_delta`, rating count/value deltas, `availability_changed`, `status` and `price_status`. A scalar price delta requires exactly one row with a point price in both observations and a known matching currency. A `price_from` with absent `price_to` is one displayed price; unequal bounds are a range. Multiple rows and ranges remain available as evidence but do not establish a scalar price delta. Inspect `price_status` before summarizing a change.

`status` meanings:

- `baseline`: no prior compatible observation.
- `unchanged`: the comparable recorded product metrics match.
- `observed_product_changed`: at least one comparable recorded product metric differs; inspect the price, ratings and availability fields to identify which changed.
- `not_comparable`: the available rows do not support a comparison.
- `newly_observed`: the product row group was not in the prior snapshot, not necessarily a newly launched product.
- `not_observed_now`: the group was not returned this time, not proof of a stockout or discontinued product.

`price_status` explains price eligibility separately. `changed` marks a comparable point-price change; `unchanged` marks matching comparable point prices. `ambiguous_rows`, `unknown_currency`, `currency_changed`, `unknown_price` and `range_observed` suppress scalar deltas. Baseline or absent-row statuses likewise provide no delta. A product metric may change while its price remains unknown or unchanged.

For product feedback, compare only the same source/row type and describe counts as ratings/feedback. The helper does not calculate exact sales from ranks, rolling purchase badges or review growth. Product availability and purchase indicators describe separate metrics.

An empty, failed, mismatched or malformed response must not replace good history with zero prices or a stockout claim. Carry the ingest rejection and collection failure into the user-facing report alongside the last valid observation. Historical values must be labelled with their age; do not quietly present them as current.

## Recurring execution

When the user requests ongoing monitoring, save the target ASINs/variants, marketplaces, locale, database path, collection cadence/timezone, alert thresholds, spend scope and allowed notification destination in the host's job configuration or an adjacent project configuration file. The helper itself is not a daemon or scheduler.

A scheduled run should read the saved targets, discover/reuse current supported contracts, quote the bounded request batch, execute within authorization, save results, ingest and generate a report. Keep paid retry behavior explicit. A run that lacks credentials, a valid quote or supported operation should record/report the gap without inventing a snapshot.

Match each alert to its evidence: a comparable product price change can trigger a price alert; a listing missing once from incomplete coverage warrants a not-observed notice only if requested. Avoid routine unchanged notifications. The host must retain the same database between runs. Do not create an external messaging destination or send messages merely because the skill supports alerts.
