import assert from 'node:assert/strict';
import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { main } from '../dist/cli.js';
import { atomicJson } from '../dist/media.js';
import { approvalHash, approvePlaybook, setPlaybook, setResearch } from '../dist/workflow.js';

let mediaTools = true;
try { execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' }); execFileSync('ffprobe', ['-version'], { stdio: 'ignore' }); } catch { mediaTools = false; }
const mediaTest = (name, fn) => test(name, { skip: !mediaTools && 'ffmpeg and ffprobe required for project checks' }, fn);

function configuredKey(t, value = 'offline-test-not-a-real-key') {
  const original = process.env.AISA_API_KEY;
  if (value === undefined) delete process.env.AISA_API_KEY;
  else process.env.AISA_API_KEY = value;
  t.after(() => { if (original === undefined) delete process.env.AISA_API_KEY; else process.env.AISA_API_KEY = original; });
}
function blockNetwork(t) {
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => { calls++; throw new Error('Network access forbidden in this test.'); });
  return () => calls;
}
async function fixture(t, { transport, preserve = true, kind = 'image' } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'studio-connection-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const source = join(root, 'source.png');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x512', '-frames:v', '1', '-threads', '1', '-y', source]);
  const placement = `shopify-${kind === 'image' ? 'gallery' : kind}`;
  const brief = {
    name: 'Connection fixture', goal: 'Verify routing without live calls.',
    targets: [{ platform: 'shopify', market: 'US', language: 'en-US', placements: [placement], themeDescription: 'Square gallery.' }],
    products: [{ sku: 'sku', name: 'Fixture', category: 'test', facts: [{ id: 'blue', text: 'Blue', source: { kind: 'visible-in-reference', referenceId: 'front' } }] }],
    references: [{ id: 'front', sku: 'sku', path: source, source: 'user-product-photo' }],
    budget: { currency: 'USD', maxEstimatedCostUsd: 1, maxAttemptsPerDeliverable: 2 },
  };
  const input = join(root, 'brief.json'); await atomicJson(input, brief);
  const directory = join(root, 'project');
  await main(['init', input, directory, ...(transport ? ['--transport', transport] : [])]);
  let state = JSON.parse(await readFile(join(directory, 'project.json'), 'utf8'));
  const now = new Date().toISOString();
  state = setResearch(state, {
    scope: 'Offline fixture; no live performance claims.',
    rules: [{ id: 'rule', platform: 'shopify', placement, requirement: 'Preserve the actual product.', status: 'mandatory', sourceUrl: 'https://help.shopify.com/en/manual/products/product-media', publisher: 'Shopify', fetchedAt: now, effectiveAt: null, conflict: null }],
    examples: [], exampleLimitations: [{ platform: 'shopify', reason: 'Offline fixture has no performance data.' }], synthesis: ['Keep identity.'], limitations: ['Offline only.'],
  });
  const cost = preserve ? 0 : 0.1;
  state = setPlaybook(state, {
    title: 'Connection fixture', version: '1', summary: 'Exercise local and explicit REST paths.', creativeDirection: 'Accurate product.',
    deliverables: [{ id: 'asset', sku: 'sku', platform: 'shopify', placement, kind, referenceIds: ['front'], claimIds: ['blue'], ruleIds: ['rule'], prompt: 'Keep the supplied product.', model: preserve ? 'local-photo-export' : 'fixture-model',
      ...(kind === 'image' ? { imageMode: preserve ? 'preserve' : 'edit', imageSize: '1K', size: '512x512' } : { size: '512x512', durationSeconds: 5, allowExperimentalVideo: true }),
      estimatedCostUsd: cost, ...(preserve ? {} : { pricingSource: 'Offline fixture only', pricingCheckedAt: now }),
      ...(!preserve && transport !== 'rest' && kind === 'image' ? { nativeRequest: {
        tool: 'fixture.createImage', argumentsTemplate: { body: { model: '', prompt: '', image: [''], size: '512x512' } },
        argumentsSchema: { type: 'object', required: ['body'], properties: { body: { type: 'object', required: ['model', 'prompt', 'image', 'size'], properties: { model: { type: 'string' }, prompt: { type: 'string' }, image: { type: 'array', items: { type: 'string' } }, size: { type: 'string' } } } } },
        responseSchema: { type: 'object', properties: { data: { type: 'array', items: { type: 'object', properties: { b64_json: { type: 'string' } } } } } },
        catalog: { source: 'Offline AIsa catalog fixture', checkedAt: now, modelIds: ['fixture-model'] },
        modelContract: { source: 'Offline model contract fixture', checkedAt: now, supportsReferences: true },
        modelPointer: '/body/model', promptPointer: '/body/prompt', referenceBindings: [{ referenceId: 'front', pointer: '/body/image/0', encoding: 'data-uri' }], result: { images: { pointer: '/data', base64Pointer: '/b64_json' } },
      } } : {}), successCriteria: ['Truthful depiction.'] }],
    budget: { estimatedTotalUsd: cost, maxAttemptsPerDeliverable: 2, costControl: 'estimate-only' }, approvalNotes: ['Offline fixture.'],
  });
  state = approvePlaybook(state, { actor: 'user', message: 'Approve this offline fixture.', playbookHash: approvalHash(state) });
  await atomicJson(join(directory, 'project.json'), state);
  return { root, directory, state };
}

