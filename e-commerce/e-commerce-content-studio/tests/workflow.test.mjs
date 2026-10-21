import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import {
  approvalHash, approvePlaybook, assertReady, initProject, renderPlaybook, renderResearch,
  setPlaybook, setResearch, validateBrief, validateProject,
} from '../dist/workflow.js';

const NOW = '2026-10-18T12:00:00.000Z';
function fixture() {
  const brief = {
    name: 'Bottle launch', goal: 'Accurate product content for a US store.',
    targets: [{ platform: 'shopify', market: 'US', language: 'en-US', placements: ['shopify-gallery'], themeDescription: 'Test theme with square product gallery.' }],
    products: [{ sku: 'BOTTLE-BLUE', name: 'Blue bottle', category: 'Drinkware', facts: [{ id: 'blue', text: 'Blue exterior.', source: { kind: 'visible-in-reference', referenceId: 'front' } }] }],
    references: [{ id: 'front', sku: 'BOTTLE-BLUE', path: '/fixture/product.png', source: 'user-product-photo' }],
    budget: { currency: 'USD', maxEstimatedCostUsd: 2, maxAttemptsPerDeliverable: 2 },
  };
  const references = [{ ...brief.references[0], sha256: 'a'.repeat(64), mimeType: 'image/png', width: 1024, height: 1024 }];
  const research = {
    scope: 'Test fixture; not live research.',
    rules: [{ id: 'format', platform: 'shopify', placement: 'shopify-gallery', requirement: 'Use supported product images.', status: 'mandatory', sourceUrl: 'https://help.shopify.com/en/manual/products/product-media', publisher: 'Shopify', fetchedAt: '2026-10-18', effectiveAt: null, conflict: null }],
    examples: [{ id: 'example', platform: 'shopify', placement: 'shopify-gallery', url: 'https://example.com/product', observedAt: '2026-10-18', metricTier: 'proxy', metrics: [{ name: 'conversion', value: null, window: null }], takeaways: ['The product is framed clearly.'] }],
    synthesis: ['Keep the product readable.'], limitations: ['Conversion is unknown; this example cannot establish causality.'],
  };
  const playbook = {
    title: 'Bottle creative plan', version: 'draft-1', summary: 'One faithful product image.', creativeDirection: 'Show the product clearly.',
    deliverables: [{ id: 'hero', sku: 'BOTTLE-BLUE', platform: 'shopify', placement: 'shopify-gallery', kind: 'image', referenceIds: ['front'], claimIds: ['blue'], ruleIds: ['format'], prompt: 'Preserve product appearance.', model: 'local-photo-export', imageMode: 'preserve', size: '1024x1024', estimatedCostUsd: 0, successCriteria: ['The correct blue bottle remains visible.'] }],
    budget: { estimatedTotalUsd: 0, maxAttemptsPerDeliverable: 1, costControl: 'estimate-only' },
    approvalNotes: ['Review the framing and actual photo.'],
  };
  return { brief, references, research, playbook };
}
function prepared() {
  const { brief, references, research, playbook } = fixture();
  return setPlaybook(setResearch(initProject(brief, references, NOW), research, NOW), playbook, NOW);
}
function approved() {
  const state = prepared();
  return approvePlaybook(state, { actor: 'user', message: 'I approve this exact playbook.', playbookHash: approvalHash(state) }, NOW);
}

test('product photographs are a hard gate for every SKU', () => {
  const { brief, references } = fixture();
  assert.throws(() => initProject({ ...brief, references: [] }, [], NOW), /product photos are required/);
  assert.throws(() => initProject(brief, [], NOW), /validated user product photos/);
  brief.products.push({ sku: 'BOTTLE-RED', name: 'Red bottle', category: 'Drinkware', facts: [] });
  assert.throws(() => initProject(brief, references, NOW), /BOTTLE-RED requires at least one/);
});

test('a claimed reference must match inspected metadata and cannot cite another SKU', () => {
  const { brief, references } = fixture();
  assert.throws(() => initProject(brief, [{ ...references[0], sha256: '' }], NOW), /SHA-256/);
  assert.throws(() => initProject(brief, [{ ...references[0], path: '/different.png' }], NOW), /match the brief reference exactly/);
  brief.products[0].facts[0].source.referenceId = 'unknown';
  assert.throws(() => initProject(brief, references, NOW), /cite a reference for its own SKU/);
});

