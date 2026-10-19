# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Mark the skill deprecated: the bundled client targets `/v1/models/{model}:generateContent` and the `/apis/v1/services/aigc/*` video routes, which are not in the published OpenAPI contract (Gemini is served under `/v1beta`; video generation is documented as `/v1/video/generations`).

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
