# Product selection playbook

Use this playbook to turn the skill's research into a market entry decision. Copy it into the seller's project and replace the bracketed fields with verified evidence or clearly named assumptions. Example JSON files bundled with the skill are hypothetical; their countries, FX, rates and costs are not recommendations.

## 1. Write the seller brief

| Item | Record |
| --- | --- |
| Starting scenario | No preference / market chosen / product chosen / both chosen |
| Fixed choices | [Market, product specification, channel, or none] |
| Seller and sourcing | [Seller domicile, source origin, supplier strengths, lead time, MOQ] |
| Budget and cash | [Research spend authorization, sample/compliance budget, inventory cash, acceptable exposure] |
| Route and channel | [Marketplace/store access, importer, fulfillment, Incoterm/version/named place, returns route] |
| Product constraints | [Materials, size/weight, buyer, restricted categories, certifications, IP] |
| Economics target | [Currency, contribution target, profit per placed order, capital constraints] |

Unknowns remain visible. Request the few details that would change the decision; continue exploratory screening with clearly stated assumptions.

## 2. Follow the correct scenario

**No preference:** use sourcing strengths and budget to generate 3–5 market hypotheses. Screen channel access, freight/service and product restrictions. Pair feasible markets with 2–3 product families; narrow to the strongest combinations before detailed SKU research. A low price supplier or a large population is insufficient evidence.

Example prompt: “I am starting cross-border selling and have no market or product in mind. My sourcing strengths are [details] and my budget is [amount]. Suggest a few entry hypotheses and show what would validate them.”

**Market chosen:** retain [destination]. Research native-language needs, local channels and matching products. Compare candidates by buyer problem, differentiation, shipping/compliance burden and economics. Explain where this market is unsuitable without silently changing the assignment.

Example prompt: “I want to enter [market]. Help me pick products for [channel/route] and calculate delivered prices from my costs.”

**Product chosen:** retain [exact specification]. Find local use cases and keyword equivalents, screen 3–5 feasible destinations and compare the same variant/channel assumptions. Create separate pricing cases for each tax, currency, fee and route combination.

Example prompt: “I source [product/specification] at [cost/currency]. Where could I sell it, and what price would support [target] after freight, fees and returns?”

**Both chosen:** validate the pair and compare plausible fulfillment/channel options. Move directly to missing evidence and pricing rather than repeating broad market selection.

## 3. Gather evidence through AIsa MCP

Reuse the native connection to `https://mcp.aisa.one/mcp` and complete client-managed OAuth when needed. Reauthorize after expiry or a 401. If the connection is missing or authorization fails, provide connection steps and wait before live research; continue only supplied-data offline work with visible gaps. Do not silently substitute ordinary web research, HTTP or CLI. Use `search` → `get_details` → check current price and authorized spend → `use` or `batch_use`, following the tool schemas exposed by this connection. Preserve returned operation IDs and search context; use the supported spend-cap fields when required.

Start with official-source market and rule research using Tavily. Add DataForSEO localized demand and executable competitor/product tools. Extract public listing evidence when product task endpoints are not executable through MCP. Use Similarweb for website/channel context only when relevant and respect endpoint geography limits. Check current price information for the exact requests and act within the already-authorized research budget. Do not silently expand or retry paid calls.

Record each decision-relevant observation:

| Evidence ID | Claim/value/unit | Market/product/channel | Tool/provider and source | Observed period / retrieved at | Fact / assumption / inference | Limit |
| --- | --- | --- | --- | --- | --- | --- |
| [ID] | [value] | [scope] | [URL/record ID] | [dates] | [status] | [coverage/uncertainty] |

Keep search interest, keyword volume, website traffic, listings and sold transactions distinct. Record both supporting and contrary evidence. Validate current rules with destination authorities and channel fees with the destination marketplace.

## 4. Apply feasibility gates

| Gate | Evidence needed | Status / next action |
| --- | --- | --- |
| Product/channel access | [Safety, labeling, classification, IP, importer/operator, account/category eligibility] | Pass / fail / unknown |
| Delivery and returns | [Route quote, dimensional weight, service promise, local returns process and responsibilities] | Pass / fail / unknown |
| Economics and cash | [Comparable prices, cost model, downside case, MOQ/payout/tax funding] | Pass / fail / unknown |