test('model discovery defaults to host MCP even when an API key is configured', async t => {
  configuredKey(t); const calls = blockNetwork(t);
  const result = await main(['models']);
  assert.equal(result.transport, 'mcp');
  assert.match(result.instructions, /https:\/\/mcp\.aisa\.one\/mcp/);
  assert.equal(result.action, 'host-model-discovery-required');
  assert.equal(calls(), 0);
});

test('official CLI discovery never reads the REST environment key or makes REST calls', async t => {
  configuredKey(t, '\ninvalid REST credential'); const calls = blockNetwork(t);
  const result = await main(['models', '--transport', 'cli']);
  assert.equal(result.transport, 'cli');
  assert.match(result.instructions, /official AIsa CLI/);
  assert.equal(calls(), 0);
});

test('REST model discovery requires explicit selection and an environment key', async t => {
  configuredKey(t, ''); const calls = blockNetwork(t);
  await assert.rejects(main(['models', '--transport', 'rest']), /explicitly selected REST.*AISA_API_KEY/);
  assert.equal(calls(), 0);
});

test('explicit REST model discovery uses the REST client', async t => {
  configuredKey(t); let calls = 0;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls++;
    assert.equal(String(url), 'https://api.aisa.one/v1/models');
    assert.match(options.headers.Authorization, /^Bearer /);
    return new Response(JSON.stringify({ data: [] }), { headers: { 'Content-Type': 'application/json' } });
  });
  const result = await main(['models', '--transport', 'rest']);
  assert.equal(result.transport, 'rest'); assert.deepEqual(result.models, []); assert.equal(calls, 1);
});

test('invalid, duplicate and misplaced transport flags fail before doing work', async t => {
  const calls = blockNetwork(t);
  for (const args of [
    ['models', '--transport', 'auto'], ['models', '--transport'], ['models', '--transport=rest'],
    ['models', '--transport', 'mcp', '--transport', 'rest'], ['status', '/missing', '--transport', 'rest'],
    ['models', '--fallback', 'rest'], ['models', '--job', 'job'], ['build-native-request', '/missing', 'asset', '--job'],
    ['help', 'extra'], ['models', 'extra'],
  ]) await assert.rejects(main(args));
  assert.equal(calls(), 0);
});

mediaTest('new project persists MCP by default and local photo production needs no credential', async t => {
  configuredKey(t, '\ninvalid REST credential'); const calls = blockNetwork(t);
  const f = await fixture(t);
  assert.equal(f.state.transport, 'mcp');
  assert.equal((await main(['status', f.directory])).transport, 'mcp');
  const job = await main(['generate', f.directory, 'asset']);
  assert.equal(job.status, 'needs-review');
  assert.equal((await main(['resume', f.directory, 'asset'])).id, job.id);
  assert.equal(calls(), 0);
});

