# Pricing helper contract

Run `node dist/cli.js price /absolute/input.json` from the skill root. Input/output use order totals including seller-charged shipping. A one-item/one-unit order makes these unit prices; bundles need their own per-order costs. Numbers are decimal rates (`0.2`, not `20`). Every cost/rate is explicit; use a known or clearly labeled hypothetical zero, never erase unknowns. Keep provenance and assumption status in the accompanying decision ledger, not extra unsupported keys in the strict pricing JSON.

## Input

See [assets/pricing-example.json](../assets/pricing-example.json) for a complete hypothetical example. These inputs are required:

| Field | Contract |
| --- | --- |
| `settlementCurrency` | Uppercase three-letter currency, e.g. `USD`. Choose one consistent destination comparison currency; convert all costs into it. |
| `tax` | `{salesTaxRate,priceIncludesTax}`. The rate is the actual destination tax applicable to this order, supplied externally. |
| `costs` | Money values for `product`, `inboundFreight`, `packaging`, `customsDuty`, `fulfillment`, `outboundShipping`, `customerAcquisition`, `fixedOrderFees`, `otherPerOrder`, `overheadAllocation`. All ten required. Avoid counting the same fulfillment/transport charge twice. |
| `importVat` | `{amount:Money,recoverableRate}`; recovery share in [0,1] requires documentation or an explicit scenario. Import VAT is separate from retail output tax. |
| `returns` | `{rate,incrementalCost:Money,productRecovery:Money}`; full-refund probability [0,1]. Recovery is the conservative value of returned inventory and cannot exceed product cost. |
| `fees` | Array of `{name,rate,basis,refundOnReturnRate}`; explicit `[]` for no percentage fees. `basis` is `grossPrice` (buyer checkout including tax) or `exTaxPrice`; refund share [0,1]. Fixed charges go in `fixedOrderFees`. |
| `target` | `{contributionMargin,profitPerOrder:Money}`. Margin before allocated overhead; desired profit per placed order after overhead. Both are seller targets, not market benchmarks. |
| `offeredPrice` | Optional nonnegative order price in settlement currency, following `priceIncludesTax`; evaluated separately from calculated floors. |

Money is `{amount:number,currency:string,fxToSettlement?:number}`. Across currencies, FX is required and means **settlement units per one source unit**: CNY 70 × USD/CNY 1/7 = USD 10. Same-currency FX, if supplied, must be 1. Rates should reflect payout/sourcing spread and date where applicable; separately include conversion fees only when not already reflected in FX.

For comparisons with tax-inclusive delivered prices, compare `buyerCheckoutPrice`. When a target floor is tax-exclusive, convert its checkout total before comparing. Do not force price points to a currency-independent `.99` ending or assume two decimal places for every currency.

## Model

Let P be the listed order price, t output-tax rate, q full-refund probability, and V all per-placed-order costs before overhead including unrecoverable import VAT plus `q × (incremental return handling − product recovery)`. Let H be allocated overhead. No refund amount is added to return handling because retained revenue already excludes refunded orders.

- Ex-tax price factor E = `1/(1+t)` if P includes tax, otherwise 1.
- Buyer checkout factor G = 1 if P includes tax, otherwise `1+t`.
- Retained revenue coefficient A = `(1−q) × E`.
- Fee coefficient B = sum of `fee.rate × (G or E for its basis) × (1−q × fee.refundOnReturnRate)`.
- Expected retained revenue = `A × P`; contribution = `(A−B) × P − V`; profit after overhead = contribution − H.
- Contribution break-even = `V/(A−B)`; allocated-cost break-even = `(V+H)/(A−B)`.
- Contribution-margin target price = `V/(A−B−marginTarget×A)`.
- Profit target price = `(V+H+profitTarget)/(A−B)`; final target is the greater of the two.

Nonpositive contribution denominators and negative margin denominators are infeasible and rejected. A zero margin denominator is also infeasible when `V > 0`. When both `V` and the margin denominator are zero, the margin holds at any positive retained revenue and its margin-price floor is a zero infimum; zero revenue itself has no defined margin and cannot meet a positive margin target. At an offered price, the helper also gives a total CAC ceiling meeting both targets and a signed shortfall before clamping it to zero. A ceiling is not a prediction of achievable acquisition cost. Keep unrounded calculations internally; round a proposed consumer price upward as appropriate and re-evaluate that exact price.

The economics output separates unrecoverable import VAT cost from recoverable VAT cash funding. This is a per-order tax funding amount, not a complete working-capital forecast: inventory, payout lag, VAT-recovery timing and financing still need a cash plan.

## Boundaries and scenarios

The linear model assumes one output-tax treatment, full refunds, proportional price-based fees, one declared refund policy per fee and constant costs/CAC. Confirm percentage-fee taxes and what the base contains. A fee base excluding collected tax uses `exTaxPrice`; a base including tax uses `grossPrice`. Marketplace collections do not turn tax into seller revenue.

It does not resolve HS classification, origin preferences, duty valuation, changing import rules, tax nexus/registration, minimum/tiered fees, partial refunds, mixed shipping tax rates, storage age or demand elasticity. Obtain current duty and import-tax amounts using their separate applicable bases and exact route; add special duties, brokerage and fees once. For a fee tier, model the applicable tier and verify the solved price stays inside it; otherwise use the next tier or a separately validated numeric model. Do not compress a nonlinear fee into an invented constant rate.

Run complete named inputs as `{scenarios:[{name:"base",input:{...}},{name:"downside",input:{...}}]}`. Use documented or clearly hypothetical shocks, not universal defaults. If import-VAT recovery is unknown, test recoverable and unrecoverable cases and mark the conclusion provisional. Include adverse freight, returns, FX and CAC changes when they could reverse the choice.

## Comparable prices

Run `node dist/cli.js compare-prices /absolute/comparables.json`. The required shape is:

```json
{
  "settlementCurrency": "EUR",
  "scope": {
    "market": "Germany", "channel": "Amazon.de", "condition": "new",
    "variant": "same-material-size-specification",
    "startDate": "2026-10-01T00:00:00Z", "endDate": "2026-10-12T23:59:59Z"
  },
  "comparables": [{
    "id": "seller-listing-variant-id", "market": "Germany", "channel": "Amazon.de",
    "condition": "new", "variant": "same-material-size-specification",
    "observedAt": "2026-10-12T12:00:00Z",
    "price": {"amount": 20, "currency": "EUR"},
    "shipping": {"amount": 0, "currency": "EUR"}, "unitsPerPack": 1,
    "tax": {"priceIncludesTax": true, "shippingIncludesTax": true}
  }]
}
```

This is an illustrative listing. Match scope fields exactly and use valid ISO timestamps. `tax.salesTaxRate` is required when either price or shipping is ex-tax; omit it when both are already tax inclusive so no unused tax assumption is invented. The helper includes tax where needed, adds shipping, converts FX, divides by units per pack, and keeps the newest valid observation per ID. Missing price/shipping, invalid values, mismatches and out-of-window rows are excluded with reasons. Quartiles use linear interpolation; n<5 receives a small-sample warning (a heuristic).

The script cannot verify that a listing ID, product match or source is authentic. Prefilter using actual specification, seller identity, availability, delivery promise and evidence type. Keep sold prices separate from asking prices, and promotional/coupon prices separate from ordinary prices. One duplicated listing with different arbitrary IDs is not independent evidence. Report sample size/coverage; quartiles are observed descriptive statistics, not buyer willingness-to-pay or sales forecasts.
