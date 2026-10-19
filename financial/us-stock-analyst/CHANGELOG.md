# Changelog

## 1.0.2

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Map legacy financial routes to the published contract (`/financial/financials` with `period`, `/financial/analyst-estimates`, `/financial/insider-trades`, `/financial/filings`), mark institutional ownership as absent from the contract, report cost from the `X-AISA-Customer-Cost-Micros-USD` header, and use the canonical docs host.
- README lists the published `analyst-estimates` and `insider-trades` routes and the canonical docs host.

## 1.0.1

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
