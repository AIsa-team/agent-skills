# AIsa product-tracking providers

## Supported scope

This skill supports **Amazon US product observations through DataForSEO Merchant**: exact product identity, available product prices, availability, ratings and public demand signals. Seller-level information is not supported. Other Amazon markets require independent capability and response validation; non-Amazon platforms require an additional adapter.

Historical product observations from **2026-10-16** covered these exact Amazon US variants:

| Product | ASIN | Product search `bought_past_month` |
| --- | --- | --- |
| Logitech M185, Swift Grey | `B004YAVF8I` | 10000 |
| SanDisk Ultra 128GB + adapter, 140 MB/s | `B0B7NTY2S6` | 2000 |
| CeraVe Moisturizing Cream, 19 oz | `B00TTD9BRC` | 100000 |

These values are historical examples, not current observations or exact sales. Preserve the field as a provider-parsed, approximate public purchase signal. [Amazon's sales-trend explanation](https://sellercentral.amazon.com/seller-forums/discussions/t/732ded0cef8e8ee8c2a7caf832bc85f0) describes a broad estimate of customers who bought a product. Exact units, revenue and variant aggregation were not established. Repeated rolling-month badges cannot establish daily sales by subtraction.

## Discovery hints, not execution constants

The default MCP endpoint is `https://mcp.aisa.one/mcp`. Reuse the user's working connection and inspect its actual schemas. Use live discovery to obtain current identifiers and request shapes. These names and AIsa relay paths identify the product operations observed on the historical verification date:

| Need | Observed router tool | AIsa relay path |
| --- | --- | --- |
| Find exact listings and public purchase signal | `any_dataforseo_apis_v1_dataforseo_merchant_amazon_a50cdd` | `POST /apis/v1/dataforseo/merchant/amazon/products/live/advanced` |
| Verify product/variant and available details | `any_dataforseo_apis_v1_dataforseo_merchant_amazon_bc8317` | `POST /apis/v1/dataforseo/merchant/amazon/asin/live/advanced` |

Verify `execution_supported`, required arguments and response fields before collection. Older asynchronous `task_post`/`task_get` routes are not interchangeable with the synchronous live routes. Their availability must not be inferred from a similarly named endpoint.

The observed live request is an object with a `body` task array. The Amazon US example uses one task:

```json
{
  "body": [{
    "asin": "B004YAVF8I",
    "location_code": 2840,
    "language_code": "en_US",
    "se_domain": "amazon.com"
  }]
}
```

Replace the example ASIN with the user's resolved target. Product search instead takes `keyword`; historical requests used `depth: 10` and `max_crawl_pages: 1`, but responses included more than ten rows. Do not treat depth as a strict coverage or spending cap. Other markets need independently resolved location/language values and validation; do not reuse US localization.

Current schemas and quotes take precedence over historical examples. Obtain a quote for the exact tools and arguments before paid execution. An example request does not authorize a billable call. Preserve settled charges when returned; do not hard-code historical charges as a billing guarantee.

## Response semantics

AIsa wraps each result with `successful`, `call_id`, `request_id`, `tool`, optional `customer_cost_micros_usd` and `data`. DataForSEO's `data` contains top-level `status_code`, `tasks_error` and `tasks[]`. Check task-level `status_code`, `status_message` and `result` too. The observed provider success code was `20000`.

Each task records its provider route in `path`, input in `data`, task `id` and source observations in `result[]`. Keep result `se_domain`, location/language, `datetime` and `check_url`. Do not replace the provider timestamp with the local collection time.

The detail endpoint can return child/parent ASINs, model/UPC/GTIN where published, `is_available` and product ratings. Search can return product prices or price ranges, rating/feedback counts, result positions and `bought_past_month`. Preserve missing fields as unknown. Verify the child ASIN and variant before using any row; title similarity alone does not establish identity.

Search `rank_absolute` describes result position, not category sales rank. Historical category Best Sellers Rank appeared in free-form product-information fields. The helper does not parse a typed category-rank series or include opaque product-information fields in its normalized report. Do not claim the helper tracks category sales rank automatically.

Search rating/feedback counts may be rounded compared with detail counts. Build comparisons only within the same source, query, locale, row type and metric. Sponsored and organic rows are distinct. More rows do not establish additional product variants or broader marketplace coverage.

Keep listed price, regular price, ranges and currency distinct. A scalar change requires one comparable point-price row in each observation and a known matching currency. Preserve ranges without substituting a midpoint, and retain duplicate-row ambiguity rather than choosing a convenient value. Missing shipping and tax remain unknown; product prices do not automatically represent a final delivered total.

Product availability describes the observed listing, not inventory quantity. Missing or failed observations cannot establish a stockout. Public purchase signals, result positions and feedback growth are not transaction records.

## Additional evidence

The bundled helper accepts only the product routes above. Additional provider operations or public-page extraction require their own validated input adapter before they can become stored tracking series. Do not imply support merely because an operation appears in AIsa's catalog.

Public references: [AIsa catalog](https://aisa.one/api), [AIsa DataForSEO contract](https://aisa.one/docs/openapi/dataforseo.json), [DataForSEO live product search](https://docs.dataforseo.com/v3/merchant/amazon/products/live/advanced/), [DataForSEO live product details](https://docs.dataforseo.com/v3/merchant/amazon/asin/live/advanced/). Actual execution and coverage depend on the user's current connection and account.
