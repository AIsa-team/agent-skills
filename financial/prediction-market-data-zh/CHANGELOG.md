# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Report cost from the `X-AISA-Customer-Cost-Micros-USD` response header instead of a response body field.
- Document which legacy Polymarket/Kalshi/matching-markets routes are absent from the published OpenAPI contract and the published operations to migrate to.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
