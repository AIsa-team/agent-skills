---
name: use-similarweb
description: "Retrieve Similarweb website and competitor intelligence through AIsa: traffic, engagement, audience, sources, rankings, technologies, and search performance. Use for Similarweb data requests, with live contract discovery, request quotes, authorized budgets, and actual-charge reporting."
license: MIT
compatibility: "Requires Python 3.11+, network access, and AISA_API_KEY with access to the requested AIsa routes. Run the bundled Python client from a harness that supports local commands."
metadata:
  version: "1.1.0"
  short-description: Similarweb through AIsa — discover contracts, quote requests, track charges
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# AIsa Similarweb

Retrieve Similarweb data through AIsa using the live API contract and a quote before each paid request.
Read [references/discovery.md](references/discovery.md) for contract and date handling, and
[references/cost-control.md](references/cost-control.md) before executing paid requests.

## Requirements

```bash
export AISA_API_KEY="sk-aisa-..."
```

- Python 3.11+; no third-party Python packages are required.
- API origin `https://api.aisa.one`; header `Authorization: Bearer $AISA_API_KEY`.
- Access depends on the key and requested route. Use authentication or entitlement errors to identify missing access.
- Never print or commit the key. If it is missing, ask the user to set `AISA_API_KEY`.

## Quick Start

```bash
python3 scripts/similarweb_client.py discover                     # route index from the live contract
python3 scripts/similarweb_client.py describe ROUTE               # parameters, constraints, examples, response schema
python3 scripts/similarweb_client.py window                       # unverified date candidate; no paid probe
python3 scripts/similarweb_client.py check ROUTE name=value …     # local contract checks; may fetch the public contract
python3 scripts/similarweb_client.py quote ROUTE name=value …     # non-executing price estimate
python3 scripts/similarweb_client.py call  ROUTE name=value … --max-usd "$APPROVED_USD"
python3 scripts/similarweb_client.py usage --days 1               # aggregate usage for this API key
```

Run these commands from the skill directory, or use the script's absolute path. `ROUTE` may be a short
path from `discover`, such as `/website/traffic-engagement`, or its full `/apis/v1/similarweb/...` path.
Read the current `describe` output to construct each `name=value` argument. Quote arguments containing shell metacharacters.

## Request protocol

1. **Discover and inspect.** Run `discover` and `describe ROUTE`. Read required parameters, schemas,
   `x-aisa-constraints`, examples, and response declarations. Examples illustrate shape; their dates and
   account-specific identifiers are not evidence of current availability. Do not hardcode route counts or prices.
2. **Preserve the requested dates.** `window` proposes the previous complete UTC calendar month and reports
   `latest_month: null`; it does not verify Similarweb availability. Use it only when a candidate is needed.
   Never replace an explicit user period with this candidate or an example date.
3. **Build and check.** Select the smallest scope that answers the question and run `check`.
   Contract checks and a successful quote do not prove that data is available or that upstream execution will succeed.
4. **Quote and authorize.** Quote the exact request; compare variants when considering wider scope.
   Honor an existing user-approved budget and scope without asking again. If authorization is absent or the
   intended request exceeds it, show the quote and resolve that gap before execution.
5. **Execute and record.** `call --max-usd` compares the quote with an admission threshold and sends
   `X-AISA-Max-Price-USD`; this is **not a hard cap on the final charge**. For a task-wide budget, use the
   same `--task-ledger FILE` for all calls, setting `--task-budget-usd USD` when creating it. Read the
   cost-control reference for its limits.
6. **Report evidence.** Report the returned data period, quote, actual cost when known, and request ID.
   Preserve the request record and idempotency key. A missing cost header means the charge is unknown.

## Rejections and interrupted requests

Read the actual error body. A 400 can indicate invalid parameters, date constraints, or unavailable data;
it does not by itself prove contract drift. Refresh the contract once if drift is plausible, then correct
the identified problem within the user's scope. Authentication and entitlement errors require resolving access.

The client does not automatically retry paid requests. After a timeout, transport failure, or ambiguous
response, use the saved request record to establish the outcome before retrying. Do not infer zero cost from
an HTTP status or obtain a fresh idempotency key merely to bypass an uncertain or duplicate outcome.
After obtaining request-specific charge evidence from Usage & Logs, `reconcile REQUEST_RECORD
--charged-usd USD --evidence TEXT` records that evidence locally without an API call.

## When to use / when not to

- Use when the question is about a **website's** traffic, audience, sources, technology or search footprint.
- For a task that needs keyword difficulty or backlink analysis beyond the discovered Similarweb routes,
  use an available specialist tool appropriate to that task.

## Output

`call` returns the raw Similarweb response in `data`, alongside status, quote, cost, request ID, latency,
data period when available, `idempotency_key`, and `request_record`. With `--out FILE`, the full result is saved
to that file and stdout remains JSON. `requested_period` records the input; `data_period`, `data_month`, and `last_updated` retain separate
response metadata. Do not treat an update timestamp or an echoed request period as observed coverage. Missing cost or provider-period metadata must remain unknown;
do not substitute the quote for actual cost or label a calendar candidate as confirmed data availability.

`usage` reports aggregate totals for the API key over a time window. It does not isolate this task's charges.
The compact protocol in [references/agent-rules.txt](references/agent-rules.txt) is available for external agents.

## API Reference

- [Similarweb OpenAPI contract](https://aisa.one/docs/openapi/similarweb.json) — routes, parameters, constraints, and response declarations
- [Similarweb API docs](https://aisa.one/docs/api-reference/similarweb/get_similarweb-website-traffic-engagement)
- [AIsa pricing guide](https://aisa.one/docs/guides/pricing) — quotation, admission, and billing semantics

See the [full AIsa API Reference](https://aisa.one/docs/api-reference).

## License

MIT — see [LICENSE](../LICENSE) at the category root.
