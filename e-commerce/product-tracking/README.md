# Product tracking

Track an exact Amazon US product using AIsa, with a local SQLite history for product price and availability comparisons. Product ratings, search positions and public purchase signals add context. Seller-level information is not supported. Other Amazon markets require validation; other platforms require an adapter.

Start with [SKILL.md](SKILL.md). Live research uses the native AIsa connection, defaulting to `https://mcp.aisa.one/mcp`; the Python 3.10+ helper stores and compares supplied product results without network access or third-party dependencies. Recurring runs require a host scheduler and persistent storage. Existing saved history is preserved, while reports use only product observations.

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the provider catalog.
