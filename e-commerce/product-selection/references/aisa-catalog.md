# AIsa catalog and MCP research contract

Verified **2026-10-12** against anonymous live MCP `search` and
`batch_get_schema` responses, with public OpenAPI contracts as a cross-check.
Twenty selected tool schemas were retrieved successfully. No billable data
operation or quote was executed. Discovery verifies published contracts;
the search responses reported runtime availability as `unknown`, so it does
not establish provider access, data coverage, authentication, or a live price.

## Primary transport

Use the client-managed MCP connection at `https://mcp.aisa.one/mcp`.
Keep OAuth in the native client; do not extract credentials into scripts.
Connect an installed but unauthorized service through the client's native
flow; reauthorize after expiry or a 401. If the connection is absent, provide
this endpoint and the client's setup steps, then wait before live research.
Continue supplied-data planning/calculations with disclosed gaps; do not
silently substitute ordinary web research, HTTP or CLI. Free discovery does
not prove anonymous access or authentication. The official
[MCP guide](https://aisa.one/mcp) describes client-managed browser OAuth.
The public [server inventory](https://mcp.aisa.one/servers)
reviewed on 2026-10-12 describes these root tools:

| Tool | Purpose |
| --- | --- |
| `list_categories` | Free category discovery |
| `search` | Free operation discovery; returns operation IDs and input schemas |
| `get_details` | Free operation contracts, price information and pitfalls |
| `use` | Execute a discovered operation with its arguments |
| `batch_use` | Execute up to 20 independent discovered operations |

Inspect the live connection's tool listing before calling. This endpoint's
operation-based contract is distinct from the original router contract used
to gather the provider observations below. Do not assume the uppercase
`AISA_*` aliases, `batch_get_schema`, `batch_quote`, tool-name call fields,
auto-execution thresholds or session requirements from that contract apply here.

## Discover, inspect, check cost, execute

1. Search one evidence need in plain language, including the provider and
   destination when known. The inventory documents `query`, optional `category`
   and `limit` (1–10); use the current tool schema for exact fields and limits.
2. Take `operation_id` from returned candidates, never derive it from the
   provider names in this reference. Preserve `search_id` when returned.
3. Use `get_details` with the returned operation ID, or its supported batch
   field, for full schemas, current price, availability, side effects and
   pitfalls. Read field descriptions as well as required-property lists.
   Select only executable evidence-retrieval operations.
4. Build the smallest useful localized request from that operation's schema.
   Provider observations below may use an object containing a `body` task
   array; confirm the selected operation's actual input before using it.
5. Check the current price information against existing authorized task/spend
   limits. When authorization does not cover the concrete request and cost/risk,
   obtain it before execution. Missing pricing is not free; an estimate is not
   a hard cap. Refresh pricing when arguments or scope change.
6. Execute with native `use`, or `batch_use` for independent calls. Inspect
   each result; do not silently retry paid calls or expand scope. Keep dependent
   operations sequential.

Illustrative shapes from the public inventory; refresh schemas before use:

```json
{"query":"DataForSEO Amazon keyword search volume by country and language","category":"seo","limit":5}
```

```json
{"operation_id":"<operation-id-returned-by-search>"}
```

```json
{"operation_id":"<operation-id-returned-by-search>","arguments":{},"max_price_usd":0.05,"search_id":"<returned-search-id>"}
```

The empty arguments and USD 0.05 maximum are placeholders, not a valid provider
request, price estimate or granted budget. Replace them with schema-valid
arguments and an authorized ceiling. Batch items use `call_id`, `operation_id`
and `arguments`; confirm where the live batch schema supports price caps.

### Cost and response semantics

The inventory documents `max_price_usd` on `use` to refuse a call above its
maximum before spending. Use only cap fields exposed by the selected tool;
do not invent a batch-wide cap or reuse the other router's micro-USD fields.
Price information does not grant execution authorization. A local budget
comparison alone is not an enforced billing cap.

Record settled cost when the execution response reports it and preserve its
currency/unit. Missing actual cost means unknown, including after an error;
never replace it with an estimate or assume zero. Authentication/access and
provider coverage are established by actual authorized results, not discovery.

## Verified useful operations

These original router IDs are provider-discovery hints observed on the
verification date, not operation IDs for the configured endpoint. Resolve
operation IDs and inspect schemas with its native search/get_details workflow;
the tables are not an execution allowlist or a frozen API schema. Paths below are AIsa relay paths for provenance, not permission to
switch away from MCP.

### Search, market demand, product competition

| Provider / need | Original router discovery hint | AIsa path / current input notes |
|---|---|---|
| Tavily / official evidence and retailer discovery | `post_tavily_search` | `POST /apis/v1/tavily/search`; required `query`; optional `include_domains`, `country`, `max_results`, `search_depth`, date filters. Country is a schema-enumerated lowercase name. Returns `results[]` with URL/title/content. |
| Tavily / exact known pages | `post_tavily_extract` | `POST /apis/v1/tavily/extract`; required `urls` accepts one string or a string array; optional `extract_depth`, `format`; returns `results[].url`, `raw_content`, and failed URLs. |
| Exa / semantic research fallback | `post_exa_search` | `POST /apis/v1/exa/search`; required `query`; optional `includeDomains`, `numResults`, `contents`. Uses camelCase, unlike Tavily. |
| DataForSEO / local Google demand | `post_dataforseo_keywords_gads_search_volume_live` | `POST /apis/v1/dataforseo/keywords_data/google_ads/search_volume/live`; `body[].keywords`, location and language; up to 1,000 keywords, 80 characters / 10 words each. Monthly search volumes, CPC and advertising competition are demand proxies. |
| DataForSEO / product ideas | `post_dataforseo_labs_google_keyword_ideas_live` | `POST /apis/v1/dataforseo/dataforseo_labs/google/keyword_ideas/live`; `body[].keywords` up to 200, location, language, explicit small `limit`. |
| DataForSEO / comparable keyword metrics | `post_dataforseo_labs_google_keyword_overview_live` | `POST /apis/v1/dataforseo/dataforseo_labs/google/keyword_overview/live`; `body[].keywords` up to 700, location and language. `items[].keyword_info` includes search volume, monthly searches, CPC and competition. Missing keywords are unknown. |
| DataForSEO / Amazon demand | `post_dataforseo_labs_amazon_bulk_volume_live` | `POST /apis/v1/dataforseo/dataforseo_labs/amazon/bulk_search_volume/live`; `body[].keywords` up to 1,000, location and language; returns `items[].keyword`, `search_volume`. Supported locales are narrower than all Amazon marketplaces. |
| DataForSEO / Amazon keyword expansion | `post_dataforseo_labs_amazon_related_keywords_live` | `POST /apis/v1/dataforseo/dataforseo_labs/amazon/related_keywords/live`; `body[].keyword`, location and language; `depth` 0–4; `limit` up to 1,000. Keep depth and limit small. |
| DataForSEO / ASIN competitors | `post_dataforseo_labs_amazon_product_competitors_live` | `POST /apis/v1/dataforseo/dataforseo_labs/amazon/product_competitors/live`; `body[].asin`, location and language; `limit` up to 1,000. Identifies search-result competitors; it does not prove sales. |
| DataForSEO / ASIN search footprint | `post_dataforseo_labs_amazon_ranked_keywords_live` | `POST /apis/v1/dataforseo/dataforseo_labs/amazon/ranked_keywords/live`; `body[].asin`, location, language and explicit small `limit`. |
| DataForSEO / seasonality | `post_dataforseo_keywords_trends_explore_live` | `POST /apis/v1/dataforseo/keywords_data/dataforseo_trends/explore/live`; `body[].keywords` up to 5; location, dates or `time_range`, and `type`. Absent location gives global results. |
| DataForSEO / regional interest | `post_dataforseo_keywords_trends_subregion_interests_live` | `POST /apis/v1/dataforseo/keywords_data/dataforseo_trends/subregion_interests/live`; `body[].keywords` up to 5 and localized period. Relative interest is not orders or market size. |
| Semrush / independent search metric check | `get_semrush_keyword_overview` | `GET /apis/v1/semrush/keyword-overview`; required `phrase`, optional `database` defaults to `us`; specify the intended supported database. |

**Coverage cautions:** Amazon Labs related keywords, product competitors and
ranked keywords currently document support for the US, Egypt, Saudi Arabia
and UAE. Bulk search volume documents a wider set of 16 locales, including
the UK, Germany, France, Canada and Australia; verify the exact locale/language
pair per operation. Do not infer one endpoint's coverage from another. Merchant
Amazon language codes such as `en_US` differ from Labs codes such as `en`.

Google Ads can group close variants into combined volumes and omit restricted
or unknown terms. Do not sum overlapping synonyms into a market-size estimate.
Use matching geography, language, period and provider definitions when comparing
markets. Advertising competition and keyword difficulty are not seller density.

### Audience, channels and FX inputs

| Provider / need | Original router discovery hint | AIsa path / current input notes |
|---|---|---|
| Similarweb / domain audience geography | `get_similarweb_website_top_geographies` | `GET /apis/v1/similarweb/website-top-geographies`; required bare `domain`, optional `month` (`YYYY-MM`); country cannot be supplied; fixed top 10 rows. Returns `data.countries[]` with `country_code`, `share`, `visits`. |
| Similarweb / channel scale | `get_similarweb_website_traffic_snapshot` | `GET /apis/v1/similarweb/website-traffic-snapshot`; bare `domain`, optional `month`, `country` only `ww`; four metrics for one month. |
| Similarweb / audience context | `get_similarweb_demographics` | `GET /apis/v1/similarweb/website/demographics`; `domain`, `start_date`, `end_date`, `granularity: "monthly"`; `country` only `ww`, `web_source` only `total`. |
| FRED / historical FX or macro observations | `any_fred_apis_v1_fred_series_observations` | `GET /apis/v1/fred/series/observations`; required verified `series_id`; request `file_type: "json"`, bounded dates/limit, `units: "lin"`. Default format is XML. |
| FRED / confirm units and frequency | `any_fred_apis_v1_fred_series` | `GET /apis/v1/fred/series`; required `series_id`; `file_type: "json"`. Verify exchange-rate direction and observation date before conversion. |

Similarweb's current `country` schemas are **worldwide only (`ww`)**.
Top geographies describes a domain's audience distribution; it does not offer
country-filtered category demand or prove sales. Month defaults use the previous
complete UTC month, which can differ from the freshest provider data; record the
actual returned data month. Access can require the account's GTM subscription.

FRED provides published observations rather than executable FX, card settlement,
or marketplace payout quotes. Prefer the seller's dated actual conversion rate
and fee; use published FX as an explicitly identified planning assumption.

## Pricing coverage and unavailable operations

The current public DataForSEO Merchant contract contains Amazon/Google products,
product details, sellers and Google reviews via `task_post` → `tasks_ready` →
`task_get`. Its limits include Amazon products depth 100 by default, maximum
700; Google Shopping depth 40 by default, maximum 120. Increasing depth and
priority can change cost. These are asynchronous research jobs, not immediate
product observations.

The original router observations for `post_dataforseo_merchant_amazon_products_submit`
and `post_dataforseo_merchant_google_products_submit` both reported
`execution_supported: false` with this reason:
“Asynchronous lifecycle operations are not executable through the synchronous
router.” The retrieved task-ready/result operations have the same restriction.
For the configured endpoint, check its discovered operation availability and
lifecycle before use; do not transfer another router's execution guarantees.
Only submit/poll when the current MCP contract supports that lifecycle and
the work/spend is authorized. Otherwise use public listing extraction. A
successful schema lookup does not imply execution support.

For observed competitor prices, use localized public retailer/marketplace URLs
through discovered search and extraction tools, or seller-supplied exported
listings. Record exact SKU/variant, pack size, currency, tax/shipping treatment,
stock state and observation time. A snippet without a confirmed product page is
weak pricing evidence. If extraction is blocked, return the missing observation
and a collection step; do not invent price, shipping, sales or review counts.

The [public catalog](https://aisa.one/api) currently marks dedicated Shopee,
Lazada, AliExpress and Google Shopping products “Coming Soon”; this is distinct
from DataForSEO's declared Merchant contract. The API reference's eBay operation
is labelled “-test”; it is not a default dependency. No verified specialized
landed-duty, current tariff, shipping quote or product-unit-sales provider was
selected. Retrieve official customs/tax/platform/carrier documentation using
search/extract and label outstanding classification or fee inputs.

## Response checks and source provenance

DataForSEO responses wrap data in `tasks[]`; inspect both top-level and task
`status_code`, `status_message`, and `tasks_error`, then `result`/`items`.
HTTP or router success alone does not establish task-level data success. Preserve
nulls and omissions; empty results are not proof of zero demand. Preserve
retrieval dates, response IDs and provider-specific data dates with evidence.

The original router conservatively flagged several research POST tools `read_only: false` with
the generic side effect “May modify external state; do not retry automatically.”
This includes DataForSEO live keyword/trend/Labs operations, Tavily extract and
Exa search. Inspect their current semantics; permit only evidence-retrieval
operations within authorized research, and retain their no-retry/cost controls.
Do not use a blanket `read_only: true` filter that silently excludes core demand
research; do not permit posting, seller-account changes or task-monitor creation.

Sources verified on 2026-10-12:

- [Configured MCP endpoint](https://mcp.aisa.one/mcp): use its own operation-based tools; provider schema observations above came from original router discovery, not a verified call on this endpoint.
- [DataForSEO public OpenAPI](https://aisa.one/docs/openapi/dataforseo.json): locale descriptions, request/response fields and Merchant lifecycle.
- [Similarweb public OpenAPI](https://aisa.one/docs/openapi/similarweb.json): worldwide restriction, input fields and geography limits.
- [Complete AIsa OpenAPI](https://aisa.one/openapi.yaml): provider/path cross-check including FRED and experimental eBay.
- [AIsa API catalog](https://aisa.one/api): declared providers and Coming Soon distinctions.
- [MCP server inventory](https://mcp.aisa.one/servers): selected endpoint, operation-based calling convention and price-cap description.
