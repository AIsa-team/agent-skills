/**
 * Deterministic order economics, not a worldwide tax or demand model.
 *
 * All costs and rates must be explicit: use amount: 0 for a VERIFIED zero;
 * undefined/null is never interpreted as free. Money conversion is
 * amount * fxToSettlement, where FX is destination units per source unit.
 *
 * Prices cover the whole order, including seller-charged shipping. Gross fee
 * bases include destination sales tax; exTaxPrice bases exclude it. Returns
 * fully refund revenue/tax, but a fee is refunded only to the extent explicitly
 * specified. Costs are incurred for every placed order. Product recovery on a
 * return is capped at product cost; freight/duties/CAC are not recovered twice.
 *
 * Contribution excludes allocated fixed overhead. The target contribution
 * margin uses expected retained ex-tax revenue; the profit floor applies after
 * overhead. Duty and import VAT are supplied amounts calculated outside this
 * module from verified customs bases. Only unrecoverable import VAT is a cost.
 */

export interface Money {
  amount: number;
  currency: string;
  /** Required across currencies; settlement units per origin currency unit. */
  fxToSettlement?: number;
}

export interface PricingInput {
  settlementCurrency: string;
  tax: { salesTaxRate: number; priceIncludesTax: boolean };
  costs: {
    product: Money;
    inboundFreight: Money;
    packaging: Money;
    customsDuty: Money;
    fulfillment: Money;
    outboundShipping: Money;
    customerAcquisition: Money;
    fixedOrderFees: Money;
    otherPerOrder: Money;
    overheadAllocation: Money;
  };
  importVat: { amount: Money; recoverableRate: number };
  returns: { rate: number; incrementalCost: Money; productRecovery: Money };
  fees: Array<{
    name: string;
    rate: number;
    basis: "grossPrice" | "exTaxPrice";
    /** Share of this fee refunded on a returned order; explicit 0 means none. */
    refundOnReturnRate: number;
  }>;
  target: { contributionMargin: number; profitPerOrder: Money };
  /** Same currency and inclusive/exclusive convention as the output prices. */
  offeredPrice?: number;
}

export interface PriceEvaluation {
  listedOrderPrice: number;
  buyerCheckoutPrice: number;
  exTaxOrderPrice: number;
  expectedRetainedRevenue: number;
  expectedPriceBasedFees: number;
  expectedContribution: number;
  profitAfterOverhead: number;
  contributionMargin: number | null;
  meetsTarget: boolean;
  /** Maximum total CAC satisfying both targets; 0 if no nonnegative CAC works. */
  customerAcquisitionCeiling: number;
  /** Can be negative: a shortfall remains even with CAC equal to zero. */
  acquisitionBudgetBeforeClamping: number;
}

export interface PricingResult {
  currency: string;
  priceBasis: "taxInclusiveOrderTotal" | "taxExclusiveOrderTotal";
  contributionBreakEvenPrice: number;
  breakEvenPrice: number;
  targetPrice: number;
  targetPrices: { forContributionMargin: number; forProfitPerOrder: number };
  economics: {
    retainedRevenueCoefficient: number;
    priceFeeCoefficient: number;
    contributionCoefficient: number;
    costPerPlacedOrderBeforeOverhead: number;
    overheadAllocation: number;
    costPerPlacedOrderAfterOverhead: number;
    returnCostAdjustment: number;
    importVatPaid: number;
    /** Funding tied up before recovery, not an expense or full cash-flow model. */
    recoverableImportVatCash: number;
    unrecoverableImportVat: number;
    customerAcquisitionCost: number;
  };
  offeredPrice?: PriceEvaluation;
  assumptions: string[];
  warnings: string[];
}

type RecordValue = Record<string, unknown>;

