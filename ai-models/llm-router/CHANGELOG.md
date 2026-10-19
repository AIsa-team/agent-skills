# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Use the published Gemini GenerateContent base `https://api.aisa.one/v1beta` and report cost from the `X-AISA-Customer-Cost-Micros-USD` header instead of a response body field.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
