# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.

## 1.0.0

- Use `https://mcp.aisa.one/mcp` as the default AIsa MCP endpoint.
- Track product-level pricing, availability, ratings and demand with a persistent watchlist and immutable snapshots.
- Exclude seller-level collection and reporting; ignore legacy seller snapshots in reports without deleting history.
- Document authorized recurring collection, provenance and costs; ship dependency-free Python helpers and offline behavioral tests.
