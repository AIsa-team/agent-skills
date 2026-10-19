# Changelog

## 1.1.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.

## 1.1.0

- Repair live-contract compatibility and schema checks; distinguish estimates from final charges, persist requests and task accounting, and add offline regression tests. Breaking: window now returns an unverified calendar candidate with latest_month null instead of probing a paid endpoint; call output separates requested dates from response metadata and --out stdout is JSON.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
