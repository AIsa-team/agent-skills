# Changelog

## 1.1.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.

## 1.1.0

- Repair current X and YouTube field/date parsing and use Polymarket public search with explicit observation timestamps.
- Exclude undated, future, and out-of-window publications; retain unknown engagement and label indexed social web discovery.
- Require an authorized budget for hosted requests. Record exact quotes and actual micro-USD charges in durable task/watchlist ledgers, block unresolved charges, and prevent automatic paid retries.
- Keep planning/ranking local while the chat contract lacks verified free-quote capabilities. Variable-cost retrieval requires explicit acceptance; estimate budgets are not guaranteed final-charge caps.
- Validate flags, external plans, and date windows before research; preserve caller configuration, source restrictions, and partial failure evidence.
- Align Python 3.11 support and runtime version, repair offline evaluation, and ship focused adapter, pipeline, accounting, CLI, and watchlist regression tests.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
