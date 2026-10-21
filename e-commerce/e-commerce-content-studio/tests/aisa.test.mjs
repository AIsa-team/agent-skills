import test from 'node:test';
import assert from 'node:assert/strict';
import { AisaClient, AisaError, parseVideoJob } from '../dist/aisa.js';

const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5M8AAAAASUVORK5CYII=', 'base64');
const reference = { data: png, mimeType: 'image/png' };
const imageModel = { id: 'catalog-image', aisa: { model_type: 'image', capabilities: ['image', 'edit'], routes: [{ method: 'POST', path: '/v1beta/models/{model}:generateContent' }] } };
const textModel = { id: 'catalog-text', aisa: { model_type: 'text', routes: [{ method: 'POST', path: '/v1/chat/completions' }] } };
const videoModel = { id: 'wan2.7-i2v', aisa: { model_type: 'video', routes: [{ method: 'POST', path: '/v1/video/generations' }, { method: 'GET', path: '/v1/video/generations/{task_id}' }] } };
const models = { data: [imageModel, textModel, videoModel] };
const json = (value, status = 200, headers = {}) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json', ...headers } });
const inline = { inline_data: { mime_type: 'image/png', data: png.toString('base64') } };
function fake(responses) {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options, body: options.body ? JSON.parse(options.body) : undefined });
    const value = responses.shift();
    if (typeof value === 'function') return value(url, options);
    if (value instanceof Error) throw value;
    if (!value) throw new Error('Unexpected fetch');
    return value;
  };
  return { calls, client: new AisaClient({ apiKey: 'test-key-never-log', fetch }) };
}

test('images send actual product bytes and retain all images across candidates', async () => {
  const f = fake([json(models), json({ candidates: [
    { finishReason: 'STOP', content: { parts: [{ text: 'First' }, inline, inline] } },
    { finishReason: 'STOP', content: { parts: [{ inlineData: { mimeType: 'image/png', data: png.toString('base64') } }] } },
  ] })]);
  const result = await f.client.generateImages({ model: imageModel.id, prompt: 'Keep SKU identical.', references: [reference], aspectRatio: '1:1', imageSize: '2K' });
  assert.equal(result.images.length, 3);
  assert.deepEqual(Buffer.from(result.images[2].data), png);
  assert.equal(result.text, 'First');
  const generation = f.calls[1];
  assert.equal(generation.url, 'https://api.aisa.one/v1beta/models/catalog-image:generateContent');
  assert.equal(generation.body.contents[0].parts[1].inline_data.data, png.toString('base64'));
  assert.equal(generation.body.generationConfig.imageConfig.aspectRatio, '1:1');
  assert.equal(generation.body.generationConfig.imageConfig.imageSize, '2K');
  assert.equal(generation.options.redirect, 'error');
});

test('missing or corrupt product images stop before catalog or paid network calls', async () => {
  const f = fake([]);
  await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [] }), { code: 'product_photos_required' });
  await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [{ data: Buffer.from('<html>'), mimeType: 'image/png' }] }), { code: 'invalid_media' });
  assert.equal(f.calls.length, 0);
});

test('an advertised image model on an unsupported route cannot silently become text-only generation', async () => {
  const f = fake([json({ data: [{ ...imageModel, aisa: { model_type: 'image', routes: [{ method: 'POST', path: '/v1/images/generations' }] } }] })]);
  await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [reference] }), { code: 'unsupported_model' });
  assert.equal(f.calls.length, 1);
});

test('known route without image model type is insufficient capability evidence', async () => {
  const f = fake([json({ data: [{ ...imageModel, aisa: { ...imageModel.aisa, model_type: 'text' } }] })]);
  await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [reference] }), { code: 'unsupported_model' });
  assert.equal(f.calls.length, 1);
});

test('bad base64, mislabeled images, and text-only outputs fail', async () => {
  for (const parts of [
    [{ inline_data: { mime_type: 'image/png', data: '!!!!' } }],
    [{ inline_data: { mime_type: 'image/png', data: Buffer.from('<html>not an image</html>').toString('base64') } }],
    [{ text: 'No image available.' }],
  ]) {
    const f = fake([json(models), json({ candidates: [{ content: { parts } }] })]);
    await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [reference] }), (error) => ['invalid_media', 'no_images'].includes(error.code));
    assert.equal(f.calls.length, 2);
  }
});

