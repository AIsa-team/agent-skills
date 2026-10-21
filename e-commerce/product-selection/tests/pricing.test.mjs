import assert from 'node:assert/strict';
import test from 'node:test';
import { calculatePricing, comparePrices } from '../dist/pricing.js';

const usd = (amount) => ({ amount, currency: 'USD' });
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);

function fixture() {
  return {
    settlementCurrency: 'USD',
    tax: { salesTaxRate: 0.2, priceIncludesTax: true },
    costs: {
      product: usd(10), inboundFreight: usd(0), packaging: usd(0), customsDuty: usd(0),
      fulfillment: usd(0), outboundShipping: usd(0), customerAcquisition: usd(2),
      fixedOrderFees: usd(0), otherPerOrder: usd(0), overheadAllocation: usd(3),
    },
    importVat: { amount: usd(0), recoverableRate: 0 },
    returns: { rate: 0, incrementalCost: usd(0), productRecovery: usd(0) },
    fees: [{ name: 'marketplace', rate: 0.1, basis: 'grossPrice', refundOnReturnRate: 0 }],
    target: { contributionMargin: 0.2, profitPerOrder: usd(2) },
    offeredPrice: 30,
  };
}

test('tax-inclusive threshold excludes sales tax and distinguishes contribution from allocated profit', () => {
  const result = calculatePricing(fixture());
  close(result.contributionBreakEvenPrice, 12 / (5 / 6 - 0.1));
  close(result.breakEvenPrice, 15 / (5 / 6 - 0.1));
  close(result.targetPrices.forContributionMargin, 12 / (5 / 6 - 0.1 - 0.2 * 5 / 6));
  close(result.targetPrice, 17 / (5 / 6 - 0.1));
  close(result.offeredPrice.expectedRetainedRevenue, 25);
  close(result.offeredPrice.expectedContribution, 10);
  close(result.offeredPrice.profitAfterOverhead, 7);
  close(result.offeredPrice.contributionMargin, 0.4);
  close(result.offeredPrice.customerAcquisitionCeiling, 7);
  assert.equal(result.offeredPrice.meetsTarget, true);
});

test('computed target price satisfies both margin before overhead and profit floor after overhead', () => {
  const data = fixture();
  const first = calculatePricing(data);
  data.offeredPrice = first.targetPrice;
  const result = calculatePricing(data);
  assert.equal(result.offeredPrice.meetsTarget, true);
  close(result.offeredPrice.profitAfterOverhead, 2);
  assert.ok(result.offeredPrice.contributionMargin >= 0.2);
});

test('tax-exclusive quote has a distinct buyer checkout price and fees on that gross amount', () => {
  const data = fixture();
  data.tax.priceIncludesTax = false;
  const result = calculatePricing(data);
  assert.equal(result.priceBasis, 'taxExclusiveOrderTotal');
  close(result.offeredPrice.buyerCheckoutPrice, 36);
  close(result.offeredPrice.exTaxOrderPrice, 30);
  close(result.offeredPrice.expectedPriceBasedFees, 3.6);
  data.fees[0].basis = 'exTaxPrice';
  close(calculatePricing(data).offeredPrice.expectedPriceBasedFees, 3);
});

test('FX is destination units per origin unit and must be explicit across currencies', () => {
  const data = fixture();
  data.costs.product = { amount: 70, currency: 'CNY', fxToSettlement: 1 / 7 };
  close(calculatePricing(data).economics.costPerPlacedOrderBeforeOverhead, 12);
  delete data.costs.product.fxToSettlement;
  assert.throws(() => calculatePricing(data), /fxToSettlement/);
  data.costs.product = { amount: 10, currency: 'USD', fxToSettlement: 7 };
  assert.throws(() => calculatePricing(data), /fxToSettlement/);
});

test('only unrecoverable import VAT increases order costs; supplied customs duty is separate', () => {
  const data = fixture();
  data.importVat = { amount: usd(4), recoverableRate: 0.75 };
  data.costs.customsDuty = usd(2);
  const result = calculatePricing(data);
  close(result.economics.importVatPaid, 4);
  close(result.economics.recoverableImportVatCash, 3);
  close(result.economics.unrecoverableImportVat, 1);
  close(result.economics.costPerPlacedOrderBeforeOverhead, 15);
  data.importVat.recoverableRate = 1;
  close(calculatePricing(data).economics.costPerPlacedOrderBeforeOverhead, 14);
});

