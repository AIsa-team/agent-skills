# Product selection changelog

## 1.0.2

- Add the shared AIsa agent rules block (MCP first with OAuth, direct HTTP as a gated fallback, quote and approval before paid calls, settled cost from the X-AISA-Customer-Cost-Micros-USD header, never paste or print keys); synced from _shared/aisa-rules.md.

## 1.0.1

- Move the skill into the e-commerce category; preserve research and pricing behavior.

## 1.0.0

- Add MCP-first product selection, market comparison and pricing workflows for all three seller starting scenarios.
- Document live AIsa provider coverage and primary-source commerce methods.
- Ship TypeScript research/comparison and pricing helpers, compiled entrypoints and behavioral tests.
- Cover zero-variable-cost margin targets while keeping zero-revenue margins undefined and infeasible targets rejected.
- Add a reusable seller playbook under assets.
- Use `https://mcp.aisa.one/mcp` consistently in instructions, references, playbook and generated research plans; align operation discovery and calling guidance with its catalog.
- Handle native OAuth connection and reauthorization explicitly; keep missing-connection work offline unless the user chooses another research method.
