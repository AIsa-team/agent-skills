import { createHash } from 'node:crypto';
import { Ajv } from 'ajv';
import { Ajv2020 } from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
export const transportOf = (state) => state.transport ?? 'rest';
export function canonical(value) {
    if (Array.isArray(value))
        return `[${value.map(canonical).join(',')}]`;
    if (value && typeof value === 'object')
        return `{${Object.entries(value).filter(([, v]) => v !== undefined).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => `${JSON.stringify(k)}:${canonical(v)}`).join(',')}}`;
    return JSON.stringify(value);
}
export const digestJson = (value) => createHash('sha256').update(canonical(value)).digest('hex');
export function record(value, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value))
        throw new Error(`${label} must be an object.`);
    return value;
}
export function nonempty(value, label) {
    if (typeof value !== 'string' || !value.trim())
        throw new Error(`${label} must be a nonempty string.`);
    return value;
}
export function recent(value, label, maxHours = 24) {
    const age = Date.now() - Date.parse(value);
    if (!Number.isFinite(age) || age < -60_000 || age > maxHours * 3_600_000)
        throw new Error(`${label} is stale or invalid; refresh discovery/connection through the selected host connection.`);
}
export function noCredentials(value, at = 'native data') {
    if (typeof value === 'string' && (/\b(?:sk-aisa-|Bearer\s+)/i.test(value)))
        throw new Error(`${at} must not contain API keys or bearer credentials.`);
    if (!value || typeof value !== 'object')
        return;
    for (const [key, item] of Object.entries(value)) {
        if (/^(?:authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)$/i.test(key))
            throw new Error(`${at} must not contain credentials; the host owns authentication.`);
        noCredentials(item, `${at}.${key}`);
    }
}
function tokens(pointer) {
    if (typeof pointer !== 'string' || (pointer !== '' && !pointer.startsWith('/')) || /~(?![01])/u.test(pointer))
        throw new Error('Binding must use a valid JSON pointer.');
    const parts = pointer === '' ? [] : pointer.slice(1).split('/').map(part => part.replaceAll('~1', '/').replaceAll('~0', '~'));
    if (parts.some(part => ['__proto__', 'constructor', 'prototype'].includes(part)))
        throw new Error('Unsafe JSON pointer.');
    return parts;
}
export function getPointer(value, pointer) {
    let current = value;
    for (const part of tokens(pointer)) {
        if (!current || typeof current !== 'object' || !Object.hasOwn(current, part))
            throw new Error(`JSON pointer ${pointer} does not exist.`);
        current = current[part];
    }
    return current;
}
export function setPointer(value, pointer, replacement) {
    const parts = tokens(pointer);
    if (!parts.length)
        throw new Error('Input bindings cannot replace the root object.');
    const target = parts.length === 1 ? value : getPointer(value, '/' + parts.slice(0, -1).map(part => part.replaceAll('~', '~0').replaceAll('/', '~1')).join('/'));
    if (!target || typeof target !== 'object' || !Object.hasOwn(target, parts.at(-1)))
        throw new Error(`Binding ${pointer} must point to an existing placeholder in argumentsTemplate.`);
    target[parts.at(-1)] = replacement;
}
export function assertSchema(value, schema, label) {
    record(schema, `${label} schema`);
    if (schema.type === undefined && !schema.$ref && !schema.anyOf && !schema.oneOf && !schema.allOf)
        throw new Error(`${label} requires a complete JSON Schema, not a discovery summary.`);
    const dialect = schema.$schema;
    if (dialect !== undefined && !['http://json-schema.org/draft-07/schema#', 'https://json-schema.org/draft-07/schema', 'https://json-schema.org/draft/2020-12/schema'].includes(String(dialect)))
        throw new Error('Unsupported schema dialect; obtain a complete draft-07 or 2020-12 schema.');
    const validator = dialect === 'https://json-schema.org/draft/2020-12/schema' ? new Ajv2020({ strict: false, allErrors: true, validateFormats: true }) : new Ajv({ strict: false, allErrors: true, validateFormats: true });
    addFormats.default(validator);
    const validate = validator.compile(schema);
    if (!validate(value))
        throw new Error(`${label} does not match the discovered schema: ${validator.errorsText(validate.errors)}.`);
}
function validateOperation(plan, label) {
    nonempty(plan.tool, `${label}.tool`);
    record(plan.argumentsTemplate, `${label}.argumentsTemplate`);
    record(plan.argumentsSchema, `${label}.argumentsSchema`);
    record(plan.responseSchema, `${label}.responseSchema`);
    record(plan.result, `${label}.result`);
    // Compile both schemas now, but template placeholders are filled only at request creation.
    for (const schema of [plan.argumentsSchema, plan.responseSchema]) {
        try {
            assertSchema(null, schema, label);
        }
        catch (error) {
            if (!(error instanceof Error) || !error.message.startsWith(`${label} does not match`))
                throw error;
        }
    }
}
export function validateNativePlan(value, deliverable, requireFresh = false) {
    const plan = record(value, 'nativeRequest');
    noCredentials(plan);
    validateOperation(plan, 'nativeRequest');
    record(plan.catalog, 'nativeRequest.catalog');
    record(plan.modelContract, 'nativeRequest.modelContract');
    nonempty(plan.catalog.source, 'catalog.source');
    nonempty(plan.modelContract.source, 'modelContract.source');
    if (!Array.isArray(plan.catalog.modelIds) || !plan.catalog.modelIds.every(v => typeof v === 'string') || !plan.catalog.modelIds.includes(deliverable.model))
        throw new Error('Approved model is absent from the discovered AIsa model catalog. Refresh discovery; do not substitute another model.');
    for (const [date, label] of [[plan.catalog.checkedAt, 'catalog.checkedAt'], [plan.modelContract.checkedAt, 'modelContract.checkedAt']]) {
        if (!Number.isFinite(Date.parse(nonempty(date, label))))
            throw new Error(`${label} must be an ISO timestamp.`);
        if (requireFresh)
            recent(date, label);
    }
    if (typeof plan.modelContract.supportsReferences !== 'boolean')
        throw new Error('Record the selected model contract reference support explicitly.');
    const bindingPointers = [plan.modelPointer, plan.promptPointer];
    if (!Array.isArray(plan.referenceBindings))
        throw new Error('nativeRequest.referenceBindings must be an array.');
    for (const binding of plan.referenceBindings) {
        if (!deliverable.referenceIds.includes(binding.referenceId) || !['data-uri', 'https'].includes(binding.encoding))
            throw new Error('Reference binding must use an approved photo and a documented reference encoding.');
        bindingPointers.push(binding.pointer);
    }
    for (const pointer of bindingPointers) {
        nonempty(pointer, 'input pointer');
        getPointer(plan.argumentsTemplate, pointer);
    }
    for (let i = 0; i < bindingPointers.length; i++)
        for (let j = i + 1; j < bindingPointers.length; j++) {
            const a = bindingPointers[i], b = bindingPointers[j];
            if (a === b || a.startsWith(`${b}/`) || b.startsWith(`${a}/`))
                throw new Error('Input bindings must not overlap.');
        }
    if (deliverable.kind !== 'copy' && (!plan.modelContract.supportsReferences || deliverable.referenceIds.some(id => !plan.referenceBindings.some(binding => binding.referenceId === id))))
        throw new Error('This product image/video requires a model operation supporting every approved reference photo. Offer another suitable catalog model or explain the capability gap.');
    if (deliverable.kind === 'image' && !plan.result.images)
        throw new Error('Image operation needs an images response mapping.');
    if (deliverable.kind === 'copy' && plan.result.textPointer === undefined)
        throw new Error('Copy operation needs a text response mapping.');
    if (deliverable.kind === 'video' && !plan.result.task)
        throw new Error('Video operation needs a task response mapping.');
    for (const mapping of [plan.result, ...(plan.poll ? [plan.poll.result] : [])]) {
        if (mapping.images) {
            tokens(mapping.images.pointer);
            if (mapping.images.urlPointer === undefined && mapping.images.base64Pointer === undefined)
                throw new Error('Image result mapping needs urlPointer or base64Pointer.');
            if (mapping.images.urlPointer !== undefined)
                tokens(mapping.images.urlPointer);
            if (mapping.images.base64Pointer !== undefined)
                tokens(mapping.images.base64Pointer);
        }
        if (mapping.textPointer !== undefined)
            tokens(mapping.textPointer);
        if (mapping.task) {
            for (const pointer of [mapping.task.idPointer, mapping.task.statusPointer, mapping.task.urlsPointer])
                tokens(pointer);
            const statuses = ['pending', 'succeeded', 'failed'].map(key => mapping.task[key]);
            if (statuses.some(values => !Array.isArray(values) || !values.length || values.some(value => typeof value !== 'string')))
                throw new Error('Task mapping needs explicit pending/succeeded/failed status values.');
            const flat = statuses.flat();
            if (new Set(flat).size !== flat.length)
                throw new Error('Task result status groups must not overlap.');
        }
    }
    if (plan.poll) {
        validateOperation(plan.poll, 'nativeRequest.poll');
        getPointer(plan.poll.argumentsTemplate, plan.poll.taskIdPointer);
        if (!plan.poll.result.task)
            throw new Error('Polling needs a task result mapping.');
    }
    return structuredClone(plan);
}