test('full refunds reduce retained revenue while nonrefunded fees and incurred costs remain', () => {
  const data = fixture();
  data.returns = { rate: 0.2, incrementalCost: usd(2), productRecovery: usd(8) };
  const result = calculatePricing(data);
  close(result.economics.retainedRevenueCoefficient, 0.8 / 1.2);
  close(result.economics.returnCostAdjustment, -1.2);
  close(result.economics.costPerPlacedOrderBeforeOverhead, 10.8);
  close(result.offeredPrice.expectedPriceBasedFees, 3);
  close(result.offeredPrice.expectedContribution, 20 - 3 - 10.8);
  data.fees[0].refundOnReturnRate = 1;
  close(calculatePricing(data).offeredPrice.expectedPriceBasedFees, 2.4);
});

test('return recovery cannot recover costs that were never incurred', () => {
  const data = fixture();
  data.returns.productRecovery = usd(10.01);
  assert.throws(() => calculatePricing(data), /cannot exceed incurred product cost/);
});

test('unknown costs and invalid rates do not silently become zero', () => {
  for (const mutate of [
    (data) => { delete data.costs.outboundShipping; },
    (data) => { data.costs.product = null; },
    (data) => { data.importVat.amount.amount = null; },
    (data) => { data.fees[0].refundOnReturnRate = undefined; },
    (data) => { data.tax.salesTaxRate = -0.1; },
    (data) => { data.returns.rate = 1.01; },
    (data) => { data.target.contributionMargin = Number.NaN; },
    (data) => { data.offeredPrice = Infinity; },
    (data) => { data.costs.product.amount = '10'; },
    (data) => { data.costs.outboundShiping = usd(2); },
  ]) {
    const data = fixture();
    mutate(data);
    assert.throws(() => calculatePricing(data));
  }
  assert.throws(() => calculatePricing(null), /must be an object/);
});

test('impossible margin, complete returns, and fees consuming revenue fail with an explanation', () => {
  const data = fixture();
  data.target.contributionMargin = 0.95;
  assert.throws(() => calculatePricing(data), /nonpositive pricing denominator/);
  data.target.contributionMargin = 0.2;
  data.returns.rate = 1;
  assert.throws(() => calculatePricing(data), /No finite break-even price/);
  data.returns.rate = 0;
  data.fees[0].rate = 0.9;
  assert.throws(() => calculatePricing(data), /No finite break-even price/);
});

test('unviable offered price reports CAC shortfall and zero retained revenue has no margin', () => {
  const data = fixture();
  data.offeredPrice = 1;
  const result = calculatePricing(data);
  assert.equal(result.offeredPrice.customerAcquisitionCeiling, 0);
  assert.ok(result.offeredPrice.acquisitionBudgetBeforeClamping < 0);
  assert.equal(result.offeredPrice.meetsTarget, false);
  data.offeredPrice = 0;
  assert.equal(calculatePricing(data).offeredPrice.contributionMargin, null);
});

test('zero revenue cannot satisfy a positive contribution margin even with zero costs', () => {
  const data = fixture();
  for (const cost of Object.values(data.costs)) cost.amount = 0;
  data.fees = [];
  data.target.profitPerOrder.amount = 0;
  data.offeredPrice = 0;
  const result = calculatePricing(data);
  assert.equal(result.offeredPrice.contributionMargin, null);
  assert.equal(result.offeredPrice.meetsTarget, false);
  assert.ok(result.warnings.some(value => value.includes('infimum')));
  data.offeredPrice = 1;
  assert.equal(calculatePricing(data).offeredPrice.meetsTarget, true);
});

test('zero variable costs permit the maximum margin at positive revenue, with overhead and profit targets still enforced', () => {
  const data = fixture();
  for (const cost of Object.values(data.costs)) cost.amount = 0;
  data.costs.overheadAllocation.amount = 3;
  data.tax = { salesTaxRate: 0, priceIncludesTax: false };
  data.fees = [];
  data.target = { contributionMargin: 1, profitPerOrder: usd(2) };
  data.offeredPrice = 5;
  const result = calculatePricing(data);
  assert.equal(result.targetPrices.forContributionMargin, 0);
  assert.equal(result.targetPrice, 5);
  assert.equal(result.offeredPrice.contributionMargin, 1);
  assert.equal(result.offeredPrice.profitAfterOverhead, 2);
  assert.equal(result.offeredPrice.meetsTarget, true);
  assert.ok(result.warnings.some(value => value.includes('contribution-margin price floor is an infimum')));

  data.costs.overheadAllocation.amount = 0;
  data.target.profitPerOrder.amount = 0;
  data.offeredPrice = 0;
  const zero = calculatePricing(data);
  assert.equal(zero.targetPrice, 0);
  assert.equal(zero.offeredPrice.contributionMargin, null);
  assert.equal(zero.offeredPrice.meetsTarget, false);
  assert.ok(zero.warnings.some(value => value.includes('infimum')));

  data.costs.product.amount = 1;
  assert.throws(() => calculatePricing(data), /nonpositive pricing denominator/);
  data.costs.product.amount = 0;
  data.fees = [{ name: 'marketplace', rate: 0.1, basis: 'exTaxPrice', refundOnReturnRate: 0 }];
  assert.throws(() => calculatePricing(data), /nonpositive pricing denominator/);
});

