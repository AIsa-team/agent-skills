import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';
import { initProject, setResearch, setPlaybook, approvalHash, approvePlaybook, validateProject } from '../dist/workflow.js';
import { atomicJson, inspectMedia } from '../dist/media.js';
import { generate, loadLedger, productionPrompt, review, exportPackage } from '../dist/production.js';
import { digestJson, assertSchema } from '../dist/native-contract.js';
import { importConnection, buildNativeRequest, prepareNative, markNativeDispatched, ingestNativeResult, prepareNativePoll, resumeNative, importHostCopy, cancelNativePrepared } from '../dist/native.js';

const now = () => new Date().toISOString();
const schemas = {
  imageInput: { type: 'object', additionalProperties: false, required: ['body'], properties: { body: { type: 'object', additionalProperties: false, required: ['model', 'prompt', 'image', 'size', 'quality'], properties: { model: { type: 'string' }, prompt: { type: 'string' }, image: { type: 'array', minItems: 1, items: { type: 'string' } }, size: { type: 'string' }, quality: { enum: ['high'] } } } } },
  imageOutput: { type: 'object', required: ['data'], properties: { data: { type: 'array', minItems: 1, items: { type: 'object', properties: { b64_json: { type: 'string' }, url: { type: 'string' } }, anyOf: [{ required: ['b64_json'] }, { required: ['url'] }] } } } },
  videoInput: { type: 'object', required: ['body'], properties: { body: { type: 'object', required: ['model', 'prompt', 'reference', 'duration'], properties: { model: { type: 'string' }, prompt: { type: 'string' }, reference: { type: 'string' }, duration: { const: 5 } }, additionalProperties: false } }, additionalProperties: false },
  videoOutput: { type: 'object', required: ['id', 'status'], properties: { id: { type: 'string' }, status: { enum: ['queued', 'completed', 'failed', 'unknown'] }, result: { type: 'object', properties: { video_url: { type: 'string' } } } } },
};
const taskMapping = { task: { idPointer: '/id', statusPointer: '/status', pending: ['queued', 'unknown'], succeeded: ['completed'], failed: ['failed'], urlsPointer: '/result/video_url' } };
function plan(kind, model) {
  const base = {
    tool: kind === 'video' ? 'createVideoGeneration' : 'createImageGeneration',
    catalog: { source: 'offline fixture listModels receipt', checkedAt: now(), modelIds: [model] },
    modelContract: { source: 'offline fixture model reference-input contract', checkedAt: now(), supportsReferences: true },
    modelPointer: '/body/model', promptPointer: '/body/prompt',
    argumentsTemplate: { body: { model: '', prompt: '', image: [''], size: '512x512', quality: 'high' } },
    argumentsSchema: schemas.imageInput, responseSchema: schemas.imageOutput,
    referenceBindings: [{ referenceId: 'front', pointer: '/body/image/0', encoding: 'data-uri' }],
    result: { images: { pointer: '/data', base64Pointer: '/b64_json', urlPointer: '/url' } },
  };
  if (kind === 'video') Object.assign(base, {
    argumentsTemplate: { body: { model: '', prompt: '', reference: '', duration: 5 } },
    argumentsSchema: schemas.videoInput, responseSchema: schemas.videoOutput,
    referenceBindings: [{ referenceId: 'front', pointer: '/body/reference', encoding: 'data-uri' }], result: taskMapping,
    poll: { tool: 'retrieveVideoGeneration', argumentsTemplate: { task_id: '' }, argumentsSchema: { type: 'object', required: ['task_id'], properties: { task_id: { type: 'string' } }, additionalProperties: false }, taskIdPointer: '/task_id', responseSchema: schemas.videoOutput, result: taskMapping },
  });
  if (kind === 'copy') Object.assign(base, {
    tool: 'createChatCompletion', argumentsTemplate: { body: { model: '', prompt: '' } },
    argumentsSchema: { type: 'object', required: ['body'], properties: { body: { type: 'object', required: ['model', 'prompt'], properties: { model: { type: 'string' }, prompt: { type: 'string' } }, additionalProperties: false } }, additionalProperties: false },
    responseSchema: { type: 'object', required: ['text'], properties: { text: { type: 'string' } } }, referenceBindings: [], result: { textPointer: '/text' },
  });
  return base;
}
async function fixture(t, kind = 'image', transport = 'mcp', model = 'future-reference-model') {
  const root = await mkdtemp(join(tmpdir(), 'studio-native-')); t.after(() => rm(root, { recursive: true, force: true }));
  const photo = join(root, 'product.png');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x512', '-frames:v', '1', '-threads', '1', '-y', photo]);
  const info = await inspectMedia(photo, 'image');
  const brief = { name: 'Offline native fixture', goal: 'Verify host-mediated execution', targets: [{ platform: 'amazon-us', market: 'US', language: 'en', placements: [kind === 'image' ? 'amazon-gallery' : `amazon-${kind}`] }], products: [{ sku: 'sku', name: 'Blue product', category: 'test', facts: [{ id: 'color', text: 'Blue', source: { kind: 'user-confirmed', note: 'Fixture fact' } }] }], references: [{ id: 'front', sku: 'sku', path: photo, source: 'user-product-photo' }], budget: { currency: 'USD', maxEstimatedCostUsd: 1, maxAttemptsPerDeliverable: 2 } };
  const ref = { ...brief.references[0], sha256: info.sha256, mimeType: info.mimeType, width: info.width, height: info.height };
  let state = initProject(brief, [ref], now(), transport);
  state = setResearch(state, { scope: 'Offline fixture', rules: [{ id: 'rule', platform: 'amazon-us', placement: brief.targets[0].placements[0], requirement: 'Accurate product', status: 'mandatory', sourceUrl: 'https://example.com/rule', publisher: 'Fixture', fetchedAt: now(), effectiveAt: null, conflict: null }], examples: [], exampleLimitations: [{ platform: 'amazon-us', reason: 'Offline fixture' }], synthesis: ['Preserve product identity'], limitations: ['Not live evidence'] });
  const deliverable = { id: 'asset', sku: 'sku', platform: 'amazon-us', placement: brief.targets[0].placements[0], kind, referenceIds: ['front'], claimIds: ['color'], ruleIds: ['rule'], prompt: 'Show the actual blue product accurately.', model, ...(kind === 'image' ? { imageMode: 'edit', size: '512x512' } : kind === 'video' ? { size: '512x512', durationSeconds: 5 } : { copyLimits: { title: 40 } }), ...(model === 'host-copy' ? {} : { nativeRequest: plan(kind, model), pricingSource: 'Fixture quote', pricingCheckedAt: now() }), estimatedCostUsd: model === 'host-copy' ? 0 : 0.1, successCriteria: ['Faithful product'] };
  state = setPlaybook(state, { title: 'Offline plan', version: '1', summary: 'Fixture', creativeDirection: 'Accurate', deliverables: [deliverable], budget: { estimatedTotalUsd: deliverable.estimatedCostUsd, maxAttemptsPerDeliverable: 2, costControl: 'estimate-only' }, approvalNotes: ['Offline validation only; no paid call'] });
  state = approvePlaybook(state, { actor: 'user', message: 'Approve this exact offline fixture.', playbookHash: approvalHash(state) });
  const directory = join(root, 'project'); await atomicJson(join(directory, 'project.json'), state);
  const connection = { transport, server: 'https://mcp.aisa.one/mcp', connected: true, checkedAt: now(), receiptId: 'account-check-1' };
  await importConnection(directory, state, connection);
  return { root, directory, photo, state, connection };
}
async function preparation(f, jobId) {
  const built = await buildNativeRequest(f.directory, f.state, 'asset', jobId);
  return { deliverableId: 'asset', sessionId: 'session-fixture', searchId: 'search-fixture', connectionReceiptId: f.connection.receiptId,
    quote: { requestId: 'quote-fixture', tool: built.tool, sessionId: 'session-fixture', argumentsHash: built.argumentsHash, quotedAt: now(), currency: 'USD', estimatedCostUsd: jobId ? 0 : 0.1, estimateKind: 'exact', mayExceedEstimate: false, maxCostUsd: jobId ? 0 : 0.1, source: { status: 'success', estimated_cost_micros_usd: jobId ? 0 : 100000, estimate_kind: 'exact', max_cost_micros_usd: jobId ? 0 : 100000, may_exceed_estimate: false } } };
}
async function prepared(f) { return prepareNative(f.directory, f.state, await preparation(f)); }
const receipt = (operation, data, overrides = {}) => ({ tool: operation.tool, sessionId: operation.sessionId, argumentsHash: operation.argumentsHash, requestId: `result-${operation.id}`, outcome: 'success', data, customerCostMicrosUsd: 35000, ...overrides });
async function dispatch(f) { const preparedJob = await prepared(f); await markNativeDispatched(f.directory, f.state, preparedJob.operation.id); return preparedJob; }
async function imageData(f) { return { data: [{ b64_json: (await readFile(f.photo)).toString('base64') }] }; }

