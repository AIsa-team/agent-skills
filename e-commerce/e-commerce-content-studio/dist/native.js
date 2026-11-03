import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { cacheResponse, loadLedger, materialize, productionPrompt, recordReceipt, resolveDeliverable, safeId, saveLedger, validateCopy, verifyReferences } from './production.js';
import { approvalHash, assertReady } from './workflow.js';
import { atomicJson, downloadBytes, sha256 } from './media.js';
import { assertSchema, digestJson, getPointer, noCredentials, nonempty, recent, record, setPointer, transportOf, validateNativePlan } from './native-contract.js';
function nativeTransport(state) {
    const value = transportOf(state);
    if (value === 'rest')
        throw new Error('This project selected REST compatibility. Native MCP/CLI execution requires a separate project; do not switch transports during a job.');
    return value;
}
export async function importConnection(directory, state, value) {
    const connection = record(value, 'connection receipt');
    noCredentials(connection);
    if (connection.transport !== nativeTransport(state) || connection.server !== 'https://mcp.aisa.one/mcp' || connection.connected !== true)
        throw new Error('Require a successful AIsa connection check using the selected host MCP/official CLI connection.');
    nonempty(connection.receiptId, 'connection.receiptId');
    recent(connection.checkedAt, 'connection.checkedAt');
    await atomicJson(join(directory, 'connection.json'), connection);
    return connection;
}
async function connectionFor(directory, state, receiptId) {
    let value;
    try {
        value = JSON.parse(await readFile(join(directory, 'connection.json'), 'utf8'));
    }
    catch {
        throw new Error('Connect AIsa at https://mcp.aisa.one/mcp in your host, or configure the official AIsa CLI for a CLI project, then import a successful connection check. No API key is needed by this runtime.');
    }
    if (value.transport !== nativeTransport(state) || value.server !== 'https://mcp.aisa.one/mcp' || value.connected !== true || (receiptId && value.receiptId !== receiptId))
        throw new Error('Connection receipt does not match this project and request.');
    recent(value.checkedAt, 'connection.checkedAt');
    noCredentials(value);
    return value;
}
function requestPlan(state, id, requireFresh = false) {
    nativeTransport(state);
    const deliverable = resolveDeliverable(state, id, requireFresh);
    if (['local-photo-export', 'host-copy'].includes(deliverable.model))
        throw new Error('Use the local preserve-photo or import-host-copy workflow for this approved deliverable.');
    return { deliverable, plan: validateNativePlan(deliverable.nativeRequest, deliverable, requireFresh) };
}
function currentJob(ledger, state, id) {
    const job = ledger.jobs.find(job => job.id === safeId(id));
    if (!job?.native || job.transport !== nativeTransport(state) || job.approvalHash !== approvalHash(state))
        throw new Error('No native job matches this project transport and approved playbook.');
    return job;
}
async function buildArguments(state, deliverable, plan, job) {
    if (job) {
        if (!job.taskId || !plan.poll)
            throw new Error('Polling requires the saved provider task ID and an approved discovered status operation.');
        const args = structuredClone(plan.poll.argumentsTemplate);
        setPointer(args, plan.poll.taskIdPointer, job.taskId);
        assertSchema(args, plan.poll.argumentsSchema, 'Polling arguments');
        return { tool: plan.poll.tool, arguments: args, action: 'poll' };
    }
    const args = structuredClone(plan.argumentsTemplate);
    setPointer(args, plan.modelPointer, deliverable.model);
    setPointer(args, plan.promptPointer, productionPrompt(state, deliverable));
    for (const binding of plan.referenceBindings) {
        const ref = state.references.find(reference => reference.id === binding.referenceId);
        let value;
        if (binding.encoding === 'data-uri')
            value = `data:${ref.mimeType};base64,${(await readFile(ref.path)).toString('base64')}`;
        else {
            if (!ref.remoteUrl)
                throw new Error(`Reference ${ref.id} needs a user-supplied public HTTPS URL for the same photo; this runtime does not upload product photos.`);
            if (sha256(await downloadBytes(ref.remoteUrl, 50 * 1024 * 1024)) !== ref.sha256)
                throw new Error(`Remote reference ${ref.id} differs from the approved product photo.`);
            value = ref.remoteUrl;
        }
        setPointer(args, binding.pointer, value);
    }
    assertSchema(args, plan.argumentsSchema, 'Generation arguments');
    return { tool: plan.tool, arguments: args, action: 'generate' };
}
export async function buildNativeRequest(directory, state, id, jobId) {
    const { deliverable, plan } = requestPlan(state, id, !jobId);
    await connectionFor(directory, state);
    await verifyReferences(state);
    const ledger = await loadLedger(directory);
    const job = jobId ? currentJob(ledger, state, jobId) : undefined;
    if (job && job.deliverableId !== id)
        throw new Error('Saved task belongs to another deliverable.');
    const request = await buildArguments(state, deliverable, plan, job);
    const path = join(directory, 'handoffs', `${safeId(id)}-${request.action}.json`);
    await atomicJson(path, { ...request, argumentsHash: digestJson(request.arguments), approvalHash: approvalHash(state) });
    return { path, tool: request.tool, argumentsHash: digestJson(request.arguments), action: request.action };
}
function validatePreparation(value) {
    const input = record(value, 'native preparation');
    noCredentials(input);
    nonempty(input.sessionId, 'sessionId');
    nonempty(input.connectionReceiptId, 'connectionReceiptId');
    if (input.searchId !== undefined)
        nonempty(input.searchId, 'searchId');
    const quote = record(input.quote, 'quote');
    for (const field of ['requestId', 'tool', 'sessionId', 'argumentsHash'])
        nonempty(quote[field], `quote.${field}`);
    if (!/^[a-f0-9]{64}$/.test(quote.argumentsHash))
        throw new Error('quote.argumentsHash must be the canonical SHA-256 of the exact quoted arguments.');
    if (quote.currency !== 'USD' || !Number.isFinite(quote.estimatedCostUsd) || quote.estimatedCostUsd < 0)
        throw new Error('Record a successful USD quote with a finite nonnegative cost.');
    if (!['exact', 'estimate', 'upper_bound'].includes(quote.estimateKind) || typeof quote.mayExceedEstimate !== 'boolean')
        throw new Error('Quote must preserve estimateKind and mayExceedEstimate.');
    record(quote.source, 'quote.source (original provider quote excerpt)');
    if (!Object.keys(quote.source).length)
        throw new Error('Keep the original non-secret provider quote excerpt.');
    if (quote.maxCostUsd !== null && (!Number.isFinite(quote.maxCostUsd) || quote.maxCostUsd < quote.estimatedCostUsd))
        throw new Error('Quote maxCostUsd must be null or a finite ceiling at least equal to the estimate.');
    if (quote.estimateKind === 'upper_bound' && quote.maxCostUsd === null)
        throw new Error('An upper-bound quote requires its maximum cost.');
    if (quote.mayExceedEstimate !== (quote.estimateKind === 'estimate'))
        throw new Error('Quote mayExceedEstimate must preserve the provider estimate semantics.');
    if (quote.estimateKind === 'exact' && quote.maxCostUsd !== quote.estimatedCostUsd)
        throw new Error('An exact quote must preserve its exact maximum cost.');
    recent(quote.quotedAt, 'quote.quotedAt', 1);
    return input;
}
function quoteMatches(input, request) {
    if (input.quote.sessionId !== input.sessionId || input.quote.tool !== request.tool || input.quote.argumentsHash !== digestJson(request.arguments))
        throw new Error('Quote must match the exact model, arguments, operation and session. Quote the complete saved arguments object without reserializing its body.');
}
async function storeOperation(directory, state, job, input, request) {
    const operation = {
        id: randomUUID(), action: request.action, tool: request.tool, sessionId: input.sessionId, ...(input.searchId ? { searchId: input.searchId } : {}),
        argumentsHash: digestJson(request.arguments), requestPath: '', connectionReceiptId: input.connectionReceiptId,
        quote: structuredClone(input.quote), status: 'prepared',
    };
    operation.requestPath = join(directory, 'jobs', job.id, `${operation.id}-request.json`);
    await atomicJson(operation.requestPath, { transport: nativeTransport(state), server: 'https://mcp.aisa.one/mcp', operationId: operation.id, session_id: input.sessionId, ...(input.searchId ? { search_id: input.searchId } : {}), calls: [{ tool: request.tool, call_id: operation.id, arguments: request.arguments }] });
    job.native.operations.push(operation);
    return operation;
}
export async function prepareNative(directory, state, value) {
    const input = validatePreparation(value);
    const { deliverable, plan } = requestPlan(state, nonempty(input.deliverableId, 'deliverableId'), true);
    await connectionFor(directory, state, input.connectionReceiptId);
    await verifyReferences(state);
    const request = await buildArguments(state, deliverable, plan);
    quoteMatches(input, request);
    if ((input.quote.estimateKind === 'upper_bound' ? input.quote.maxCostUsd : input.quote.estimatedCostUsd) > deliverable.estimatedCostUsd + 1e-8)
        throw new Error('Current quote exceeds the approved per-attempt estimate. Update the playbook and obtain user approval.');
    const ledger = await loadLedger(directory);
    const prior = ledger.jobs.filter(job => job.deliverableId === deliverable.id && job.status !== 'cancelled');
    if (prior.some(job => (job.transport ?? 'rest') !== nativeTransport(state)))
        throw new Error('This deliverable already used another transport; create a separate project instead of switching.');
    if (prior.length && !input.retry)
        throw new Error('This deliverable already has a job. Resume or reconcile it instead of submitting again.');
    if (prior.some(job => !['failed', 'rejected'].includes(job.status)))
        throw new Error('An existing submission needs reconciliation or review; never retry an uncertain task.');
    if (input.retry && !prior.length)
        throw new Error('Retry requires a confirmed failed or rejected job.');
    if (prior.some(job => job.native?.authFailureConnectionReceiptId === input.connectionReceiptId))
        throw new Error('A prior 401 requires a fresh successful host connection check before retrying; do not infer missing service authorization or switch transports.');
    if (prior.length >= state.playbook.budget.maxAttemptsPerDeliverable)
        throw new Error('Approved attempt limit reached.');
    if (ledger.jobs.reduce((sum, job) => sum + job.estimatedCostUsd, 0) + deliverable.estimatedCostUsd > state.brief.budget.maxEstimatedCostUsd + 1e-8)
        throw new Error('This attempt exceeds the approved project estimate allowance.');
    const job = { id: randomUUID(), deliverableId: deliverable.id, transport: nativeTransport(state), approvalHash: approvalHash(state), model: deliverable.model, status: 'prepared', estimatedCostUsd: deliverable.estimatedCostUsd, createdAt: new Date().toISOString(), artifacts: [], native: { operations: [] } };
    const operation = await storeOperation(directory, state, job, input, request);
    ledger.jobs.push(job);
    await saveLedger(directory, ledger);
    return { job, operation };
}
export async function prepareNativePoll(directory, state, jobId, value) {
    const input = validatePreparation(value);
    const ledger = await loadLedger(directory);
    const job = currentJob(ledger, state, jobId);
    const { deliverable, plan } = requestPlan(state, job.deliverableId);
    await connectionFor(directory, state, input.connectionReceiptId);
    await verifyReferences(state);
    if (job.native.authFailureConnectionReceiptId === input.connectionReceiptId)
        throw new Error('A prior 401 requires a fresh successful host connection check before polling the saved task.');
    if (!['submitted', 'download-pending', 'uncertain'].includes(job.status) || !job.taskId)
        throw new Error('Only a saved pending task or its expired download may be polled.');
    if (job.native.operations.some(operation => operation.action === 'poll' && ['prepared', 'dispatched'].includes(operation.status)))
        throw new Error('Resolve the existing poll operation first.');
    const request = await buildArguments(state, deliverable, plan, job);
    quoteMatches(input, request);
    if (input.quote.estimatedCostUsd !== 0)
        throw new Error('This runtime only dispatches zero-cost status polls. A paid status operation requires a separately approved workflow.');
    const operation = await storeOperation(directory, state, job, input, request);
    await saveLedger(directory, ledger);
    return { job, operation };
}
function findOperation(ledger, state, id) {
    safeId(id);
    const job = ledger.jobs.find(job => job.native?.operations.some(operation => operation.id === id));
    if (!job)
        throw new Error('Unknown native operation.');
    currentJob(ledger, state, job.id);
    return { job, operation: job.native.operations.find(operation => operation.id === id) };
}
export async function markNativeDispatched(directory, state, id) {
    await verifyReferences(state);
    const ledger = await loadLedger(directory);
    const { job, operation } = findOperation(ledger, state, id);
    if (operation.action === 'generate')
        assertReady(state);
    if (operation.status !== 'prepared')
        throw new Error('Operation was already dispatched or reconciled. Do not submit it again.');
    await connectionFor(directory, state, operation.connectionReceiptId);
    recent(operation.quote.quotedAt, 'quote.quotedAt', 1);
    const request = JSON.parse(await readFile(operation.requestPath, 'utf8'));
    const expectedEnvelope = { transport: nativeTransport(state), server: 'https://mcp.aisa.one/mcp', operationId: operation.id, session_id: operation.sessionId, ...(operation.searchId ? { search_id: operation.searchId } : {}), calls: [{ tool: operation.tool, call_id: operation.id, arguments: request.calls?.[0]?.arguments }] };
    if (digestJson(request) !== digestJson(expectedEnvelope) || digestJson(request.calls?.[0]?.arguments) !== operation.argumentsHash)
        throw new Error('Prepared request envelope or arguments changed after its quote.');
    const { deliverable, plan } = requestPlan(state, job.deliverableId, operation.action === 'generate');
    const expected = await buildArguments(state, deliverable, plan, operation.action === 'poll' ? job : undefined);
    if (digestJson(expected.arguments) !== operation.argumentsHash)
        throw new Error('Prepared request no longer matches the approved template/photos.');
    operation.status = 'dispatched';
    if (operation.action === 'generate')
        job.status = 'uncertain';
    await saveLedger(directory, ledger);
    return operation;
}
function tryPointer(value, pointer) {
    if (pointer === undefined)
        return undefined;
    try {
        return getPointer(value, pointer);
    }
    catch {
        return undefined;
    }
}
function normalize(data, plan, deliverable) {
    assertSchema(data, plan.responseSchema, 'Provider response');
    if (deliverable.kind === 'copy')
        return { response: { text: nonempty(getPointer(data, plan.result.textPointer), 'copy response text') }, status: 'download-pending' };
    if (deliverable.kind === 'image') {
        const mapping = plan.result.images;
        const images = getPointer(data, mapping.pointer);
        if (!Array.isArray(images) || !images.length)
            throw new Error('Successful image response has no candidates.');
        return { response: { images: images.map(image => {
                    const base64 = tryPointer(image, mapping.base64Pointer);
                    const url = tryPointer(image, mapping.urlPointer);
                    if (typeof base64 === 'string' && base64)
                        return { base64 };
                    if (typeof url === 'string' && url)
                        return { url };
                    throw new Error('Image candidate lacks a mapped URL/base64 payload.');
                }) }, status: 'download-pending' };
    }
    const mapping = plan.result.task;
    const taskId = nonempty(getPointer(data, mapping.idPointer), 'provider task ID');
    safeId(taskId);
    const status = nonempty(getPointer(data, mapping.statusPointer), 'provider task status');
    if (mapping.pending.includes(status))
        return { taskId, status: 'submitted' };
    if (mapping.failed.includes(status))
        return { taskId, status: 'failed' };
    if (!mapping.succeeded.includes(status))
        return { taskId, status: 'submitted' };
    const output = getPointer(data, mapping.urlsPointer);
    const urls = typeof output === 'string' ? [output] : output;
    if (!Array.isArray(urls) || !urls.length || urls.some(url => typeof url !== 'string' || !url))
        throw new Error('Completed video task has no mapped output URLs.');
    return { taskId, status: 'download-pending', response: { urls } };
}
export async function ingestNativeResult(directory, state, id, value) {
    const input = record(value, 'native result');
    noCredentials(input);
    const ledger = await loadLedger(directory);
    const { job, operation } = findOperation(ledger, state, id);
    if (operation.status !== 'dispatched')
        throw new Error('Only a dispatched operation may receive a result.');
    if (input.tool !== operation.tool || input.sessionId !== operation.sessionId || input.argumentsHash !== operation.argumentsHash)
        throw new Error('Result receipt belongs to another operation, session or argument set.');
    nonempty(input.requestId, 'requestId');
    if (!['success', 'failed', 'unknown'].includes(input.outcome))
        throw new Error('Result outcome must be success, failed or unknown.');
    if (input.customerCostMicrosUsd !== undefined && input.customerCostMicrosUsd !== null && (!Number.isSafeInteger(input.customerCostMicrosUsd) || input.customerCostMicrosUsd < 0))
        throw new Error('Settled cost must be unknown or nonnegative integer micro-USD.');
    operation.requestId = input.requestId;
    operation.resultPath = join(directory, 'jobs', job.id, `${operation.id}-result-${randomUUID()}.json`);
    // Keep raw evidence before interpretation; a malformed successful response must never allow another submission.
    await atomicJson(operation.resultPath, input);
    if (operation.action === 'poll')
        operation.status = 'received';
    const previousReceipt = job.receipts?.find(receipt => receipt.requestId === input.requestId);
    if (previousReceipt?.customerCostMicrosUsd != null && input.customerCostMicrosUsd != null && previousReceipt.customerCostMicrosUsd !== input.customerCostMicrosUsd) {
        job.error = 'Conflicting settled costs for the same provider request ID. Original and new raw receipts are retained; reconcile billing before accepting the new receipt.';
        await saveLedger(directory, ledger);
        throw new Error(job.error);
    }
    recordReceipt(job, { requestId: input.requestId, customerCostMicrosUsd: input.customerCostMicrosUsd ?? null });
    const { deliverable, plan } = requestPlan(state, job.deliverableId);
    const operationPlan = operation.action === 'poll' ? plan.poll : plan;
    try {
        if (input.taskId) {
            safeId(input.taskId);
            if (job.taskId && job.taskId !== input.taskId)
                throw new Error('Response references a different provider task.');
            job.taskId = input.taskId;
            job.status = 'submitted';
            await saveLedger(directory, ledger);
        }
        if (input.outcome !== 'success') {
            operation.status = input.outcome === 'unknown' && operation.action === 'generate' ? 'dispatched' : 'received';
            job.error = input.error ?? `Host reported ${input.outcome}.`;
            if (operation.action === 'generate')
                job.status = job.taskId ? 'submitted' : input.outcome === 'failed' ? 'failed' : 'uncertain';
            if (input.statusCode === 401)
                job.native.authFailureConnectionReceiptId = operation.connectionReceiptId;
            await saveLedger(directory, ledger);
            return job;
        }
        // Persist a known task identity before validating the rest of a response or saving its media.
        const knownId = operationPlan.result.task ? tryPointer(input.data, operationPlan.result.task.idPointer) : undefined;
        if (typeof knownId === 'string' && knownId) {
            safeId(knownId);
            if (job.taskId && job.taskId !== knownId)
                throw new Error('Provider returned a different task ID.');
            job.taskId = knownId;
            job.status = 'submitted';
            await saveLedger(directory, ledger);
        }
        const result = normalize(input.data, operationPlan, deliverable);
        operation.status = 'received';
        if (result.taskId)
            job.taskId = result.taskId;
        job.status = result.status;
        await saveLedger(directory, ledger);
        if (result.response !== undefined) {
            await cacheResponse(directory, ledger, job, result.response);
            await materialize(directory, state, deliverable, job);
        }
        if (job.status === 'failed')
            job.error = 'Provider confirmed the saved task failed.';
        await saveLedger(directory, ledger);
        return job;
    }
    catch (error) {
        job.error = error instanceof Error ? error.message : 'Native result processing failed.';
        await saveLedger(directory, ledger);
        throw new Error(`${job.error} Saved native job ${job.id}; reconcile or resume it without regeneration.`);
    }
}
export async function resumeNative(directory, state, id) {
    nativeTransport(state);
    const deliverable = resolveDeliverable(state, id, false);
    await verifyReferences(state);
    const ledger = await loadLedger(directory);
    const latest = ledger.jobs.filter(job => job.deliverableId === id).at(-1);
    if (!latest)
        throw new Error('No saved job exists.');
    const job = currentJob(ledger, state, latest.id);
    if (['needs-review', 'approved'].includes(job.status))
        return job;
    if (job.status !== 'download-pending')
        throw new Error(`Job is ${job.status}. Use the saved task and prepare-native-poll, or reconcile its original operation; no new generation will be sent.`);
    try {
        await materialize(directory, state, deliverable, job);
        await saveLedger(directory, ledger);
        return job;
    }
    catch (error) {
        await saveLedger(directory, ledger);
        throw error;
    }
}
export async function importHostCopy(directory, state, id, value) {
    nativeTransport(state);
    const deliverable = resolveDeliverable(state, id);
    await verifyReferences(state);
    if (deliverable.kind !== 'copy' || deliverable.model !== 'host-copy')
        throw new Error('Host-written copy must be explicitly approved as model host-copy before import.');
    const input = record(value, 'host copy');
    noCredentials(input);
    if (input.producedBy !== 'host')
        throw new Error('Record producedBy: host for host-written copy.');
    nonempty(input.note, 'host copy note');
    const text = nonempty(input.text, 'host copy text');
    validateCopy(text, deliverable);
    const ledger = await loadLedger(directory);
    if (ledger.jobs.some(job => job.deliverableId === id))
        throw new Error('This deliverable already has a job; do not overwrite it.');
    const job = { id: randomUUID(), deliverableId: id, transport: nativeTransport(state), native: { operations: [] }, approvalHash: approvalHash(state), model: 'host-copy', status: 'download-pending', estimatedCostUsd: 0, createdAt: new Date().toISOString(), artifacts: [] };
    ledger.jobs.push(job);
    await saveLedger(directory, ledger);
    try {
        await cacheResponse(directory, ledger, job, { text, producedBy: 'host', note: input.note });
        await materialize(directory, state, deliverable, job);
    }
    finally {
        await saveLedger(directory, ledger);
    }
    return job;
}
export async function cancelNativePrepared(directory, state, id) {
    const ledger = await loadLedger(directory);
    const { job, operation } = findOperation(ledger, state, id);
    if (operation.status !== 'prepared')
        throw new Error('Only a never-dispatched prepared operation can be cancelled. Reconcile dispatched or uncertain operations instead.');
    operation.status = 'cancelled';
    if (operation.action === 'generate') {
        job.status = 'cancelled';
        job.estimatedCostUsd = 0;
    }
    await saveLedger(directory, ledger);
    return job;
}
