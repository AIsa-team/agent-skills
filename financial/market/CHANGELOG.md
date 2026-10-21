# Changelog

## 1.0.2

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Map legacy financial routes to the published contract: `/financial/financials[/income-statements|/balance-sheets|/cash-flow-statements]` (with `period`), `/financial/analyst-estimates`, `/financial/insider-trades`, `/financial/filings[/items]`, `/financial/macro/interest-rates[/snapshot]`, and the screener `/financial/financials/search/screener` with contract-shaped `filters[]` (`stock screen --filter FIELD:OP:VALUE`).
- Mark `/financial/crypto/*` and `/financial/institutional/ownership` as absent from the published contract; replace the cost-field claim with the `X-AISA-Customer-Cost-Micros-USD` header and use the canonical docs host.
- Send the required `period` parameter on `GET /financial/financial-metrics` (`stock metrics --historical --period`).

## 1.0.1

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