mediaTest('explicit REST is persisted without requiring credentials for offline setup', async t => {
  configuredKey(t, ''); const calls = blockNetwork(t);
  const f = await fixture(t, { transport: 'rest', preserve: false });
  assert.equal(f.state.transport, 'rest');
  await assert.rejects(main(['generate', f.directory, 'asset']), /explicitly selected REST.*AISA_API_KEY/);
  assert.equal(calls(), 0);
});

mediaTest('a configured environment key cannot switch an MCP project to REST', async t => {
  configuredKey(t); const calls = blockNetwork(t);
  const f = await fixture(t);
  await assert.rejects(main(['generate', f.directory, 'asset', '--transport', 'rest']), /Create a new project to change connections/);
  assert.equal((await main(['status', f.directory])).transport, 'mcp');
  assert.equal(calls(), 0);
});

mediaTest('MCP generation stops with connection instructions instead of using a configured REST key', async t => {
  configuredKey(t, '\ninvalid REST credential'); const calls = blockNetwork(t);
  const f = await fixture(t, { preserve: false });
  await assert.rejects(main(['generate', f.directory, 'asset']), /Connect AIsa.*https:\/\/mcp\.aisa\.one\/mcp/);
  assert.equal((await main(['status', f.directory])).ledger.jobs.length, 0);
  assert.equal(calls(), 0);
});

mediaTest('official CLI projects keep their native route when REST credentials exist', async t => {
  configuredKey(t, '\ninvalid REST credential'); const calls = blockNetwork(t);
  const f = await fixture(t, { transport: 'cli', preserve: false });
  assert.equal(f.state.transport, 'cli');
  await assert.rejects(main(['generate', f.directory, 'asset']), /authenticated official AIsa CLI/);
  await assert.rejects(main(['generate', f.directory, 'asset', '--transport', 'rest']), /Create a new project/);
  assert.equal(calls(), 0);
});

mediaTest('native CLI handoff completes a quoted MCP image import without executing REST', async t => {
  configuredKey(t, '\ninvalid REST credential'); const calls = blockNetwork(t);
  const f = await fixture(t, { preserve: false });
  const receiptPath = join(f.root, 'connection.json');
  await atomicJson(receiptPath, { transport: 'mcp', server: 'https://mcp.aisa.one/mcp', connected: true, checkedAt: new Date().toISOString(), receiptId: 'offline-account-check' });
  await main(['connection-import', f.directory, receiptPath]);
  const built = await main(['build-native-request', f.directory, 'asset']);
  const request = JSON.parse(await readFile(built.path, 'utf8'));
  assert.equal(request.arguments.body.model, 'fixture-model');
  assert.match(request.arguments.body.image[0], /^data:image\/png;base64,/);
  const preparationPath = join(f.root, 'preparation.json');
  await atomicJson(preparationPath, {
    deliverableId: 'asset', sessionId: 'offline-session', connectionReceiptId: 'offline-account-check',
    quote: { requestId: 'offline-quote', tool: built.tool, sessionId: 'offline-session', argumentsHash: built.argumentsHash, quotedAt: new Date().toISOString(), currency: 'USD', estimatedCostUsd: 0.1, estimateKind: 'exact', mayExceedEstimate: false, maxCostUsd: 0.1, source: { object: 'cost_estimate', currency: 'USD', estimated_cost_micros_usd: 100000, estimate_kind: 'exact', may_exceed_estimate: false, max_cost_micros_usd: 100000 } },
  });
  const prepared = await main(['prepare-native', f.directory, preparationPath]);
  assert.equal(prepared.job.transport, 'mcp');
  const dispatch = await main(['mark-native-dispatched', f.directory, prepared.operation.id]);
  assert.equal(dispatch.status, 'dispatched');
  const resultPath = join(f.root, 'result.json');
  await atomicJson(resultPath, { tool: built.tool, sessionId: 'offline-session', argumentsHash: built.argumentsHash, requestId: 'offline-generation', outcome: 'success', data: { data: [{ b64_json: (await readFile(f.state.references[0].path)).toString('base64') }] }, customerCostMicrosUsd: 0 });
  const job = await main(['ingest-native-result', f.directory, prepared.operation.id, resultPath]);
  assert.equal(job.status, 'needs-review');
  assert.equal((await main(['resume', f.directory, 'asset'])).id, job.id);
  assert.equal((await main(['resume-native', f.directory, 'asset'])).id, job.id);
  assert.equal(calls(), 0);
});

