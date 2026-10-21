import test from 'node:test';
import assert from 'node:assert/strict';
import { AisaClient, AisaError, validateImageConfiguration } from '../dist/aisa.js';

// Adapter-contract tests only. All responses and catalog entries are fixtures;
// this suite never contacts AIsa and does not establish live generation support.
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5M8AAAAASUVORK5CYII=', 'base64');
const reference = { data: png, mimeType: 'image/png' };
const key = 'fixture-private-key-never-in-errors';
const model = { id: 'gpt-image-2', aisa: { model_type: 'image', routes: [{ method: 'POST', path: '/v1/images/edits' }] } };
const json = (value, status = 200, headers = {}) => new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json', ...headers } });
const output = () => json({ data: [{ b64_json: png.toString('base64') }] });
const input = (patch = {}) => ({ model: model.id, prompt: 'Keep the supplied product and label unchanged.', references: [reference], aspectRatio: '1:1', imageSize: '1K', ...patch });
function fake(responses) {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options, body: options.body ? JSON.parse(options.body) : undefined });
    if (!responses.length) throw new Error('Unexpected network attempt in offline test');
    const response = responses.shift();
    if (response instanceof Error) throw response;
    return response;
  };
  return { calls, client: new AisaClient({ apiKey: key, fetch }) };
}
const posts = f => f.calls.filter(call => call.options.method === 'POST');

test('GPT Image edits send actual reference bytes to the explicit catalog-supported edit route', async () => {
  const f = fake([json({ data: [model] }), output()]);
  const result = await f.client.generateImages(input({ references: [reference, { data: new Uint8Array(png), mimeType: 'image/png' }] }));
  assert.equal(f.calls.length, 2);
  assert.equal(f.calls[0].url, 'https://api.aisa.one/v1/models');
  const request = posts(f)[0];
  assert.equal(request.url, 'https://api.aisa.one/v1/images/edits');
  assert.deepEqual(request.body, {
    model: model.id,
    prompt: input().prompt,
    images: [{ image_url: `data:image/png;base64,${png.toString('base64')}` }, { image_url: `data:image/png;base64,${png.toString('base64')}` }],
    n: 1, size: '1024x1024', quality: 'medium', output_format: 'png', stream: false,
  });
  for (const image of request.body.images) assert.deepEqual(Buffer.from(image.image_url.split(',')[1], 'base64'), png);
  assert.equal(request.options.redirect, 'error');
  assert.equal(request.options.headers.Authorization, `Bearer ${key}`);
  assert.equal(request.options.headers['Content-Type'], 'application/json');
  assert.doesNotMatch(request.url + JSON.stringify(request.body), /fixture-private-key/);
  assert.equal(result.images.length, 1);
  assert.equal(result.images[0].mimeType, 'image/png');
  assert.deepEqual(Buffer.from(result.images[0].data), png);
});

test('GPT Image edit parsing retains every inline result and its revised-prompt text', async () => {
  const f = fake([json({ data: [model] }), json({ data: [
    { b64_json: png.toString('base64'), revised_prompt: 'First provider revision.' },
    { b64_json: png.toString('base64'), revised_prompt: 'Second provider revision.' },
  ] }, 200, { 'X-AISA-Customer-Cost-Micros-USD': '42000', 'x-request-id': 'edit-request' })]);
  const result = await f.client.generateImages(input());
  assert.equal(result.images.length, 2);
  for (const image of result.images) assert.deepEqual(Buffer.from(image.data), png);
  assert.match(result.text, /First provider revision/);
  assert.match(result.text, /Second provider revision/);
  assert.deepEqual(result.receipt, { customerCostMicrosUsd: 42000, requestId: 'edit-request' });
});

test('GPT Image edit needs the requested model, image type and POST edit route in the live catalog', async () => {
  const catalogs = [
    [],
    [{ ...model, id: 'another-image-model' }],
    [{ ...model, aisa: { ...model.aisa, model_type: 'text' } }],
    [{ ...model, aisa: { routes: model.aisa.routes } }],
    [{ ...model, aisa: { model_type: 'image', routes: [{ method: 'POST', path: '/v1/images/generations' }] } }],
    [{ ...model, aisa: { model_type: 'image', routes: [{ method: 'POST', path: '/v1beta/models/{model}:generateContent' }] } }],
    [{ ...model, aisa: { model_type: 'image', routes: [{ method: 'GET', path: '/v1/images/edits' }] } }],
  ];
  for (const data of catalogs) {
    const f = fake([json({ data })]);
    await assert.rejects(f.client.generateImages(input()), { code: 'unsupported_model' });
    assert.equal(f.calls.length, 1);
    assert.equal(posts(f).length, 0, 'No paid submission or alternate-provider fallback is permitted');
  }
});