// These use local fixtures. They verify adapter contracts, not live model acceptance.
test('new projects default to MCP while missing-transport historical states retain legacy identity', async t => {
  const f = await fixture(t);
  assert.equal(initProject(f.state.brief, f.state.references).transport, 'mcp');
  const legacy = structuredClone(f.state); delete legacy.transport; delete legacy.playbook; delete legacy.approval;
  assert.equal(validateProject(legacy).transport, undefined);
});
test('model choice follows catalog evidence rather than a name allowlist', async t => {
  const f = await fixture(t);
  for (const model of ['gpt-image-2', 'gpt-image-2.5-flare', 'gpt-image-2.5-sunburst', 'seedream-5-0-260128', 'wan2.7-image', 'wan2.7-image-pro', 'a-new-catalog-model']) {
    const book = structuredClone(f.state.playbook); book.deliverables[0].model = model; book.deliverables[0].nativeRequest.catalog.modelIds = [model];
    assert.equal(setPlaybook(f.state, book).playbook.deliverables[0].model, model);
  }
  const book = structuredClone(f.state.playbook); book.deliverables[0].model = 'not-discovered';
  assert.throws(() => setPlaybook(f.state, book), /absent.*catalog/);
});
test('request injects exact approved prompt/photos and preserves model-specific options', async t => {
  const f = await fixture(t); const built = await buildNativeRequest(f.directory, f.state, 'asset'); const saved = JSON.parse(await readFile(built.path));
  assert.equal(saved.arguments.body.model, 'future-reference-model'); assert.equal(saved.arguments.body.quality, 'high');
  assert.equal(saved.arguments.body.prompt, productionPrompt(f.state, f.state.playbook.deliverables[0]));
  assert.equal(saved.arguments.body.image[0], `data:image/png;base64,${(await readFile(f.photo)).toString('base64')}`);
  assert.equal(digestJson(saved.arguments), built.argumentsHash);
});
test('unsupported references, overlapping bindings, credentials and stale discovery are blocked', async t => {
  const f = await fixture(t);
  for (const change of [p => { p.modelContract.supportsReferences = false; }, p => { p.referenceBindings = []; }, p => { p.promptPointer = p.modelPointer; }, p => { p.argumentsTemplate.api_key = 'secret'; }]) {
    const book = structuredClone(f.state.playbook); change(book.deliverables[0].nativeRequest); assert.throws(() => setPlaybook(f.state, book), /reference|bindings|credentials/i);
  }
  const state = structuredClone(f.state); state.playbook.deliverables[0].nativeRequest.catalog.checkedAt = '2020-01-01T00:00:00Z';
  state.approval.playbookHash = approvalHash(state);
  await assert.rejects(buildNativeRequest(f.directory, state, 'asset'), /stale/);
});
test('full JSON Schema enforces nested refs, alternatives and additional properties', () => {
  const schema = { type: 'object', $defs: { body: { type: 'object', required: ['value'], additionalProperties: false, properties: { value: { oneOf: [{ type: 'integer', minimum: 1 }, { type: 'string', pattern: '^ok$' }] } } } }, properties: { body: { $ref: '#/$defs/body' } }, required: ['body'], additionalProperties: false };
  assert.doesNotThrow(() => assertSchema({ body: { value: 1 } }, schema, 'test'));
  for (const data of [{ body: { value: 0 } }, { body: { value: 'bad' } }, { body: JSON.stringify({ value: 1 }) }, { body: { value: 1, extra: true } }]) assert.throws(() => assertSchema(data, schema, 'test'), /schema/);
});
test('quote mismatch or upper-bound cost over approval creates no job', async t => {
  const f = await fixture(t); const input = await preparation(f);
  for (const patch of [{ argumentsHash: '0'.repeat(64) }, { sessionId: 'other' }, { tool: 'different' }, { estimateKind: 'upper_bound', estimatedCostUsd: 0.01, maxCostUsd: 0.2 }]) {
    await assert.rejects(prepareNative(f.directory, f.state, { ...input, quote: { ...input.quote, ...patch } }), /Quote|quote/);
  }
  assert.equal((await loadLedger(f.directory)).jobs.length, 0);
});
test('MCP and CLI both require host connection and never construct REST clients', async t => {
  for (const transport of ['mcp', 'cli']) {
    const f = await fixture(t, 'image', transport); let calls = 0;
    await assert.rejects(generate(f.directory, f.state, 'asset', { generateImages: async () => { calls++; } }), /prepare-native/);
    await rm(join(f.directory, 'connection.json'));
    await assert.rejects(buildNativeRequest(f.directory, f.state, 'asset'), /Connect AIsa/);
    assert.equal(calls, 0);
  }
});
test('all handoff envelope fields and call count remain bound before dispatch', async t => {
  const f = await fixture(t); const { operation } = await prepared(f); const original = JSON.parse(await readFile(operation.requestPath));
  for (const mutate of [v => { v.session_id = 'other'; }, v => { v.search_id = 'other'; }, v => { v.calls.push(structuredClone(v.calls[0])); }, v => { v.calls[0].call_id = 'other'; }, v => { v.server = 'https://other.example'; }, v => { v.transport = 'rest'; }, v => { v.calls[0].arguments.body.quality = 'low'; }]) {
    const data = structuredClone(original); mutate(data); await atomicJson(operation.requestPath, data);
    await assert.rejects(markNativeDispatched(f.directory, f.state, operation.id), /changed/);
  }
  await atomicJson(operation.requestPath, original); await markNativeDispatched(f.directory, f.state, operation.id);
  await assert.rejects(markNativeDispatched(f.directory, f.state, operation.id), /already dispatched/);
});
test('native image result enters the shared review/export workflow with transport and billing provenance', async t => {
  const f = await fixture(t); const { operation } = await dispatch(f);
  const job = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, await imageData(f)));
  assert.equal(job.status, 'needs-review'); assert.equal(job.artifacts.length, 1);
  await assert.rejects(exportPackage(f.directory, f.state, join(f.root, 'export')), /not reviewed/);
  await review(f.directory, f.state, { deliverableId: 'asset', inspectedBy: 'agent', artifacts: job.artifacts.map(a => ({ sha256: a.sha256, productFidelity: 'pass', platformCompliance: 'pass', copyAccuracy: 'pass', visualQuality: 'pass', notes: 'Offline fixture inspected against supplied source' })) });
  await exportPackage(f.directory, f.state, join(f.root, 'export'));
  const manifest = JSON.parse(await readFile(join(f.root, 'export', 'manifest.json')));
  assert.equal(manifest.deliverables[0].transport, 'mcp'); assert.equal(manifest.deliverables[0].native.operations[0].argumentsHash, operation.argumentsHash); assert.equal(manifest.billing.actualChargesUsd, 0.035);
});
test('unknown submission never retries or changes transport, and can accept its reconciled original receipt', async t => {
  const f = await fixture(t); const { operation } = await dispatch(f);
  const job = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, undefined, { outcome: 'unknown', error: 'Host connection closed', customerCostMicrosUsd: null }));
  assert.equal(job.status, 'uncertain');
  await assert.rejects(prepareNative(f.directory, f.state, { ...await preparation(f), retry: true }), /reconciliation/);
  const changed = structuredClone(f.state); changed.transport = 'cli'; changed.approval.playbookHash = approvalHash(changed);
  await assert.rejects(ingestNativeResult(f.directory, changed, operation.id, receipt(operation, await imageData(f))), /No native job/);
  const reconciled = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, await imageData(f)));
  assert.equal(reconciled.status, 'needs-review'); assert.equal(reconciled.receipts.length, 1); assert.equal(reconciled.receipts[0].customerCostMicrosUsd, 35000);
});
test('bad successful payload keeps an uncertain paid attempt for reconciliation', async t => {
  const f = await fixture(t); const { operation } = await dispatch(f);
  await assert.rejects(ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { data: [{ b64_json: 123 }] })), /schema/);
  assert.equal((await loadLedger(f.directory)).jobs[0].status, 'uncertain');
  await assert.rejects(prepareNative(f.directory, f.state, { ...await preparation(f), retry: true }), /reconciliation/);
});
test('401 retry needs a new successful host connection check', async t => {
  const f = await fixture(t); const { operation } = await dispatch(f);
  await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, undefined, { outcome: 'failed', statusCode: 401, error: 'invalid_api_key', customerCostMicrosUsd: 0 }));
  await assert.rejects(prepareNative(f.directory, f.state, { ...await preparation(f), retry: true }), /fresh successful/);
  f.connection.receiptId = 'account-check-2'; await importConnection(f.directory, f.state, f.connection);
  assert.equal((await prepareNative(f.directory, f.state, { ...await preparation(f), retry: true })).job.status, 'prepared');
});
test('native chat and explicitly approved host-written copy both share copy validation', async t => {
  const f = await fixture(t, 'copy'); const { operation } = await dispatch(f);
  assert.equal((await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { text: '{"title":"Blue product"}' }))).status, 'needs-review');
  const host = await fixture(t, 'copy', 'mcp', 'host-copy');
  await assert.rejects(importHostCopy(host.directory, host.state, 'asset', { producedBy: 'host', note: 'fixture', text: '{"title":"Blue","invented":"claim"}' }), /fields/);
  assert.equal((await importHostCopy(host.directory, host.state, 'asset', { producedBy: 'host', note: 'Fixture approved factual copy', text: '{"title":"Blue product"}' })).status, 'needs-review');
});
test('saved video task survives unknown/error results and polling never submits generation again', async t => {
  const f = await fixture(t, 'video'); const { operation, job: preparedJob } = await dispatch(f);
  const submitted = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, undefined, { outcome: 'unknown', statusCode: 503, taskId: 'known-task', error: 'video_submission_pending', customerCostMicrosUsd: null }));
  assert.equal(submitted.taskId, 'known-task'); assert.equal(submitted.status, 'submitted');
  const polling = await prepareNativePoll(f.directory, f.state, preparedJob.id, await preparation(f, preparedJob.id));
  assert.equal(JSON.parse(await readFile(polling.operation.requestPath)).calls[0].arguments.task_id, 'known-task');
  await markNativeDispatched(f.directory, f.state, polling.operation.id);
  assert.equal((await ingestNativeResult(f.directory, f.state, polling.operation.id, receipt(polling.operation, { id: 'known-task', status: 'unknown' }, { customerCostMicrosUsd: 0 }))).status, 'submitted');
  const second = await prepareNativePoll(f.directory, f.state, preparedJob.id, await preparation(f, preparedJob.id)); await markNativeDispatched(f.directory, f.state, second.operation.id);
  await ingestNativeResult(f.directory, f.state, second.operation.id, receipt(second.operation, undefined, { outcome: 'failed', statusCode: 503, error: 'status temporarily unavailable', customerCostMicrosUsd: 0 }));
  assert.equal((await loadLedger(f.directory)).jobs[0].status, 'submitted');
  assert.equal((await loadLedger(f.directory)).jobs[0].native.operations.filter(op => op.action === 'generate').length, 1);
});
test('frozen approved task accepts delayed results without fresh catalog/research or another generation', async t => {
  const f = await fixture(t, 'video'); const { operation } = await dispatch(f);
  const actualNow = Date.now; const future = actualNow() + 8 * 86_400_000;
  t.mock.method(Date, 'now', () => future);
  const result = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { id: 'delayed-task', status: 'queued' }));
  assert.equal(result.status, 'submitted'); assert.equal(result.taskId, 'delayed-task');
});
test('saved image download/cache materialization resumes locally with no dispatch', async t => {
  const f = await fixture(t); const { operation } = await dispatch(f); const result = await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, await imageData(f)));
  const ledger = await loadLedger(f.directory); ledger.jobs[0].status = 'download-pending'; await atomicJson(join(f.directory, 'execution.json'), ledger);
  const resumed = await resumeNative(f.directory, f.state, 'asset');
  assert.equal(resumed.artifacts[0].sha256, result.artifacts[0].sha256); assert.equal(resumed.native.operations.length, 1);
});