mediaTest('legacy projects keep their approval hash and require explicit REST only for network execution', async t => {
  configuredKey(t); const calls = blockNetwork(t);
  const f = await fixture(t, { transport: 'rest', preserve: false });
  delete f.state.transport;
  f.state.approval.playbookHash = approvalHash(f.state);
  await atomicJson(join(f.directory, 'project.json'), f.state);
  const before = await readFile(join(f.directory, 'project.json'), 'utf8');
  const status = await main(['status', f.directory]);
  assert.equal(status.transport, 'legacy-rest'); assert.equal(status.approvalCurrent, true);
  await main(['report', f.directory]);
  const reported = JSON.parse(await readFile(join(f.directory, 'project.json'), 'utf8'));
  assert.equal(reported.transport, undefined); assert.equal(reported.approval.playbookHash, f.state.approval.playbookHash);
  await assert.rejects(main(['generate', f.directory, 'asset']), /Explicitly select --transport rest/);
  assert.equal(calls(), 0);
  await assert.rejects(main(['generate', f.directory, 'asset', '--transport', 'rest']), /AIsa request failed before a usable response/);
  assert.equal(calls(), 1);
  assert.equal(JSON.parse(before).approval.playbookHash, reported.approval.playbookHash);
});

mediaTest('legacy read-only review and export remain available without a credential', async t => {
  configuredKey(t, ''); const calls = blockNetwork(t);
  const f = await fixture(t, { transport: 'rest' });
  delete f.state.transport;
  f.state.approval.playbookHash = approvalHash(f.state);
  await atomicJson(join(f.directory, 'project.json'), f.state);
  const job = await main(['generate', f.directory, 'asset']);
  const reviewPath = join(f.root, 'review.json');
  await atomicJson(reviewPath, { deliverableId: 'asset', inspectedBy: 'agent', artifacts: job.artifacts.map(artifact => ({ sha256: artifact.sha256, productFidelity: 'pass', platformCompliance: 'pass', copyAccuracy: 'pass', visualQuality: 'pass', notes: 'Offline fixture inspected for matching dimensions and product pixels.' })) });
  await main(['review', f.directory, reviewPath]);
  const exported = await main(['export', f.directory, join(f.root, 'export')]);
  assert.equal(exported.files, 4);
  const manifest = JSON.parse(await readFile(join(exported.destination, 'manifest.json'), 'utf8'));
  assert.equal(manifest.approval.playbookHash, f.state.approval.playbookHash);
  assert.equal(calls(), 0);
});

mediaTest('legacy video resume cannot poll through REST until it is explicitly selected', async t => {
  configuredKey(t); const calls = blockNetwork(t);
  const f = await fixture(t, { transport: 'rest', preserve: false, kind: 'video' });
  delete f.state.transport;
  f.state.approval.playbookHash = approvalHash(f.state);
  await atomicJson(join(f.directory, 'project.json'), f.state);
  await atomicJson(join(f.directory, 'execution.json'), { schemaVersion: 1, jobs: [{ id: 'pending-job', deliverableId: 'asset', approvalHash: f.state.approval.playbookHash, model: 'fixture-model', status: 'submitted', taskId: 'known-task', estimatedCostUsd: 0.1, createdAt: new Date().toISOString(), artifacts: [] }] });
  await assert.rejects(main(['resume', f.directory, 'asset']), /Explicitly select --transport rest/);
  assert.equal(calls(), 0);
  assert.equal((await main(['status', f.directory])).ledger.jobs[0].taskId, 'known-task');
});