test('supported native GPT Image size mappings remain separate from downstream export dimensions', async () => {
  for (const [imageSize, aspectRatio, expected] of [
    ['1K', '1:1', '1024x1024'], ['1K', '3:2', '1536x1024'],
    ['1K', '2:3', '1024x1536'], ['2K', '1:1', '2048x2048'],
  ]) {
    assert.equal(validateImageConfiguration(model.id, aspectRatio, imageSize), expected);
    const f = fake([json({ data: [model] }), output()]);
    await f.client.generateImages(input({ imageSize, aspectRatio }));
    assert.equal(posts(f).length, 1);
    assert.equal(posts(f)[0].body.size, expected);
  }
});

test('image configuration preflight applies defaults and supported GPT aliases without network calls', () => {
  for (const id of ['gpt-image-2', 'gpt-image-2-2026-04-21', 'gpt-image-2.5-flare', 'gpt-image-2.5-sunburst-2026-10-01']) {
    assert.equal(validateImageConfiguration(id), '1024x1024');
    assert.equal(validateImageConfiguration(id, '1:1', '2K'), '2048x2048');
    assert.throws(() => validateImageConfiguration(id, '16:9', '1K'), { code: 'invalid_input' });
  }
  for (const id of ['catalog-image', 'gemini-3.1-flash-image-preview']) {
    assert.equal(validateImageConfiguration(id), undefined);
    assert.equal(validateImageConfiguration(id, '16:9', '4K'), undefined);
    assert.throws(() => validateImageConfiguration(id, '7:3', '1K'), { code: 'invalid_input' });
    assert.throws(() => validateImageConfiguration(id, '1:1', '8K'), { code: 'invalid_input' });
  }
});

test('unsupported GPT Image native sizes and excessive references fail before any paid POST', async () => {
  for (const patch of [
    { imageSize: '512' }, { imageSize: '4K' }, { imageSize: '2K', aspectRatio: '3:2' },
    { imageSize: '1K', aspectRatio: '16:9' }, { imageSize: '1K', aspectRatio: '9:16' },
    { imageSize: '1K', aspectRatio: '4:5' }, { references: Array(17).fill(reference) },
  ]) {
    const f = fake([json({ data: [model] })]);
    await assert.rejects(f.client.generateImages(input(patch)), { code: 'invalid_input' });
    assert.equal(posts(f).length, 0);
    assert.equal(f.calls.length, 0, 'Adapter settings must fail before catalog lookup');
  }
});

test('URL-only, corrupt, empty and mixed invalid edit outputs are never accepted or silently downloaded', async () => {
  const invalid = [
    { data: [{ url: 'https://signed.example/output.png?secret=fixture-secret' }] },
    { data: [{ b64_json: '!!!!' }] },
    { data: [{ b64_json: Buffer.from('<html>not an image</html>').toString('base64') }] },
    { data: [] },
    { text: 'Here is your image.' },
    { data: [{ b64_json: png.toString('base64') }, { url: 'https://signed.example/other.png?secret=fixture-secret' }] },
  ];
  for (const response of invalid) {
    const f = fake([json({ data: [model] }), json(response, 200, { 'X-AISA-Customer-Cost-Micros-USD': '40000', 'request-id': 'invalid-edit' })]);
    await assert.rejects(f.client.generateImages(input()), error => {
      assert.ok(error instanceof AisaError);
      assert.ok(['invalid_media', 'no_images'].includes(error.code));
      assert.deepEqual(error.receipt, { customerCostMicrosUsd: 40000, requestId: 'invalid-edit' });
      assert.doesNotMatch(error.message, /signed\.example|fixture-secret|not an image/);
      return true;
    });
    assert.equal(f.calls.length, 2, 'Only catalog lookup and one POST; no URL fetch or retry');
  }
});

test('GPT Image POST errors redact echoed credentials and signed URLs without retry or fallback', async () => {
  for (const status of [401, 429, 502]) {
    const f = fake([json({ data: [model] }), json({ error: { message: `${key} https://signed.example/?secret=fixture-secret` } }, status)]);
    await assert.rejects(f.client.generateImages(input()), error => {
      assert.ok(error instanceof AisaError);
      assert.equal(error.httpStatus, status);
      assert.equal(error.ambiguous, status >= 500);
      assert.doesNotMatch(error.message, /fixture-private-key|signed\.example|fixture-secret/);
      return true;
    });
    assert.equal(posts(f).length, 1);
    assert.equal(f.calls.length, 2);
  }
});

test('GPT Image network failure remains ambiguous and never triggers another submission', async () => {
  const f = fake([json({ data: [model] }), new Error(`${key} https://signed.example/?secret=fixture-secret`)]);
  await assert.rejects(f.client.generateImages(input()), error => {
    assert.equal(error.code, 'network_error');
    assert.equal(error.ambiguous, true);
    assert.doesNotMatch(error.message, /fixture-private-key|signed\.example|fixture-secret/);
    return true;
  });
  assert.equal(posts(f).length, 1);
  assert.equal(f.calls.length, 2);
});