test('platform and placement support is explicit, including market restrictions', () => {
  const { brief } = fixture();
  assert.throws(() => validateBrief({ ...brief, targets: [{ ...brief.targets[0], platform: 'etsy' }] }), /must be one of/);
  assert.throws(() => validateBrief({ ...brief, targets: [{ platform: 'amazon-us', market: 'GB', language: 'en-GB', placements: ['amazon-main'] }] }), /US market only/);
  assert.throws(() => validateBrief({ ...brief, targets: [{ ...brief.targets[0], placements: ['tiktok-gallery'] }] }), /does not belong/);
  assert.throws(() => validateBrief({ ...brief, targets: [{ ...brief.targets[0], market: '' }] }), /target.market/);
});

test('optional remote video reference must remain bound to the same inspected input', () => {
  const { brief, references } = fixture();
  brief.references[0].remoteUrl = 'http://example.com/product.png';
  assert.throws(() => initProject(brief, references, NOW), /must use HTTPS/);
  brief.references[0].remoteUrl = 'https://example.com/product.png';
  assert.throws(() => initProject(brief, references, NOW), /match the brief reference exactly/);
  references[0].remoteUrl = brief.references[0].remoteUrl;
  assert.equal(initProject(brief, references, NOW).references[0].remoteUrl, references[0].remoteUrl);
});

test('research requires each selected placement and explicit performance uncertainty', () => {
  const { brief, references, research } = fixture();
  const state = initProject(brief, references, NOW);
  assert.throws(() => setResearch(state, { ...research, rules: [{ ...research.rules[0], status: 'recommended' }] }, NOW), /mandatory requirements/);
  research.examples[0].metricTier = 'measured';
  assert.throws(() => setResearch(state, research, NOW), /actual metric value and measurement window/);
  research.examples = [];
  assert.throws(() => setResearch(state, research, NOW), /explicit exampleLimitations/);
  research.exampleLimitations = [{ platform: 'shopify', reason: 'The selected store pages could not be accessed; no performance inference is possible.' }];
  assert.equal(setResearch(state, research, NOW).research.examples.length, 0);
});

test('a report can record conflicts but a playbook cannot pass them', () => {
  const { brief, references, research, playbook } = fixture();
  research.rules[0].conflict = 'Two official sources disagree about size.';
  const state = setResearch(initProject(brief, references, NOW), research, NOW);
  assert.ok(renderResearch(state).includes('Two official sources disagree about size.'));
  assert.throws(() => setPlaybook(state, playbook, NOW), /Resolve research conflict/);
});

test('research and price evidence must be fresh at approval and generation', () => {
  const state = approved();
  assert.throws(() => assertReady(state, '2026-10-26T12:00:00.000Z'), /older than 7 days/);
  const plan = structuredClone(state.playbook);
  Object.assign(plan.deliverables[0], { model: 'test-image-edit', imageMode: 'edit', imageSize: '1K', estimatedCostUsd: 0.1, pricingSource: 'https://aisa.one/models/test', pricingCheckedAt: '2026-10-01' });
  plan.budget.estimatedTotalUsd = 0.1;
  const changed = setPlaybook(state, plan, NOW);
  assert.throws(() => approvePlaybook(changed, { actor: 'user', message: 'Approved.', playbookHash: approvalHash(changed) }, NOW), /Pricing evidence/);
});

test('approval binds the full brief, product photo hashes, research, and output specs', () => {
  const state = approved();
  assert.equal(assertReady(state, NOW).deliverables[0].id, 'hero');
  for (const mutate of [
    value => { value.brief.goal = 'A changed campaign'; },
    value => { value.references[0].sha256 = 'b'.repeat(64); },
    value => { value.research.examples[0].takeaways = ['Different direction']; },
    value => { value.playbook.deliverables[0].size = '1600x1600'; },
  ]) {
    const changed = structuredClone(state); mutate(changed);
    assert.throws(() => assertReady(changed, NOW), /changed.*approve/);
  }
  assert.equal(approvalHash({ ...state, updatedAt: '2026-10-19' }), approvalHash(state));
});