test('HTTP errors are immediate, redact provider bodies, and never retry', async () => {
  const f = fake([json({ error: { message: 'test-key-never-log https://signed.example/?secret=hidden' } }, 401)]);
  await assert.rejects(f.client.getVideoJob('job-123'), (error) => {
    assert.ok(error instanceof AisaError);
    assert.equal(error.httpStatus, 401);
    assert.equal(error.ambiguous, false);
    assert.doesNotMatch(error.message, /test-key|signed|secret/);
    return true;
  });
  assert.equal(f.calls.length, 1);
});

test('submission network failure is ambiguous and no POST is repeated', async () => {
  const f = fake([json(models), new Error('secret provider response')]);
  await assert.rejects(f.client.submitVideo({ model: videoModel.id, prompt: 'x', referenceUrls: ['https://images.example/product.png'] }), (error) => error.code === 'network_error' && error.ambiguous && !error.message.includes('secret'));
  assert.equal(f.calls.length, 2);
});

test('a non-JSON response cannot masquerade as success', async () => {
  const f = fake([new Response('<html>Access denied</html>', { headers: { 'Content-Type': 'text/html' } })]);
  await assert.rejects(f.client.listModels(), { code: 'invalid_response' });
});

test('request deadlines abort pending work', async () => {
  const fetch = async (_, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('secret')), { once: true });
  });
  const client = new AisaClient({ apiKey: 'test', fetch, timeoutMs: 5 });
  await assert.rejects(client.listModels(), { code: 'timeout', ambiguous: false });
});

test('request deadlines cover the response body too', async () => {
  const fetch = async (_, options) => new Response(new ReadableStream({ start(controller) {
    options.signal.addEventListener('abort', () => controller.error(new Error('body timeout')), { once: true });
  } }), { headers: { 'Content-Type': 'application/json' } });
  const client = new AisaClient({ apiKey: 'test', fetch, timeoutMs: 5 });
  await assert.rejects(client.listModels(), { code: 'timeout' });
});

test('redirects never forward credentials', async () => {
  const f = fake([new Response(null, { status: 302, headers: { Location: 'https://elsewhere.example/' } })]);
  await assert.rejects(f.client.listModels(), { httpStatus: 302 });
  assert.equal(f.calls[0].options.redirect, 'error');
  assert.equal(f.calls.length, 1);
});

test('research preserves sources and reports extraction misses', async () => {
  const f = fake([
    json({ results: [{ title: 'Rule', url: 'https://official.example/rule', content: 'Snippet', raw_content: 'Full content', score: 0.9 }] }),
    json({ results: [{ url: 'https://official.example/rule', raw_content: 'Current requirements.' }], failed_results: [{ url: 'https://official.example/missing' }] }),
  ]);
  const search = await f.client.search({ query: 'Current official image requirements', includeDomains: ['official.example'] });
  assert.equal(search[0].content, 'Full content');
  assert.equal(f.calls[0].body.include_answer, false);
  assert.equal(f.calls[0].body.include_raw_content, true);
  const extract = await f.client.extract({ urls: ['https://official.example/rule', 'https://official.example/missing'] });
  assert.deepEqual(extract.failedUrls, ['https://official.example/missing']);
});

test('catalog cache cannot be corrupted by its caller', async () => {
  const f = fake([json(models), json({ choices: [{ finish_reason: 'stop', message: { content: 'Accurate copy' } }] })]);
  const listed = await f.client.listModels();
  listed[1].aisa.routes.length = 0;
  const result = await f.client.copy({ model: textModel.id, system: 'Only verified facts', prompt: 'Write a title.' });
  assert.equal(result.text, 'Accurate copy');
  assert.equal(f.calls.length, 2);
});

test('truncated copy is rejected instead of marked complete', async () => {
  const f = fake([json(models), json({ choices: [{ finish_reason: 'length', message: { content: 'Cut off title' } }] })]);
  await assert.rejects(f.client.copy({ model: textModel.id, system: 'Facts only', prompt: 'Write' }), { code: 'incomplete_output' });
});

test('video submission uses verified product HTTPS references and preserves its task ID', async () => {
  const f = fake([json(models), json({ task_id: 'job-123', status: 'queued' })]);
  const result = await f.client.submitVideo({ model: videoModel.id, prompt: 'Product reveal', referenceUrls: ['https://images.example/product.png'], duration: 5, ratio: '16:9' });
  assert.deepEqual(result, { id: 'job-123', status: 'queued', urls: [], receipt: { customerCostMicrosUsd: null } });
  assert.equal(f.calls[1].body.content[1].image_url.url, 'https://images.example/product.png');
  assert.equal(f.calls[1].body.content[1].role, 'reference_image');
});