function object(value: unknown, path: string): RecordValue {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${path} must be an object`);
  }
  return value as RecordValue;
}

function keys(value: RecordValue, allowed: readonly string[], path: string): void {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) throw new TypeError(`${path}.${key} is not supported`);
  }
}

function number(value: unknown, path: string, minimum = 0, maximum = Infinity): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < minimum || value > maximum) {
    throw new TypeError(`${path} must be a finite number in [${minimum}, ${maximum}]`);
  }
  return value;
}

function finite(value: number, path: string): number {
  if (!Number.isFinite(value)) throw new RangeError(`${path} exceeds finite arithmetic`);
  return value;
}

function boolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") throw new TypeError(`${path} must be a boolean`);
  return value;
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new TypeError(`${path} must be a nonempty string`);
  }
  return value;
}

function currency(value: unknown, path: string): string {
  const code = string(value, path);
  if (!/^[A-Z]{3}$/.test(code)) throw new TypeError(`${path} must be a three-letter uppercase currency code`);
  return code;
}

function money(value: unknown, path: string, settlement: string): number {
  const parsed = object(value, path);
  keys(parsed, ["amount", "currency", "fxToSettlement"], path);
  const amount = number(parsed.amount, `${path}.amount`);
  const source = currency(parsed.currency, `${path}.currency`);
  let fx = 1;
  if (source !== settlement) {
    fx = number(parsed.fxToSettlement, `${path}.fxToSettlement`, Number.MIN_VALUE);
  } else if (parsed.fxToSettlement !== undefined) {
    fx = number(parsed.fxToSettlement, `${path}.fxToSettlement`, 1, 1);
  }
  return finite(amount * fx, `${path} converted amount`);
}

const COST_NAMES = [
  "product", "inboundFreight", "packaging", "customsDuty", "fulfillment",
  "outboundShipping", "customerAcquisition", "fixedOrderFees", "otherPerOrder", "overheadAllocation",
] as const;

export function calculatePricing(input: unknown): PricingResult {
  const data = object(input, "input");
  keys(data, ["settlementCurrency", "tax", "costs", "importVat", "returns", "fees", "target", "offeredPrice"], "input");
  const settlement = currency(data.settlementCurrency, "settlementCurrency");
  const tax = object(data.tax, "tax");
  keys(tax, ["salesTaxRate", "priceIncludesTax"], "tax");
  const salesTax = number(tax.salesTaxRate, "tax.salesTaxRate");
  const inclusive = boolean(tax.priceIncludesTax, "tax.priceIncludesTax");
  const exTaxFactor = inclusive ? 1 / (1 + salesTax) : 1;
  const grossFactor = inclusive ? 1 : finite(1 + salesTax, "gross tax factor");
  const rawCosts = object(data.costs, "costs");
  keys(rawCosts, COST_NAMES, "costs");
  const costs = {} as Record<(typeof COST_NAMES)[number], number>;
  for (const key of COST_NAMES) costs[key] = money(rawCosts[key], `costs.${key}`, settlement);

  const vat = object(data.importVat, "importVat");
  keys(vat, ["amount", "recoverableRate"], "importVat");
  const importVatPaid = money(vat.amount, "importVat.amount", settlement);
  const vatRecoveryRate = number(vat.recoverableRate, "importVat.recoverableRate", 0, 1);
  const recoverableImportVatCash = importVatPaid * vatRecoveryRate;
  const unrecoverableVat = importVatPaid * (1 - vatRecoveryRate);
  const returns = object(data.returns, "returns");
  keys(returns, ["rate", "incrementalCost", "productRecovery"], "returns");
  const returnRate = number(returns.rate, "returns.rate", 0, 1);
  const returnHandling = money(returns.incrementalCost, "returns.incrementalCost", settlement);
  const recovery = money(returns.productRecovery, "returns.productRecovery", settlement);
  if (recovery > costs.product) throw new RangeError("returns.productRecovery cannot exceed incurred product cost");
  const returnAdjustment = finite(returnRate * (returnHandling - recovery), "return cost adjustment");
  const beforeOverhead = finite(
    COST_NAMES.filter((key) => key !== "overheadAllocation").reduce((sum, key) => sum + costs[key], 0) +
      unrecoverableVat + returnAdjustment,
    "cost per placed order before overhead",
  );
  const afterOverhead = finite(beforeOverhead + costs.overheadAllocation, "cost per placed order after overhead");
  const retainedRevenueCoefficient = (1 - returnRate) * exTaxFactor;
  if (!Array.isArray(data.fees)) throw new TypeError("fees must be an explicit array; use [] for no percentage fees");
  const feeNames = new Set<string>();
  const feeCoefficient = finite(data.fees.reduce((sum: number, value: unknown, index: number) => {
    const path = `fees[${index}]`;
    const fee = object(value, path);
    keys(fee, ["name", "rate", "basis", "refundOnReturnRate"], path);
    const name = string(fee.name, `${path}.name`);
    if (feeNames.has(name)) throw new TypeError(`${path}.name duplicates ${name}`);
    feeNames.add(name);
    const rate = number(fee.rate, `${path}.rate`, 0, 1);
    const refunded = number(fee.refundOnReturnRate, `${path}.refundOnReturnRate`, 0, 1);
    if (fee.basis !== "grossPrice" && fee.basis !== "exTaxPrice") {
      throw new TypeError(`${path}.basis must be grossPrice or exTaxPrice`);
    }
    return sum + rate * (fee.basis === "grossPrice" ? grossFactor : exTaxFactor) * (1 - returnRate * refunded);
  }, 0), "price fee coefficient");
  const contributionCoefficient = retainedRevenueCoefficient - feeCoefficient;
  if (contributionCoefficient <= 0) {
    throw new RangeError("No finite break-even price: retained revenue minus price-based fees is nonpositive");
  }
  const target = object(data.target, "target");
  keys(target, ["contributionMargin", "profitPerOrder"], "target");
  const margin = number(target.contributionMargin, "target.contributionMargin", 0, 1);
  const profitFloor = money(target.profitPerOrder, "target.profitPerOrder", settlement);
  const marginDenominator = contributionCoefficient - margin * retainedRevenueCoefficient;
  if (marginDenominator < 0 || (marginDenominator === 0 && beforeOverhead > 0)) {
    throw new RangeError("No finite target price: target margin leaves a nonpositive pricing denominator");
  }
  // With no variable costs, the maximum achievable margin holds at any
  // positive retained revenue; its price floor is a zero infimum, not 0/0.
  const marginPrice = marginDenominator === 0 ? 0 : finite(beforeOverhead / marginDenominator, "target margin price");
  const profitPrice = finite((afterOverhead + profitFloor) / contributionCoefficient, "target profit price");
  const result: PricingResult = {
    currency: settlement,
    priceBasis: inclusive ? "taxInclusiveOrderTotal" : "taxExclusiveOrderTotal",
    contributionBreakEvenPrice: finite(beforeOverhead / contributionCoefficient, "contribution break-even price"),
    breakEvenPrice: finite(afterOverhead / contributionCoefficient, "full-cost break-even price"),
    targetPrice: Math.max(marginPrice, profitPrice),
    targetPrices: { forContributionMargin: marginPrice, forProfitPerOrder: profitPrice },
    economics: {
      retainedRevenueCoefficient,
      priceFeeCoefficient: feeCoefficient,
      contributionCoefficient,
      costPerPlacedOrderBeforeOverhead: beforeOverhead,
      overheadAllocation: costs.overheadAllocation,
      costPerPlacedOrderAfterOverhead: afterOverhead,
      returnCostAdjustment: returnAdjustment,
      importVatPaid,
      recoverableImportVatCash,
      unrecoverableImportVat: unrecoverableVat,
      customerAcquisitionCost: costs.customerAcquisition,
    },
    assumptions: [
      "All supplied costs are incurred for every placed order; return handling and product recovery are incremental.",
      "Returns fully refund the order revenue and destination sales tax; percentage fees follow each explicit refund rate.",
      "All shipping charged to the buyer is included in the order price and shares its declared sales-tax treatment.",
      "Contribution margin excludes allocated fixed overhead; profit per order includes that allocation.",
      "Duty/import VAT are supplied input amounts requiring route-specific verification; only the stated unrecoverable import VAT share is an economic cost.",
    ],
    warnings: [
      "No demand, sales volume, cash-flow, customs classification, or worldwide tax liability is forecast by this model.",
      "Validate category-specific fees, fee taxes, minimum fees, refund policy, VAT recovery, and tax/fee bases before using a quote.",
      "Output prices are unrounded mathematical thresholds; round upward using the destination currency's minor unit and re-evaluate.",
    ],
  };
  if ((marginDenominator === 0 && beforeOverhead === 0) || (result.targetPrice === 0 && margin > 0)) {
    result.warnings.push("The zero-cost contribution-margin price floor is an infimum; a positive margin still requires an offered price with positive retained revenue.");
  }
  if (data.offeredPrice !== undefined) {
    const price = number(data.offeredPrice, "offeredPrice");
    const retained = finite(retainedRevenueCoefficient * price, "offered expected revenue");
    const fees = finite(feeCoefficient * price, "offered expected fees");
    const contribution = finite(contributionCoefficient * price - beforeOverhead, "offered contribution");
    const profit = finite(contribution - costs.overheadAllocation, "offered profit");
    const acquisitionBudget = finite(Math.min(
      contributionCoefficient * price - (beforeOverhead - costs.customerAcquisition) - margin * retained,
      contributionCoefficient * price - (afterOverhead - costs.customerAcquisition) - profitFloor,
    ), "acquisition budget");
    const tolerance = 1e-10 * Math.max(1, Math.abs(contribution), Math.abs(profit));
    result.offeredPrice = {
      listedOrderPrice: price,
      buyerCheckoutPrice: finite(grossFactor * price, "buyer checkout price"),
      exTaxOrderPrice: finite(exTaxFactor * price, "ex-tax order price"),
      expectedRetainedRevenue: retained,
      expectedPriceBasedFees: fees,
      expectedContribution: contribution,
      profitAfterOverhead: profit,
      contributionMargin: retained > 0 ? finite(contribution / retained, "offered contribution margin") : null,
      meetsTarget: (margin === 0 || retained > 0) && contribution + tolerance >= margin * retained && profit + tolerance >= profitFloor,
      customerAcquisitionCeiling: Math.max(0, acquisitionBudget),
      acquisitionBudgetBeforeClamping: acquisitionBudget,
    };
  }
  return result;
}

/** Comparables are already matched to the same product by the agent. The script
 * additionally enforces this explicit scope; a variant label is not proof of a
 * true match. Prices/shipping are pack totals. Delivered unit prices include
 * known destination sales tax plus charged shipping, then divide by pack size.
 * Unknown shipping/tax/pack quantities exclude the observation, never become 0.
 */
export interface ComparisonInput {
  settlementCurrency: string;
  scope: {
    market: string;
    channel: string;
    condition: string;
    variant: string;
    startDate: string;
    endDate: string;
  };
  comparables: Array<{
    id: string;
    market: string;
    channel: string;
    condition: string;
    variant: string;
    observedAt: string;
    price: Money;
    shipping: Money;
    unitsPerPack: number;
    tax: { salesTaxRate?: number; priceIncludesTax: boolean; shippingIncludesTax: boolean };
  }>;
}

export interface ComparisonResult {
  currency: string;
  metric: "taxInclusiveDeliveredUnitPrice";
  n: number;
  p25: number | null;
  median: number | null;
  p75: number | null;
  observations: Array<{ id: string; observedAt: string; deliveredUnitPrice: number }>;
  exclusions: Array<{ index: number; id: string | null; reason: string }>;
  warnings: string[];
}

function timestamp(value: unknown, path: string): number {
  const text = string(value, path);
  // A time zone is mandatory so host locale cannot alter the comparison window.
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(text)) {
    throw new TypeError(`${path} must be an ISO timestamp with an explicit time zone`);
  }
  const parsed = Date.parse(text);
  if (!Number.isFinite(parsed)) throw new TypeError(`${path} is not a valid timestamp`);
  // Date.parse normalizes e.g. February 30: validate the written calendar date.
  const year = Number(text.slice(0, 4));
  const month = Number(text.slice(5, 7));
  const day = Number(text.slice(8, 10));
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1] ?? 0;
  if (month < 1 || month > 12 || day < 1 || day > days || Number(text.slice(11, 13)) > 23) {
    throw new TypeError(`${path} has an invalid calendar date or hour`);
  }
  return parsed;
}

function quantile(values: number[], fraction: number): number | null {
  if (values.length === 0) return null;
  const position = (values.length - 1) * fraction;
  const lower = Math.floor(position);
  const low = values[lower]!;
  const high = values[Math.ceil(position)]!;
  return low + (high - low) * (position - lower);
}

export function comparePrices(input: unknown): ComparisonResult {
  const data = object(input, "input");
  keys(data, ["settlementCurrency", "scope", "comparables"], "input");
  const settlement = currency(data.settlementCurrency, "settlementCurrency");
  const scope = object(data.scope, "scope");
  keys(scope, ["market", "channel", "condition", "variant", "startDate", "endDate"], "scope");
  const scopeFields = ["market", "channel", "condition", "variant"] as const;
  for (const key of scopeFields) string(scope[key], `scope.${key}`);
  const start = timestamp(scope.startDate, "scope.startDate");
  const end = timestamp(scope.endDate, "scope.endDate");
  if (start > end) throw new RangeError("scope.startDate must not be later than scope.endDate");
  if (!Array.isArray(data.comparables)) throw new TypeError("comparables must be an array");
  const exclusions: ComparisonResult["exclusions"] = [];
  type Observation = ComparisonResult["observations"][number] & { index: number; time: number };
  const byId = new Map<string, Observation>();
  data.comparables.forEach((value: unknown, index: number) => {
    let id: string | null = null;
    try {
      const path = `comparables[${index}]`;
      const row = object(value, path);
      keys(row, ["id", ...scopeFields, "observedAt", "price", "shipping", "unitsPerPack", "tax"], path);
      id = string(row.id, `${path}.id`);
      for (const key of scopeFields) {
        if (string(row[key], `${path}.${key}`) !== scope[key]) throw new RangeError(`outside configured ${key}`);
      }
      const time = timestamp(row.observedAt, `${path}.observedAt`);
      if (time < start || time > end) throw new RangeError("outside configured observation window");
      const price = money(row.price, `${path}.price`, settlement);
      if (price <= 0) throw new RangeError("price must be positive for a paid-product comparable");
      const shipping = money(row.shipping, `${path}.shipping`, settlement);
      const units = number(row.unitsPerPack, `${path}.unitsPerPack`, 1);
      if (!Number.isSafeInteger(units)) throw new TypeError("unitsPerPack must be a positive safe integer");
      const tax = object(row.tax, `${path}.tax`);
      keys(tax, ["salesTaxRate", "priceIncludesTax", "shippingIncludesTax"], `${path}.tax`);
      const priceInclusive = boolean(tax.priceIncludesTax, `${path}.tax.priceIncludesTax`);
      const shippingInclusive = boolean(tax.shippingIncludesTax, `${path}.tax.shippingIncludesTax`);
      // Already-inclusive totals need no tax-rate assumption; zero is unused.
      const rate = tax.salesTaxRate === undefined && priceInclusive && shippingInclusive
        ? 0 : number(tax.salesTaxRate, `${path}.tax.salesTaxRate`);
      const deliveredUnitPrice = finite(
        (price * (priceInclusive ? 1 : 1 + rate) + shipping * (shippingInclusive ? 1 : 1 + rate)) / units,
        `${path}.deliveredUnitPrice`,
      );
      const observation: Observation = { id, observedAt: row.observedAt as string, deliveredUnitPrice, index, time };
      const previous = byId.get(id);
      if (!previous) byId.set(id, observation);
      else if (time > previous.time) {
        exclusions.push({ index: previous.index, id, reason: "duplicate id; newer valid observation retained" });
        byId.set(id, observation);
      } else exclusions.push({ index, id, reason: "duplicate id; newest valid observation retained (first on timestamp ties)" });
    } catch (error) {
      exclusions.push({ index, id, reason: error instanceof Error ? error.message : "invalid comparable" });
    }
  });
  const observations = [...byId.values()].sort((a, b) => a.index - b.index)
    .map(({ id, observedAt, deliveredUnitPrice }) => ({ id, observedAt, deliveredUnitPrice }));
  const prices = observations.map((row) => row.deliveredUnitPrice).sort((a, b) => a - b);
  const warnings = [
    "Asking/listed prices do not establish realized sale prices, demand, conversion, or likely sales volume.",
    "Agent must verify product identity, variant, condition, delivery/service level, and source timestamp before supplying comparables.",
    "Quantiles use linear interpolation between sorted observations; observations are not sales-weighted.",
  ];
  if (prices.length === 0) warnings.push("No eligible comparables; do not infer a market price from this result.");
  else if (prices.length < 5) warnings.push("Fewer than 5 eligible comparables: sparse evidence; treat the price range as provisional.");
  if (exclusions.length > 0) warnings.push(`${exclusions.length} observations excluded; inspect the recorded reasons.`);
  return {
    currency: settlement,
    metric: "taxInclusiveDeliveredUnitPrice",
    n: prices.length,
    p25: quantile(prices, 0.25),
    median: quantile(prices, 0.5),
    p75: quantile(prices, 0.75),
    observations,
    exclusions: exclusions.sort((a, b) => a.index - b.index),
    warnings,
  };
}
