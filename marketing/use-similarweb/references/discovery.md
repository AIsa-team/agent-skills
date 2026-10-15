# Discovering the live contract

Use the public [Similarweb OpenAPI contract](https://aisa.one/docs/openapi/similarweb.json) for current
routes, request schemas, constraints, examples, and response declarations. Its route count and structure
can change; successful discovery is not proof that every route has been executed or is accessible to the key.

## Commands and paths

`discover` lists the available GET operations. `describe ROUTE` exposes the selected operation's parameters,
`constraints`, examples, `responses`, referenced `response_definitions`, and `response_pending` metadata.

The client accepts short paths such as `/website/traffic-engagement`, legacy `/similarweb/...` paths,
and full `/apis/v1/similarweb/...` paths. It combines the contract's server URL with the actual path;
do not prepend another `/apis/v1` when it is already present.

## Reading a route

- Include the required parameters and use the schema's types, enums, bounds, and defaults.
- Read `x-aisa-constraints` as well as operation and parameter descriptions. Important rules may appear
  only in extension fields, even when the operation description is empty.
- Parameter examples and code samples show request shape. Replace example domains and account-specific
  identifiers; do not treat example dates as the latest available data month.
- Use response schemas and examples to interpret returned fields. A `response_pending` declaration means
  an authoritative public success schema is still missing; inspect the actual response without inventing fields.

`check ROUTE name=value …` performs the client's supported local schema checks. It may fetch or refresh
the public contract, but does not execute a Similarweb request. Passing this check or receiving a quote
does not verify account entitlement, provider data availability, or every upstream date rule.

## Dates and availability

Preserve explicit user dates. If the user asks for the latest data and no confirmed availability is known,
`window` returns `candidate_month` as the previous complete UTC calendar month, `latest_month: null`, and
`availability: "unverified"`, along with relevant contract constraints and default policies.

This command does not send an authenticated or paid request. The candidate may be newer than the provider's
available data. Do not intentionally execute an invalid paid request to discover an allowed date range.
If an authorized request returns a date or availability error, use that evidence to explain the limitation;
changing the user's requested period still requires that the resulting task remain within their intent.

## Caching and changes

The cache lives at `$AISA_SIMILARWEB_CACHE` or `~/.cache/aisa-similarweb`. The client respects the contract's
cache lifetime and revalidates cached content with its ETag when available. `discover --refresh` requests
a new copy. If a network failure causes use of a cached copy, the client warns that discovery is stale.

A rejected request does not necessarily mean the contract changed. Inspect the actual error, refresh once
when drift is plausible, and compare the request with the refreshed schema and constraints. Do not loop
through refreshes or paid retries when the rejection is an access or data-availability problem.

## MCP alternative

The Similarweb module endpoint is `https://mcp.aisa.one/similarweb/mcp`. If using an existing MCP connection,
inspect its current `tools/list` rather than assuming tool names or schema parity. This skill's client uses
REST so it can preserve response billing headers and request records; apply the same authorization and
uncertain-outcome handling to any alternative client.
