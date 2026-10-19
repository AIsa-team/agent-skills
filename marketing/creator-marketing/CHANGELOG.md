# Changelog

## 0.0.2

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Assert the User-Agent format in tests instead of a pinned skill version, so version bumps do not break the suite.

## 0.0.1

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
