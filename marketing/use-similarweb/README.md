# AIsa Similarweb

**Similarweb website intelligence through AIsa, with live contract discovery and request quotes.**

The bundled Python client reads the live contract for routes, parameters, constraints, and response schemas.
It quotes requests before execution, records paid attempts, and reports actual charges when the API supplies
them. The contract can evolve; discovery does not itself verify provider data availability.

## Compatibility

Requires Python 3.11+, network access, and a harness that can run local commands. The client uses only the
Python standard library. Set `AISA_API_KEY` with access to the requested routes; obtain a key at
[aisa.one](https://aisa.one). Authentication and entitlement errors identify missing account access.

## What Can You Do?

### Traffic for a domain
```text
"How many visits did cnn.com get last month? Quote it first."
```

### Competitors and search footprint
```text
"Who are nike.com's keyword competitors and which landing pages win?"
```

### Audience and sources, within a budget
```text
"Show me cnn.com's referral sources and its audience overlap with bbc.com — ask me before spending."
```

## Quick Start

```bash
export AISA_API_KEY="sk-aisa-..."
python3 scripts/similarweb_client.py discover
python3 scripts/similarweb_client.py describe ROUTE
python3 scripts/similarweb_client.py check ROUTE name=value …
python3 scripts/similarweb_client.py quote ROUTE name=value …
python3 scripts/similarweb_client.py call  ROUTE name=value … --max-usd "$APPROVED_USD"
```

Run from this skill directory or use the script's absolute path. Get `ROUTE` and its parameters from
discovery. `--max-usd` is an estimate threshold for admission, **not a hard cap on the final charge**.
The optional `--task-ledger FILE --task-budget-usd USD` tracks actual charges across a task and blocks
further spending when a charge is unresolved. See [cost control](references/cost-control.md) for its limits.

`window` supplies an unverified candidate month without a paid probe; it does not confirm the latest
available Similarweb data. Explicit user dates are preserved. See [discovery](references/discovery.md).

## API Reference

See the [Similarweb contract](https://aisa.one/docs/openapi/similarweb.json),
[AIsa API Reference](https://aisa.one/docs/api-reference), and
[pricing guide](https://aisa.one/docs/guides/pricing).

## License

MIT — see [LICENSE](../LICENSE) at the category root.