test('approval requires user evidence and the exact presented hash', () => {
  const state = prepared();
  assert.throws(() => assertReady(state, NOW), /explicit user approval/);
  assert.throws(() => approvePlaybook(state, { actor: 'assistant', message: 'Approved automatically.', playbookHash: approvalHash(state) }, NOW), /approval.actor/);
  assert.throws(() => approvePlaybook(state, { actor: 'user', message: '', playbookHash: approvalHash(state) }, NOW), /approval.message/);
  assert.throws(() => approvePlaybook(state, { actor: 'user', message: 'true', playbookHash: approvalHash(state) }, NOW), /boolean string/);
  assert.throws(() => approvePlaybook(state, { actor: 'user', message: 'Approved.', playbookHash: 'a'.repeat(64) }, NOW), /does not match/);
});

test('research and playbook updates revoke previous approvals immutably', () => {
  const state = approved();
  const next = setResearch(state, state.research, NOW);
  assert.equal(next.approval, undefined); assert.equal(next.playbook, undefined);
  assert.ok(state.approval);
  assert.equal(setPlaybook(state, state.playbook, NOW).approval, undefined);
});

test('deliverables require supported facts, correct reference SKUs, and mandatory rules', () => {
  const state = prepared();
  for (const [patch, expected] of [
    [{ claimIds: ['unverified-health-claim'] }, /unsupported product claim/],
    [{ referenceIds: ['competitor-photo'] }, /photos of its own SKU/],
    [{ ruleIds: ['different-platform-rule'] }, /another placement or an unknown rule/],
    [{ id: '../../escape' }, /safe file identifiers/],
    [{ kind: 'video' }, /kind does not match/],
  ]) {
    const plan = structuredClone(state.playbook); Object.assign(plan.deliverables[0], patch);
    assert.throws(() => setPlaybook(state, plan, NOW), expected);
  }
});

test('Amazon main requires actual-photo preserve mode', () => {
  const { brief, references, research, playbook } = fixture();
  brief.targets[0] = { platform: 'amazon-us', market: 'US', language: 'en-US', placements: ['amazon-main'] };
  for (const item of [research.rules[0], research.examples[0], playbook.deliverables[0]]) { item.platform = 'amazon-us'; item.placement = 'amazon-main'; }
  const state = setResearch(initProject(brief, references, NOW), research, NOW);
  Object.assign(playbook.deliverables[0], { imageMode: 'edit', model: 'test-model' });
  assert.throws(() => setPlaybook(state, playbook, NOW), /Amazon main images require preserve mode/);
});

test('output constraints and retry estimates are checked before approval', () => {
  const state = prepared();
  let plan = structuredClone(state.playbook);
  plan.deliverables[0].constraints = { minWidth: 1600 };
  assert.throws(() => setPlaybook(state, plan, NOW), /below the researched minimum/);
  plan.deliverables[0].constraints = { aspectRatio: '16:9' };
  assert.throws(() => setPlaybook(state, plan, NOW), /do not match/);
  plan = structuredClone(state.playbook);
  Object.assign(plan.deliverables[0], { model: 'test-image-edit', imageMode: 'edit', imageSize: '1K', estimatedCostUsd: 1.1, pricingSource: 'https://aisa.one/models/test', pricingCheckedAt: '2026-10-18' });
  plan.budget.estimatedTotalUsd = 1.1; plan.budget.maxAttemptsPerDeliverable = 2;
  assert.throws(() => setPlaybook(state, plan, NOW), /including all allowed attempts exceeds/);
});

test('reports preserve source links, evidence uncertainty, constraints and approval scope', () => {
  const state = prepared();
  const researchReport = renderResearch(state);
  assert.ok(researchReport.includes('https://example.com/product'));
  assert.ok(researchReport.includes('conversion: unknown; measurement window: unknown'));
  assert.ok(researchReport.includes('does not establish'));
  const playbookReport = renderPlaybook(state);
  assert.ok(playbookReport.includes(approvalHash(state)));
  assert.ok(playbookReport.includes('not an enforced provider billing cap'));
  assert.deepEqual(validateProject(JSON.parse(JSON.stringify(state))), state);
});

test('packaged examples are visibly blocked templates, not ready production authority', async () => {
  const load = async name => JSON.parse(await readFile(new URL(`../assets/${name}.example.json`, import.meta.url), 'utf8'));
  const brief = await load('brief'); const research = await load('research'); const playbook = await load('playbook');
  const references = brief.references.map(ref => ({ ...ref, sha256: 'a'.repeat(64), mimeType: 'image/jpeg', width: 1600, height: 1600 }));
  const state = setResearch(initProject(brief, references, NOW), research, NOW);
  assert.throws(() => setPlaybook(state, playbook, NOW), /Resolve research conflict|older than 7 days/);
});
