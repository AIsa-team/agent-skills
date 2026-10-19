# Changelog

## 1.0.1

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.
- Use the MCP endpoint published by https://aisa.one/llms.txt (`https://mcp.aisa.one/mcp`) instead of `tools.aisa.one`, so the skill matches its shared rules block.

## 1.0.0

- Establish the independently versioned baseline and maintenance manifest.
- Preserve the existing skill contract and declare tracked upstream sources.