test('expired undispatched generation can be cancelled and requoted without consuming an attempt', async t => {
  const f = await fixture(t); const { operation } = await prepared(f);
  const ledger = await loadLedger(f.directory); ledger.jobs[0].native.operations[0].quote.quotedAt = '2020-01-01T00:00:00Z'; await atomicJson(join(f.directory, 'execution.json'), ledger);
  await assert.rejects(markNativeDispatched(f.directory, f.state, operation.id), /stale/);
  const cancelled = await cancelNativePrepared(f.directory, f.state, operation.id);
  assert.equal(cancelled.status, 'cancelled'); assert.equal(cancelled.estimatedCostUsd, 0);
  const next = await prepared(f); await markNativeDispatched(f.directory, f.state, next.operation.id);
  await assert.rejects(cancelNativePrepared(f.directory, f.state, next.operation.id), /never-dispatched/);
  assert.equal((await loadLedger(f.directory)).jobs.filter(job => job.status !== 'cancelled').length, 1);
});
test('cancelled and malformed status polls retain the task and permit a new read-only poll', async t => {
  const f = await fixture(t, 'video'); const { operation, job } = await dispatch(f);
  await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { id: 'saved-task', status: 'queued' }));
  const first = await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id));
  await cancelNativePrepared(f.directory, f.state, first.operation.id);
  const second = await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id)); await markNativeDispatched(f.directory, f.state, second.operation.id);
  await assert.rejects(ingestNativeResult(f.directory, f.state, second.operation.id, receipt(second.operation, { id: 'saved-task' }, { customerCostMicrosUsd: 0 })), /schema/);
  const saved = (await loadLedger(f.directory)).jobs[0]; assert.equal(saved.taskId, 'saved-task'); assert.equal(saved.status, 'submitted');
  const third = await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id)); assert.equal(third.operation.status, 'prepared');
});
test('a poll 401 requires fresh host verification while preserving its known task', async t => {
  const f = await fixture(t, 'video'); const { operation, job } = await dispatch(f);
  await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { id: 'saved-task', status: 'queued' }));
  const poll = await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id)); await markNativeDispatched(f.directory, f.state, poll.operation.id);
  await ingestNativeResult(f.directory, f.state, poll.operation.id, receipt(poll.operation, undefined, { outcome: 'failed', statusCode: 401, customerCostMicrosUsd: 0 }));
  await assert.rejects(prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id)), /fresh successful/);
  f.connection.receiptId = 'new-account-check'; await importConnection(f.directory, f.state, f.connection);
  assert.equal((await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id))).job.taskId, 'saved-task');
});
test('completed video poll materializes the returned media and retains source task provenance', async t => {
  const f = await fixture(t, 'video'); const video = join(f.root, 'fixture.mp4');
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x512:d=5:r=10', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '1', '-y', video]);
  const bytes = await readFile(video); t.mock.method(globalThis, 'fetch', async () => new Response(bytes));
  const { operation, job } = await dispatch(f);
  await ingestNativeResult(f.directory, f.state, operation.id, receipt(operation, { id: 'saved-task', status: 'queued' }));
  const poll = await prepareNativePoll(f.directory, f.state, job.id, await preparation(f, job.id)); await markNativeDispatched(f.directory, f.state, poll.operation.id);
  const result = await ingestNativeResult(f.directory, f.state, poll.operation.id, receipt(poll.operation, { id: 'saved-task', status: 'completed', result: { video_url: 'https://93.184.216.34/fixture.mp4' } }, { customerCostMicrosUsd: 0 }));
  assert.equal(result.status, 'needs-review'); assert.equal(result.artifacts[0].media.durationSeconds, 5); assert.equal(result.taskId, 'saved-task');
});
