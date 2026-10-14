# Market and product decisions

## Screen the seller's feasible choices

Capture sourcing origin separately from seller domicile. Record product materials/function, buyer, use case, dimensions/weight, supplier capability, MOQ, lead time, available working capital, channel access and fulfillment model. A seller's existing supply advantage matters more than a universal “best country.” When context is absent, use provisional hypotheses and explain their assumed buyer and fulfillment route.

For market-first requests, start with native-language category searches and customer problems in the named market; do not make market comparison a prerequisite. For product-first requests, use the exact product/variant across markets so specification changes do not create an artificial price advantage. For open requests, narrow broad market hypotheses before detailed SKU research.

Check these gates before launch recommendations:

- **Compliance/access:** sale/import restrictions, classification and origin, tests/certificates, labels, IP, importer/economic operator, marketplace category/account eligibility and relevant packaging obligations. Supplier assurances alone do not establish compliance. Unresolved decisive obligations are unknown, not pass.
- **Fulfillment:** real route quote, dimensional weight, dangerous-goods constraints where relevant, delivery promise, returns address/process and allocation of import charges. Record Incoterm, named place and version for supplier/route quotations; confirm who is importer and who pays.
- **Economics/capital:** validated delivered price can support the seller's target under plausible costs, and cash funds MOQ, inventory, recoverable tax, lead time and payout delay. A positive margin does not prove sufficient working capital.

## Gather evidence that answers a decision

| Question | Useful evidence | Avoid this inference |
| --- | --- | --- |
| Is there demand? | Product-code imports over multiple periods; local keyword volumes/seasonality; actual marketplace transactions when available | Total retail spend or imports equal achievable online sales |
| Can we compete? | Matching variants, landed delivered prices, seller concentration, review complaints, delivery and differentiated features | Review count or rank equals unit sales |
| Can we acquire buyers? | Relevant SERP/listings, local channel usage, traffic country mix, estimated CPC followed by observed conversion | CPC equals CAC or site visits equal sales |
| Can we serve buyers? | Carrier/supplier quote for this route, packaging/weight, marketplace fulfillment charges, local return terms | A country logistics indicator predicts this parcel's delivery |

Localize search phrases by buyer intent, category vocabulary, units and season. Keep keyword volume provider, country/language, period and engine. Google Trends is relative interest; never compare separate normalized queries as absolute demand. Amazon BSR is category/store-specific relative rank. Similarweb is estimated website audience; check each endpoint's geography coverage.

Record an evidence ledger: ID, claim, market/product/channel, provider/tool, source URL or returned record ID, retrieved timestamp, observation period, value/unit, observed vs inferred vs assumed, limitations. Provider observations and multiple web pages repeating one dataset are not independent corroboration. Open primary links behind synthesized answers before adopting legal rules or important numbers.

## Compare finalists

The bundled `rank` helper defaults to demand 25%, economics 35%, competitive gap 20%, operations 20%. These are disclosed planning heuristics, not empirically calibrated probabilities. Grade each dimension 0–5 with a short evidence-backed rationale; 0 is clearly adverse and 5 strongly favorable for this seller. Adjust the analysis when business priorities differ; do not force every question through this scoring helper.

Its input is `{opportunities:[{id,market,product,channel,gates:{compliance,fulfillment,economics},dimensions:{demand,economics,competition,operations}}]}`. Gate values are `pass`, `fail`, `unknown`. Dimension values are `{score:number,evidence:["ledger-id"]}` or `null` when unknown. Record the route and score rationale in the ledger/decision report. See [assets/ranking-example.json](../assets/ranking-example.json) for a complete hypothetical input.

The helper gives missing dimensions an interval [0,5], producing lower/upper scores rather than filling them with a neutral point. Failed gates are blocked; unknown gates or dimensions require investigation. Overlapping intervals and thin evidence should trigger the next useful research step, not confident ranking. Evidence coverage measures completeness, not source quality. Review quality separately and refuse unsupported scores.

## Pilot and update

Choose a small reversible test consistent with the seller's capital and channel. Define thresholds before testing: retained orders, conversion, contribution after CAC, returns, delivery performance and customer complaints. Set test duration to account for seasonality, delivery and return windows; avoid universal conversion/margin benchmarks. Budget research, samples/compliance and pilot inventory separately. Update estimates using observed cohorts and stop if gates fail, contribution is persistently negative or cash exposure exceeds tolerance.

Read [references/sources.md](sources.md) from the skill root for the primary knowledge foundation; refresh facts for the actual route rather than treating this framework as current legal guidance.