test('conversion overflow and duplicate fee labels are rejected', () => {
  const data = fixture();
  data.costs.product = { amount: Number.MAX_VALUE, currency: 'CNY', fxToSettlement: 2 };
  assert.throws(() => calculatePricing(data), /finite arithmetic/);
  data.costs.product = usd(10);
  data.fees.push({ ...data.fees[0] });
  assert.throws(() => calculatePricing(data), /duplicates/);
});

function comparison() {
  return {
    settlementCurrency: 'USD',
    scope: {
      market: 'US', channel: 'Amazon', condition: 'new', variant: 'red-100ml',
      startDate: '2026-10-01T00:00:00Z', endDate: '2026-10-12T23:59:59Z',
    },
    comparables: [],
  };
}

function row(id, price, extra = {}) {
  return {
    id, market: 'US', channel: 'Amazon', condition: 'new', variant: 'red-100ml',
    observedAt: '2026-10-10T12:00:00Z', price: usd(price), shipping: usd(0), unitsPerPack: 1,
    tax: { salesTaxRate: 0, priceIncludesTax: true, shippingIncludesTax: true },
    ...extra,
  };
}

test('comparables normalize pack quantities, shipping, sales tax, and FX to delivered unit prices', () => {
  const data = comparison();
  data.comparables = [row('a', 1, {
    price: { amount: 140, currency: 'CNY', fxToSettlement: 1 / 7 },
    shipping: usd(4), unitsPerPack: 2,
    tax: { salesTaxRate: 0.2, priceIncludesTax: false, shippingIncludesTax: false },
  })];
  const result = comparePrices(data);
  close(result.median, 14.4);
  assert.equal(result.n, 1);
  assert.ok(result.warnings.some((value) => value.includes('Fewer than 5')));
});

test('already tax-inclusive comparables need no invented tax rate, while ex-tax values require one', () => {
  const data = comparison();
  data.comparables = [row('inclusive', 20, {tax:{priceIncludesTax:true,shippingIncludesTax:true}}),
    row('exclusive', 25, {tax:{priceIncludesTax:false,shippingIncludesTax:true}})];
  const result = comparePrices(data);
  assert.equal(result.n, 1);
  close(result.median, 20);
  assert.match(result.exclusions[0].reason, /salesTaxRate/);
});

test('quantiles interpolate sorted prices and keep newest valid observation per id', () => {
  const data = comparison();
  data.comparables = [row('a', 100), row('b', 20), row('c', 30), row('d', 40),
    row('a', 10, { observedAt: '2026-10-11T12:00:00Z' })];
  const result = comparePrices(data);
  assert.equal(result.n, 4);
  close(result.p25, 17.5);
  close(result.median, 25);
  close(result.p75, 32.5);
  assert.equal(result.exclusions.length, 1);
  assert.equal(result.exclusions[0].index, 0);
});

test('missing price/shipping and out-of-scope observations are excluded with reasons', () => {
  const data = comparison();
  data.comparables = [
    row('good', 10), row('missing-price', 20, { price: null }),
    row('unknown-shipping', 20, { shipping: undefined }), row('market', 20, { market: 'GB' }),
    row('old', 20, { observedAt: '2026-09-30T12:00:00Z' }), row('pack', 20, { unitsPerPack: 0 }),
    row('condition', 20, { condition: 'used' }), row('variant', 20, { variant: 'blue-50ml' }),
    row('free', 0), row('invalid-date', 20, { observedAt: '2026-02-30T12:00:00Z' }),
  ];
  const result = comparePrices(data);
  assert.equal(result.n, 1);
  assert.equal(result.exclusions.length, 9);
  assert.equal(result.median, 10);
  assert.ok(result.exclusions.some((value) => value.reason.includes('shipping')));
});

test('zero eligible comparables returns null quantiles instead of a manufactured market price', () => {
  const result = comparePrices(comparison());
  assert.equal(result.n, 0);
  assert.equal(result.p25, null);
  assert.equal(result.median, null);
  assert.equal(result.p75, null);
  assert.ok(result.warnings.some((value) => value.includes('No eligible comparables')));
});

test('comparison window requires valid absolute ISO timestamps', () => {
  const data = comparison();
  data.scope.startDate = '2026-10-01';
  assert.throws(() => comparePrices(data), /ISO timestamp/);
  data.scope.startDate = '2026-10-13T00:00:00Z';
  assert.throws(() => comparePrices(data), /must not be later/);
});