A failed gate stops this proposed route; an unknown gate requires investigation before a launch recommendation. Do not score away a compliance or loss-making issue.

## 5. Build comparable delivered prices

Choose a scope: [destination], [channel], [condition], [exact variant/material/size], [date window]. Separate ordinary asking prices, promotional prices and sold prices. Record pack count, charged shipping, tax inclusion, currency, delivery promise and listing identity; exclude unavailable or mismatched offers.

Run `compare-prices` with the schema in `references/pricing-model.md` to convert FX/tax/shipping/pack quantity. Report n, exclusions and p25/median/p75. A small sample is descriptive evidence, not a reliable sales forecast. If buyer tax varies by address, state the comparison address/tax assumption.

## 6. Solve unit economics

Prepare explicit order costs: goods, inbound freight, packaging, verified duty, import VAT/recovery, fulfillment/outbound, CAC, fixed fees, other variable costs and allocated overhead. Confirm buyer shipping is in the modeled order price. Distinguish retail output tax from import VAT and the marketplace fee base. Avoid double-counting payment processing or shipping already in fulfillment.

Run from the installed skill root:

```bash
node dist/cli.js --help
node dist/cli.js plan assets/explore-input.json
node dist/cli.js price assets/pricing-example.json
node dist/cli.js rank assets/ranking-example.json
```

Replace example files with the seller's evidence. The helpers operate offline, need Node.js 22+, and do not call AIsa. For a price input use `node dist/cli.js price /absolute/seller-input.json`. For several complete cases use `{scenarios:[{name,input}]}`. Run every final rounded offered price through the model again.

| Case | Delivered buyer price | Contribution before overhead | Profit after overhead | Break-even / target floor | CAC ceiling | Recoverable tax funding |
| --- | --- | --- | --- | --- | --- | --- |
| Base | [amount/currency] | [amount and margin] | [amount] | [amount] | [amount] | [cash/timing] |
| Downside | [amount/currency] | [amount and margin] | [amount] | [amount] | [amount] | [cash/timing] |

Explain downside changes and why they are plausible. If the floor exceeds comparable prices, record “not viable under current assumptions” and the concrete gap. Options may include sourcing, packaging, acquisition, route or channel changes; a lower unsupported margin target does not create evidence of buyer demand.

## 7. Choose the next action

| Pair | Evidence coverage | Demand / competitive gap | Delivery/access gates | Base/downside economics | Decision |
| --- | --- | --- | --- | --- | --- |
| [market × product × channel × route] | [sources/gaps] | [rationale] | [status] | [results] | Investigate / pilot / reject |

The optional `rank` helper uses disclosed heuristic weights and uncertainty intervals. Review source quality and overlapping intervals; a top score is not an investment guarantee. Lead the recommendation with the actual decision and the unresolved fact most likely to reverse it.

## 8. Define a bounded pilot

Record [budget], [quantity], [channel], [duration], [delivery and return observation window] and [cash limit]. Set seller-specific continuation criteria before the test: retained orders, conversion, contribution after CAC, refunds/returns, delivery performance and customer complaints. Record a stop threshold and who owns each next action. Do not order inventory, create listings, launch ads or contact suppliers without the seller's authorization for that action.

After the pilot, replace estimated CAC/returns/costs with observed cohorts. Re-run pricing, check current fees/rules and reconsider the choice. Successful revenue with negative contribution is not a successful pilot.

## Decision record to deliver

**Recommendation:** [action, chosen pair, confidence/decision stage].

**Why:** [the strongest evidence and seller-specific advantage, with source dates].

**Pricing:** [delivered consumer range, proposed exact price, contribution, overhead profit, floor, downside and currency].

**Assumptions/gaps:** [explicit cost/tax/route assumptions, data gaps, contradictory observations and next verification].

**Pilot:** [budget/quantity, gates and stop/continue measures].

**Evidence appendix:** [ledger and current authority/channel references].