test('video requires references before any paid or catalog request and rejects local URLs', async () => {
  const f = fake([]);
  for (const referenceUrls of [[], ['file:///tmp/product.png'], ['data:image/png;base64,abc'], ['https://127.0.0.1/product.png'], ['https://user:password@images.example/product.png']]) {
    await assert.rejects(f.client.submitVideo({ model: videoModel.id, prompt: 'x', referenceUrls }), (error) => ['product_photos_required', 'invalid_url'].includes(error.code));
  }
  assert.equal(f.calls.length, 0);
});

test('video completion collects all results but rejects missing URLs and unknown states', () => {
  const result = parseVideoJob({ output: { task_id: 'task-1', task_status: 'SUCCEEDED', results: [{ video_url: 'https://assets.example/1.mp4' }, { video_url: 'https://assets.example/2.mp4' }] } }, 'task-1');
  assert.equal(result.urls.length, 2);
  assert.equal(result.status, 'succeeded');
  assert.throws(() => parseVideoJob({ id: 'task-1', status: 'succeeded' }), { code: 'missing_video' });
  assert.throws(() => parseVideoJob({ id: 'task-1', status: 'not_a_known_state' }), { code: 'unknown_job_status' });
  assert.throws(() => parseVideoJob({ id: 'task-other', status: 'queued' }, 'task-1'), { code: 'invalid_response' });
  assert.equal(parseVideoJob({ id: 'task-1', status: 'failed' }).status, 'failed');
});

test('malformed submission keeps a recoverable task ID and is explicitly ambiguous', async () => {
  const f = fake([json(models), json({ task_id: 'job-keep-me', status: 'new_state' })]);
  await assert.rejects(f.client.submitVideo({ model: videoModel.id, prompt: 'x', referenceUrls: ['https://images.example/product.png'] }), { code: 'unknown_job_status', taskId: 'job-keep-me', ambiguous: true });
});

test('poll only queries the saved task and never submits another video', async () => {
  const f = fake([json({ id: 'job-123', status: 'running' }), json({ id: 'job-123', status: 'succeeded', content: { video_url: 'https://assets.example/out.mp4' } })]);
  assert.equal((await f.client.getVideoJob('job-123')).status, 'running');
  assert.equal((await f.client.getVideoJob('job-123')).urls[0], 'https://assets.example/out.mp4');
  assert.ok(f.calls.every((call) => call.options.method === 'GET' && call.url.endsWith('/v1/video/generations/job-123')));
});

test('settled cost receipts remain separate from provider JSON on image and copy results', async () => {
  const headers = { 'X-AISA-Customer-Cost-Micros-USD': '23450', 'x-request-id': 'req:valid_1.2-3', 'x-provider-secret': 'never-save-me' };
  const f = fake([
    json(models, 200, { 'X-AISA-Customer-Cost-Micros-USD': '999', 'x-request-id': 'catalog-request' }),
    json({ candidates: [{ content: { parts: [inline] } }], receipt: { customerCostMicrosUsd: 0 } }, 200, headers),
    json({ choices: [{ message: { content: 'Facts only' } }], usage: { total_tokens: 12 } }, 200, { 'X-AISA-Customer-Cost-Micros-USD': '0', 'request-id': 'copy-request' }),
  ]);
  const images = await f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [reference] });
  assert.deepEqual(images.receipt, { customerCostMicrosUsd: 23450, requestId: 'req:valid_1.2-3' });
  const copy = await f.client.copy({ model: textModel.id, system: 'Facts only', prompt: 'Write' });
  assert.deepEqual(copy.receipt, { customerCostMicrosUsd: 0, requestId: 'copy-request' });
  assert.deepEqual(copy.usage, { total_tokens: 12 });
});

test('missing, malformed, negative and unsafe settled costs remain unknown, never free', async () => {
  for (const cost of [undefined, '', '-1', '1.5', '1e3', '+1', 'NaN', 'free', '9007199254740992']) {
    const f = fake([json({ id: 'job-123', status: 'running' }, 200, cost === undefined ? {} : { 'X-AISA-Customer-Cost-Micros-USD': cost })]);
    assert.deepEqual((await f.client.getVideoJob('job-123')).receipt, { customerCostMicrosUsd: null });
  }
  const f = fake([json({ id: 'job-123', status: 'running' }, 200, { 'X-AISA-Customer-Cost-Micros-USD': '9007199254740991' })]);
  assert.equal((await f.client.getVideoJob('job-123')).receipt.customerCostMicrosUsd, Number.MAX_SAFE_INTEGER);
});

