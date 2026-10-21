import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm, stat, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { main } from '../dist/cli.js';
import { approvalHash, approvePlaybook, setPlaybook, setResearch } from '../dist/workflow.js';
import { generate, resume, review, exportPackage, loadLedger, validateCopy } from '../dist/production.js';
import { inspectMedia, strictBase64, saveMedia, atomicJson } from '../dist/media.js';
import { AisaError } from '../dist/aisa.js';

let mediaTools = true;
try { execFileSync('ffmpeg', ['-version'], { stdio: 'ignore' }); execFileSync('ffprobe', ['-version'], { stdio: 'ignore' }); } catch { mediaTools = false; }
const mediaTest = (name, fn) => test(name, { skip: !mediaTools && 'ffmpeg and ffprobe required for media integration checks' }, fn);
const now = () => new Date().toISOString();
function photo(path, color = 'blue') {
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', `color=c=${color}:s=512x512`, '-frames:v', '1', '-threads', '1', '-y', path]);
}
async function fixture(t, kind = 'image', preserve = false) {
  const root = await mkdtemp(join(tmpdir(), 'studio-test-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const source = join(root, 'source.png'); photo(source);
  const platform = 'shopify'; const placement = `shopify-${kind === 'image' ? 'gallery' : kind}`;
  const brief = {
    name: 'Offline test', goal: 'Verify workflow behavior', targets: [{ platform, market: 'US', language: 'en-US', placements: [placement], themeDescription: 'Square product gallery.' }],
    products: [{ sku: 'sku-1', name: 'Fixture product', category: 'test fixture', facts: [{ id: 'color', text: 'Blue', source: { kind: 'visible-in-reference', referenceId: 'front' } }] }],
    references: [{ id: 'front', sku: 'sku-1', path: source, source: 'user-product-photo' }], budget: { currency: 'USD', maxEstimatedCostUsd: 1, maxAttemptsPerDeliverable: 2 },
  };
  const briefPath = join(root, 'brief.json'); await atomicJson(briefPath, brief);
  const directory = join(root, 'project'); await main(['init', briefPath, directory]);
  let state = JSON.parse(await readFile(join(directory, 'project.json')));
  state = setResearch(state, { scope: 'Offline fixture, not live evidence', rules: [{ id: 'rule', platform, placement, requirement: 'Use the approved accurate product depiction.', status: 'mandatory', sourceUrl: 'https://help.shopify.com/en/manual/products/product-media', publisher: 'Shopify', fetchedAt: now(), effectiveAt: null, conflict: null }], examples: [], exampleLimitations: [{ platform, reason: 'Offline test has no performance data.' }], synthesis: ['Keep product identity.'], limitations: ['No real performance inference.'] });
  const deliverable = {
    id: 'asset', sku: 'sku-1', platform, placement, kind, referenceIds: ['front'], claimIds: ['color'], ruleIds: ['rule'], prompt: 'Accurate product content.', model: preserve ? 'local-photo-export' : 'fixture-model',
    ...(kind === 'image' ? { imageMode: preserve ? 'preserve' : 'edit', imageSize: '1K', size: '512x512' } : kind === 'video' ? { size: '512x512', durationSeconds: 5, allowExperimentalVideo: true } : { copyLimits: { title: 75, description: 200 } }),
    estimatedCostUsd: preserve ? 0 : 0.1, ...(preserve ? {} : { pricingSource: 'Offline fixture estimate only', pricingCheckedAt: now() }), successCriteria: ['Truthful product and legible text.'],
  };
  state = setPlaybook(state, { title: 'Fixture playbook', version: '1', summary: 'Offline test.', creativeDirection: 'Plain product depiction.', deliverables: [deliverable], budget: { estimatedTotalUsd: deliverable.estimatedCostUsd, maxAttemptsPerDeliverable: 2, costControl: 'estimate-only' }, approvalNotes: ['This is offline testing, not commercial content.'] });
  state = approvePlaybook(state, { actor: 'user', message: 'Approve this fixture playbook for offline tests.', playbookHash: approvalHash(state) });
  await atomicJson(join(directory, 'project.json'), state);
  return { root, directory, source, state, deliverable };
}
const findings = job => ({ deliverableId: job.deliverableId, inspectedBy: 'agent', artifacts: [...new Map(job.artifacts.map(a => [a.sha256, a])).values()].map(a => ({ sha256: a.sha256, productFidelity: 'pass', platformCompliance: 'pass', copyAccuracy: 'pass', visualQuality: 'pass', notes: 'Offline fixture: exact product pixels, dimensions and hash inspected by assertions.' })) });

test('base64 rejects the previously accepted empty corrupt payload', () => {
  assert.throws(() => strictBase64('!!!!'), /base64/);
  assert.throws(() => strictBase64(''), /base64/);
});
test('copy field validation counts Unicode characters and rejects unexpected claims fields', () => {
  assert.deepEqual(validateCopy('{"title":"商品图"}', { copyLimits: { title: 3 } }), { title: '商品图' });
  assert.throws(() => validateCopy('{"title":"long"}', { copyLimits: { title: 3 } }), /limit/);
  assert.throws(() => validateCopy('{"title":"A","claim":"invented"}', { copyLimits: { title: 75 } }), /fields/);
});
test('CLI rejects a missing-photo brief without starting a project', async t => {
  const root = await mkdtemp(join(tmpdir(), 'studio-empty-')); t.after(() => rm(root, { recursive: true, force: true }));
  await atomicJson(join(root, 'brief.json'), { name: 'Empty', goal: 'Test', targets: [{ platform: 'amazon-us', market: 'US', language: 'en', placements: ['amazon-copy'] }], references: [] });
  await assert.rejects(main(['init', join(root, 'brief.json'), join(root, 'project')]), /photos|references/);
  await assert.rejects(stat(join(root, 'project')), { code: 'ENOENT' });
});
mediaTest('preserved product photo requires review before export and exports complete provenance', async t => {
  const f = await fixture(t, 'image', true);
  const job = await generate(f.directory, f.state, 'asset');
  assert.equal(job.status, 'needs-review'); assert.equal(job.artifacts.length, 1);
  const inspected = await inspectMedia(job.artifacts[0].path, 'image'); assert.equal(inspected.width, 512);
  await assert.rejects(exportPackage(f.directory, f.state, join(f.root, 'export')), /not reviewed/);
  const wrong = findings(job); wrong.artifacts[0].sha256 = '0'.repeat(64);
  await assert.rejects(review(f.directory, f.state, wrong), /hash/);
  await review(f.directory, f.state, findings(job));
  const exported = await exportPackage(f.directory, f.state, join(f.root, 'export'));
  assert.equal(exported.files, 4);
  const manifest = JSON.parse(await readFile(join(exported.destination, 'manifest.json')));
  assert.equal(manifest.approval.playbookHash, approvalHash(f.state));
  assert.equal(manifest.deliverables[0].artifacts[0].sha256, inspected.sha256);
});
mediaTest('unapproved or mutated references cause zero provider submissions', async t => {
  const f = await fixture(t); let calls = 0;
  const client = { generateImages: async () => { calls++; throw new Error('Must not call'); } };
  const unapproved = structuredClone(f.state); delete unapproved.approval;
  await assert.rejects(generate(f.directory, unapproved, 'asset', client), /approval/);
  photo(f.state.references[0].path, 'red');
  await assert.rejects(generate(f.directory, f.state, 'asset', client), /photo.*changed/);
  assert.equal(calls, 0);
});
mediaTest('all returned image candidates are retained in nested job folders', async t => {
  const f = await fixture(t); const other = join(f.root, 'other.png'); photo(other, 'red');
  const client = { generateImages: async () => ({ images: [{ data: await readFile(f.source), mimeType: 'image/png' }, { data: await readFile(other), mimeType: 'image/png' }], text: '' }) };
  const job = await generate(f.directory, f.state, 'asset', client);
  assert.equal(job.artifacts.length, 2); assert.notEqual(job.artifacts[0].sha256, job.artifacts[1].sha256);
  for (const artifact of job.artifacts) assert.ok((await stat(artifact.path)).size > 0);
  await assert.rejects(generate(f.directory, f.state, 'asset', client), /already has a job/);
});
mediaTest('ambiguous submissions cannot be resubmitted and retain the known provider task ID', async t => {
  const f = await fixture(t);
  const ambiguous = { generateImages: async () => { throw new AisaError('timeout', 'Timed out.', undefined, true); } };
  await assert.rejects(generate(f.directory, f.state, 'asset', ambiguous), /uncertain/);
  await assert.rejects(generate(f.directory, f.state, 'asset', ambiguous, true), /reconciliation/);
  const ledger = await loadLedger(f.directory); assert.equal(ledger.jobs.length, 1);
});
mediaTest('invalid generated copy is saved, rejected and retries consume the bounded allowance', async t => {
  const f = await fixture(t, 'copy'); let calls = 0;
  const client = { copy: async () => { calls++; return { text: '{"title":"A"}' }; } };
  await assert.rejects(generate(f.directory, f.state, 'asset', client), /rejected/);
  const first = (await loadLedger(f.directory)).jobs[0];
  assert.match(await readFile(first.responsePath, 'utf8'), /title/);
  await assert.rejects(generate(f.directory, f.state, 'asset', client, true), /rejected/);
  await assert.rejects(generate(f.directory, f.state, 'asset', client, true), /attempt limit/);
  assert.equal(calls, 2);
});
mediaTest('successful copy validates fields, then blocks export when modified after review', async t => {
  const f = await fixture(t, 'copy');
  const job = await generate(f.directory, f.state, 'asset', { copy: async () => ({ text: '{"title":"Blue product","description":"Product shown in the supplied reference."}' }) });
  await review(f.directory, f.state, findings(job));
  await writeFile(job.artifacts[0].path, 'changed');
  await assert.rejects(exportPackage(f.directory, f.state, join(f.root, 'export')), /Artifact changed/);
});
mediaTest('video without a verified remote reference fails before creating or charging a job', async t => {
  const f = await fixture(t, 'video'); let calls = 0;
  await assert.rejects(generate(f.directory, f.state, 'asset', { submitVideo: async () => { calls++; } }), /remoteUrl/);
  assert.equal(calls, 0); assert.equal((await loadLedger(f.directory)).jobs.length, 0);
});
mediaTest('resume retries a saved response without a new generation submission', async t => {
  const f = await fixture(t);
  const job = await generate(f.directory, f.state, 'asset', { generateImages: async () => ({ images: [{ data: await readFile(f.source), mimeType: 'image/png' }], text: '' }) });
  const ledger = await loadLedger(f.directory); ledger.jobs[0].status = 'download-pending'; await atomicJson(join(f.directory, 'execution.json'), ledger);
  const resumed = await resume(f.directory, f.state, 'asset');
  assert.equal(resumed.status, 'needs-review'); assert.equal(resumed.artifacts[0].sha256, job.artifacts[0].sha256);
});
mediaTest('invalid media cannot overwrite an existing good artifact', async t => {
  const f = await fixture(t);
  const target = join(f.root, 'saved'); const original = await saveMedia(await readFile(f.source), target, 'image');
  await assert.rejects(saveMedia(Buffer.from('<html>error</html>'), target, 'image'), /corrupt/);
  assert.equal((await inspectMedia(original.path, 'image')).sha256, original.sha256);
  await assert.rejects(saveMedia(await readFile(f.source), target, 'image'), /already exists/);
});

async function reapprove(f, mutate) {
  mutate(f.state);
  f.state = setPlaybook(f.state, f.state.playbook);
  f.state = approvePlaybook(f.state, { actor: 'user', message: 'Approve this updated offline fixture.', playbookHash: approvalHash(f.state) });
  await atomicJson(join(f.directory, 'project.json'), f.state);
}
async function remoteVideo(t) {
  const f = await fixture(t, 'video');
  const remoteUrl = 'https://93.184.216.34/product.png';
  await reapprove(f, state => { state.brief.references[0].remoteUrl = remoteUrl; state.references[0].remoteUrl = remoteUrl; });
  return { ...f, remoteUrl };
}
function video(path) {
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=512x512:d=5:r=10', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '1', '-y', path]);
}
mediaTest('duplicate candidate bytes are retained and share one hash-bound review', async t => {
  const f = await fixture(t); const bytes = await readFile(f.source);
  const job = await generate(f.directory, f.state, 'asset', { generateImages: async () => ({ images: [{ data: bytes, mimeType: 'image/png' }, { data: bytes, mimeType: 'image/png' }], text: '' }) });
  assert.equal(job.artifacts.length, 2); assert.equal(job.artifacts[0].sha256, job.artifacts[1].sha256);
  assert.equal((await review(f.directory, f.state, findings(job))).status, 'approved');
  assert.equal((await exportPackage(f.directory, f.state, join(f.root, 'export'))).files, 5);
});
mediaTest('native generated images are retained and only downsized to the approved export', async t => {
  const f = await fixture(t); await reapprove(f, state => { state.playbook.deliverables[0].size = '300x300'; });
  let request;
  const job = await generate(f.directory, f.state, 'asset', { generateImages: async input => { request = input; return { images: [{ data: await readFile(f.source), mimeType: 'image/png' }], text: '' }; } });
  assert.equal(request.imageSize, '1K');
  assert.equal((await inspectMedia(join(f.directory, 'jobs', job.id, 'source-1.png'), 'image')).width, 512);
  assert.equal((await inspectMedia(job.artifacts[0].path, 'image')).width, 300);
});
mediaTest('review and export cannot override a technical dimension rejection', async t => {
  const f = await fixture(t, 'image', true); const job = await generate(f.directory, f.state, 'asset');
  const path = job.artifacts[0].path;
  execFileSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=300x300', '-frames:v', '1', '-threads', '1', '-y', path]);
  const media = await inspectMedia(path, 'image');
  const ledger = await loadLedger(f.directory); Object.assign(ledger.jobs[0].artifacts[0], { sha256: media.sha256, media }); ledger.jobs[0].status = 'rejected';
  await atomicJson(join(f.directory, 'execution.json'), ledger);
  await assert.rejects(review(f.directory, f.state, findings(ledger.jobs[0])), /dimensions/);
  ledger.jobs[0].status = 'approved'; await atomicJson(join(f.directory, 'execution.json'), ledger);
  await assert.rejects(exportPackage(f.directory, f.state, join(f.root, 'export')), /dimensions/);
});
mediaTest('video requires disclosed experimental opt-in before approval', async t => {
  const f = await fixture(t, 'video'); const plan = structuredClone(f.state.playbook);
  delete plan.deliverables[0].allowExperimentalVideo;
  assert.throws(() => setPlaybook(f.state, plan), /experimental/);
});
mediaTest('known video task survives local response-save failure and cannot be resubmitted', async t => {
  const f = await remoteVideo(t); const bytes = await readFile(f.source); let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => new Response(bytes));
  const client = { submitVideo: async () => {
    calls++; const job = (await loadLedger(f.directory)).jobs.at(-1);
    await mkdir(join(f.directory, 'jobs', job.id, 'response.json'));
    return { id: 'known-task', status: 'queued', urls: [] };
  } };
  await assert.rejects(generate(f.directory, f.state, 'asset', client), /status: submitted/);
  const saved = (await loadLedger(f.directory)).jobs[0]; assert.equal(saved.taskId, 'known-task');
  await assert.rejects(generate(f.directory, f.state, 'asset', client, true), /reconciliation/); assert.equal(calls, 1);
});
mediaTest('expired video download is refreshed from the saved task without resubmission', async t => {
  const f = await remoteVideo(t); const source = await readFile(f.source); const path = join(f.root, 'clip.mp4'); video(path); const bytes = await readFile(path);
  let posts = 0; let polls = 0;
  t.mock.method(globalThis, 'fetch', async url => String(url).endsWith('product.png') ? new Response(source) : String(url).endsWith('expired.mp4') ? new Response('Expired', { status: 403 }) : new Response(bytes));
  const client = {
    submitVideo: async () => { posts++; return { id: 'saved-task', status: 'queued', urls: [], receipt: { customerCostMicrosUsd: 80000, requestId: 'video-submit' } }; },
    getVideoJob: async id => { assert.equal(id, 'saved-task'); polls++; return { id, status: 'succeeded', urls: [`https://93.184.216.34/${polls === 1 ? 'expired' : 'fresh'}.mp4`], receipt: { customerCostMicrosUsd: 0, requestId: `video-poll-${polls}` } }; },
  };
  await generate(f.directory, f.state, 'asset', client);
  await assert.rejects(resume(f.directory, f.state, 'asset', client), /HTTP 403/);
  assert.equal((await resume(f.directory, f.state, 'asset', client)).status, 'needs-review');
  assert.equal(posts, 1); assert.equal(polls, 2);
  assert.deepEqual((await loadLedger(f.directory)).jobs[0].receipts.map(receipt => receipt.requestId), ['video-submit', 'video-poll-1', 'video-poll-2']);
});
mediaTest('video above the approved file size is saved and rejected instead of stuck downloading', async t => {
  const f = await remoteVideo(t); await reapprove(f, state => { state.playbook.deliverables[0].constraints = { maxBytes: 1 }; });
  const source = await readFile(f.source); const path = join(f.root, 'clip.mp4'); video(path); const bytes = await readFile(path);
  t.mock.method(globalThis, 'fetch', async url => new Response(String(url).endsWith('product.png') ? source : bytes));
  const client = { submitVideo: async () => ({ id: 'oversized-task', status: 'succeeded', urls: ['https://93.184.216.34/output.mp4'] }) };
  await assert.rejects(generate(f.directory, f.state, 'asset', client), /file-size limit.*status: rejected/);
  const job = (await loadLedger(f.directory)).jobs[0]; assert.equal(job.status, 'rejected'); assert.ok((await stat(job.artifacts[0].path)).size > 1);
  await assert.rejects(resume(f.directory, f.state, 'asset', client), /Job is rejected/);
});
mediaTest('corrupt provider media becomes a rejected output with a saved raw response', async t => {
  const f = await fixture(t);
  await assert.rejects(generate(f.directory, f.state, 'asset', { generateImages: async () => ({ images: [{ data: Buffer.from('not an image'), mimeType: 'image/png' }], text: '' }) }), /status: rejected/);
  const job = (await loadLedger(f.directory)).jobs[0]; assert.ok((await stat(job.responsePath)).size > 0);
});

mediaTest('unsupported or undersized native image plans fail before reserving an attempt', async t => {
  const f = await fixture(t); let calls = 0;
  const client = { generateImages: async () => { calls++; throw new Error('Must not dispatch'); } };
  for (const patch of [
    { size: '1200x628', imageSize: '1K' },
    { size: '1024x1024', imageSize: '4K' },
    { size: '1200x1200', imageSize: '1K' },
  ]) {
    const plan = structuredClone(f.state.playbook);
    Object.assign(plan.deliverables[0], { model: 'gpt-image-2', ...patch });
    assert.throws(() => setPlaybook(f.state, plan), /aspect ratio|native size|native image size/);
    await assert.rejects(generate(f.directory, { ...f.state, playbook: plan }, 'asset', client), /aspect ratio|native size|native image size/);
    assert.equal((await loadLedger(f.directory)).jobs.length, 0);
  }
  assert.equal(calls, 0);
});

mediaTest('successful image and copy cache-write failures retain a resumable result without another paid call', async t => {
  for (const kind of ['image', 'copy']) {
    const f = await fixture(t, kind); let calls = 0;
    const receipt = { customerCostMicrosUsd: 12345, requestId: `saved-${kind}` };
    const success = async () => {
      calls++;
      const job = (await loadLedger(f.directory)).jobs.at(-1);
      await mkdir(join(f.directory, 'jobs', job.id, 'response.json'));
      return kind === 'image'
        ? { images: [{ data: await readFile(f.source), mimeType: 'image/png' }], text: '', receipt }
        : { text: '{"title":"Blue product","description":"The supplied product."}', receipt };
    };
    const client = { generateImages: success, copy: success };
    await assert.rejects(generate(f.directory, f.state, 'asset', client), /status: download-pending/);
    const job = (await loadLedger(f.directory)).jobs[0];
    assert.ok(job.cachedResponse);
    assert.deepEqual(job.receipts, [receipt]);
    await assert.rejects(generate(f.directory, f.state, 'asset', client, true), /reconciliation/);
    await rm(job.responsePath, { recursive: true });
    const resumed = await resume(f.directory, f.state, 'asset');
    assert.equal(resumed.status, 'needs-review');
    assert.equal(resumed.cachedResponse, undefined);
    assert.equal((await loadLedger(f.directory)).jobs[0].cachedResponse, undefined);
    assert.equal(calls, 1);
  }
});

mediaTest('settled receipts survive generation, export and paid-call failure while missing cost stays unknown', async t => {
  for (const receipt of [{ customerCostMicrosUsd: 12345, requestId: 'paid-copy' }, undefined]) {
    const f = await fixture(t, 'copy');
    const job = await generate(f.directory, f.state, 'asset', { copy: async () => ({ text: '{"title":"Blue product","description":"The supplied product."}', ...(receipt ? { receipt } : {}) }) });
    assert.deepEqual(job.receipts, receipt ? [receipt] : undefined);
    await review(f.directory, f.state, findings(job));
    const exported = await exportPackage(f.directory, f.state, join(f.root, 'export'));
    const manifest = JSON.parse(await readFile(join(exported.destination, 'manifest.json')));
    assert.deepEqual(manifest.deliverables[0].receipts, receipt ? [receipt] : []);
    assert.equal(manifest.billing.knownSettledCostMicrosUsd, receipt ? 12345 : 0);
    assert.equal(manifest.billing.actualChargesUsd, receipt ? 0.012345 : null);
    assert.equal(manifest.billing.unsettledCostJobs, receipt ? 0 : 1);
  }
  const f = await fixture(t);
  const error = new AisaError('invalid_media', 'Rejected provider output.');
  error.receipt = { customerCostMicrosUsd: 9000, requestId: 'charged-invalid-output' };
  await assert.rejects(generate(f.directory, f.state, 'asset', { generateImages: async () => { throw error; } }), /Rejected provider output/);
  assert.deepEqual((await loadLedger(f.directory)).jobs[0].receipts, [error.receipt]);
});