test('receipt request IDs accept only bounded safe identifiers from allowlisted headers', async () => {
  for (const requestId of ['https://signed.example/?secret=hidden', 'two words', 'x'.repeat(201), '']) {
    const f = fake([json({ id: 'job-123', status: 'running' }, 200, { 'x-request-id': requestId, 'x-aisa-request-id': 'not-a-documented-header' })]);
    assert.deepEqual((await f.client.getVideoJob('job-123')).receipt, { customerCostMicrosUsd: null });
  }
  const f = fake([json({ id: 'job-123', status: 'running' }, 200, { 'x-request-id': 'unsafe id', 'request-id': 'safe-fallback' })]);
  assert.equal((await f.client.getVideoJob('job-123')).receipt.requestId, 'safe-fallback');
});

test('video submission and each poll retain their own receipt without overwriting earlier costs', async () => {
  const f = fake([
    json(models),
    json({ task_id: 'job-123', status: 'queued' }, 200, { 'X-AISA-Customer-Cost-Micros-USD': '100', 'x-request-id': 'submit' }),
    json({ id: 'job-123', status: 'running' }, 200, { 'X-AISA-Customer-Cost-Micros-USD': '0', 'x-request-id': 'poll-1' }),
    json({ id: 'job-123', status: 'succeeded', content: { video_url: 'https://assets.example/out.mp4' } }, 200, { 'x-request-id': 'poll-2' }),
  ]);
  const submitted = await f.client.submitVideo({ model: videoModel.id, prompt: 'x', referenceUrls: ['https://images.example/product.png'] });
  const running = await f.client.getVideoJob('job-123');
  const completed = await f.client.getVideoJob('job-123');
  assert.deepEqual([submitted.receipt, running.receipt, completed.receipt], [
    { customerCostMicrosUsd: 100, requestId: 'submit' },
    { customerCostMicrosUsd: 0, requestId: 'poll-1' },
    { customerCostMicrosUsd: null, requestId: 'poll-2' },
  ]);
});

test('HTTP and response-validation failures preserve the response receipt', async () => {
  const headers = { 'X-AISA-Customer-Cost-Micros-USD': '900', 'x-request-id': 'failed-paid-request' };
  const receipt = { customerCostMicrosUsd: 900, requestId: 'failed-paid-request' };
  for (const response of [
    json({ error: { message: 'never-print-provider-body' } }, 502, headers),
    json({ success: false }, 200, headers),
    new Response('invalid JSON', { headers: { 'Content-Type': 'application/json', ...headers } }),
    new Response('invalid content type', { headers: { 'Content-Type': 'text/html', ...headers } }),
    json({ choices: [{ finish_reason: 'length', message: { content: 'Truncated' } }] }, 200, headers),
    json({ choices: [{}] }, 200, headers),
  ]) {
    const f = fake([json(models), response]);
    await assert.rejects(f.client.copy({ model: textModel.id, system: 'Facts only', prompt: 'Write' }), error => {
      assert.ok(error instanceof AisaError);
      assert.deepEqual(error.receipt, receipt);
      assert.doesNotMatch(error.message, /never-print-provider-body/);
      return true;
    });
    assert.equal(f.calls.length, 2);
  }
});

test('invalid image and video outputs retain their paid receipt and recoverable task ID', async () => {
  const headers = { 'X-AISA-Customer-Cost-Micros-USD': '500', 'request-id': 'invalid-output' };
  const receipt = { customerCostMicrosUsd: 500, requestId: 'invalid-output' };
  const f = fake([json(models), json({ candidates: [{ content: { parts: [{ text: 'No image' }] } }] }, 200, headers)]);
  await assert.rejects(f.client.generateImages({ model: imageModel.id, prompt: 'x', references: [reference] }), { code: 'no_images', receipt });
  const video = fake([json(models), json({ task_id: 'job-keep-me', status: 'unknown' }, 200, headers)]);
  await assert.rejects(video.client.submitVideo({ model: videoModel.id, prompt: 'x', referenceUrls: ['https://images.example/product.png'] }), { code: 'unknown_job_status', taskId: 'job-keep-me', ambiguous: true, receipt });
  const poll = fake([json({ id: 'job-123', status: 'succeeded' }, 200, headers)]);
  await assert.rejects(poll.client.getVideoJob('job-123'), { code: 'missing_video', receipt });
});

test('a network failure before response headers has no settled-cost receipt', async () => {
  const f = fake([json(models), new Error('transport failed')]);
  await assert.rejects(f.client.copy({ model: textModel.id, system: 'Facts only', prompt: 'Write' }), error => {
    assert.equal(error.receipt, undefined);
    assert.equal(error.ambiguous, true);
    return true;
  });
});
