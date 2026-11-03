#!/usr/bin/env node
import { mkdir, open, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { AisaClient } from './aisa.js';
import { PLATFORM_SUPPORT, PLACEMENTS } from './types.js';
import { approvePlaybook, approvalHash, assertReady, initProject, renderPlaybook, renderResearch, setPlaybook, setResearch, validateBrief, validateProject } from './workflow.js';
import { atomicJson, inspectMedia } from './media.js';
import { exportPackage, generate, loadLedger, resume, review, safeId, verifyReferences } from './production.js';
import { buildNativeRequest, cancelNativePrepared, importConnection, importHostCopy, ingestNativeResult, markNativeDispatched, prepareNative, prepareNativePoll, resumeNative } from './native.js';
const help = `E-commerce Content Studio — version 1.1.0

Node.js 22+, ffmpeg and ffprobe are required. Paths may be absolute.
  platforms                                  Current profiles and future roadmap
  init <brief.json> <project-dir> [--transport mcp|cli|rest]
                                             Copy required photos; default connection: MCP
  research-import <project-dir> <research.json>
  playbook-import <project-dir> <playbook.json>
  report <project-dir>                       Write research/playbook reports and hash
  approve <project-dir> <approval.json>       Record the user's exact-version approval
  connection-import <project-dir> <receipt.json>
  build-native-request <project-dir> <deliverable-id> [--job <job-id>]
  prepare-native <project-dir> <request.json>
  mark-native-dispatched <project-dir> <operation-id>
  cancel-native-prepared <project-dir> <operation-id>
  ingest-native-result <project-dir> <operation-id> <result.json>
  prepare-native-poll <project-dir> <job-id> <request.json>
  resume-native <project-dir> <deliverable-id>
  import-host-copy <project-dir> <deliverable-id> <copy.json>
  generate <project-dir> <deliverable-id>     Local photo or explicitly selected REST
  resume <project-dir> <deliverable-id>       Resume through the saved connection
  retry <project-dir> <deliverable-id>        REST/local retry after confirmed failure
  review <project-dir> <review.json>          Record actual inspections of all outputs
  status <project-dir>                       Show approval and generation status
  export <project-dir> <new-destination>      Export only a fully reviewed package
  models [--transport mcp|cli|rest]           Host discovery instructions; explicit REST query

Connect AIsa MCP at https://mcp.aisa.one/mcp through your host and complete browser
authorization. The host checks the account, discovers models and tools, and executes
quoted native requests. No pasted API key is required for MCP. The official AIsa CLI
is an explicit host-managed alternative; this helper does not read its credentials.
Import the source-backed research and proposed playbook; show both to the user before
recording approval. No product photos means stop, including for copy-only requests.
For direct REST compatibility, select --transport rest at init and configure
AISA_API_KEY in the environment. Older projects without a saved transport require
--transport rest on generate/retry/resume before a REST network operation. Connections
cannot be switched within a project. No credential or error triggers a fallback.
Never pass keys as arguments. This tool does not publish listings. REST video requires
a public HTTPS remoteUrl for the same approved photo; native inputs follow live schemas.
Estimates and attempt limits do not enforce a provider billing cap.
`;
const json = async (path) => JSON.parse(await readFile(resolve(path), 'utf8'));
async function project(directory) {
    const state = validateProject(await json(join(directory, 'project.json')));
    await verifyReferences(state);
    return state;
}
async function reports(directory, state) {
    if (state.research)
        await writeFile(join(directory, 'research-report.md'), renderResearch(state));
    if (state.playbook)
        await writeFile(join(directory, 'playbook.md'), renderPlaybook(state));
    else
        await rm(join(directory, 'playbook.md'), { force: true });
}
async function lock(directory, action) {
    const path = join(directory, '.studio.lock');
    let handle;
    try {
        handle = await open(path, 'wx', 0o600);
    }
    catch (error) {
        if (error.code === 'EEXIST')
            throw new Error('This project is locked by another command. After a crash, confirm no command is running and reconcile any submitting job before removing .studio.lock.');
        throw error;
    }
    try {
        await handle.writeFile(JSON.stringify({ pid: process.pid, createdAt: new Date().toISOString() }));
        return await action();
    }
    finally {
        await handle.close();
        await rm(path, { force: true });
    }
}
function parseArgs(args) {
    const parsed = { positional: [] };
    for (let i = 0; i < args.length; i++) {
        const value = args[i];
        if (value === '--transport') {
            if (parsed.transport !== undefined)
                throw new Error('--transport must be specified only once.');
            const transport = args[++i];
            if (!['mcp', 'cli', 'rest'].includes(transport))
                throw new Error('--transport must be mcp, cli, or rest.');
            parsed.transport = transport;
        }
        else if (value === '--job') {
            if (parsed.job !== undefined)
                throw new Error('--job must be specified only once.');
            const job = args[++i];
            if (!job || job.startsWith('-'))
                throw new Error('--job requires a saved job ID.');
            parsed.job = safeId(job);
        }
        else if (value.startsWith('-') && !['--help', '-h'].includes(value))
            throw new Error('Unknown option. Use help for supported flags; credentials must never be passed as arguments.');
        else
            parsed.positional.push(value);
    }
    const command = parsed.positional[0];
    if (parsed.transport && !['init', 'models', 'generate', 'resume', 'retry'].includes(command))
        throw new Error(`--transport is not supported by ${command ?? 'this command'}.`);
    if (parsed.job && command !== 'build-native-request')
        throw new Error('--job is only supported by build-native-request.');
    return parsed;
}
function selectedTransport(state, requested) {
    const transport = state.transport ?? 'rest';
    if (requested && requested !== transport)
        throw new Error(`This project uses ${state.transport ?? 'legacy REST'}. Create a new project to change connections; reconcile existing jobs through their original connection first.`);
    return transport;
}
function restClient(state, requested) {
    if (state && selectedTransport(state, requested) !== 'rest')
        throw new Error('REST cannot execute a project using another connection.');
    if (state && state.transport === undefined && requested !== 'rest')
        throw new Error('This legacy project has no saved connection. Explicitly select --transport rest to resume its REST workflow; this does not change its approval or migrate existing jobs.');
    if (!process.env.AISA_API_KEY)
        throw new Error('The explicitly selected REST connection requires AISA_API_KEY in the environment. Never paste the key into a command or project file.');
    return new AisaClient({ apiKey: process.env.AISA_API_KEY });
}
function nativeInstructions(transport) {
    return transport === 'mcp'
        ? 'Connect AIsa in your host using https://mcp.aisa.one/mcp, complete browser authorization, and run the account check. Import the host connection receipt, then use build-native-request and prepare-native; the host executes the quoted MCP operation. Do not supply an API key or switch to REST.'
        : 'Use the authenticated official AIsa CLI in your host to check the account and discover current tools. Import its connection receipt, then use build-native-request and prepare-native; the host executes the quoted CLI operation. This helper never reads CLI credentials or switches to REST.';
}
export async function main(args = process.argv.slice(2)) {
    const parsed = parseArgs(args);
    const [command, first, second, third] = parsed.positional;
    if (!command || ['--help', '-h', 'help'].includes(command)) {
        if (parsed.positional.length > 1)
            throw new Error('help takes no arguments.');
        return help;
    }
    if (command === 'platforms') {
        if (parsed.positional.length !== 1)
            throw new Error('platforms takes no arguments.');
        return { version: '1.1.0', ...PLATFORM_SUPPORT, placements: PLACEMENTS, meaning: 'Content workflow profiles and validated exports; no seller-account or publishing integrations. Future platforms are rejected at intake.' };
    }
    if (command === 'models') {
        if (parsed.positional.length !== 1)
            throw new Error('models takes no arguments.');
        const transport = parsed.transport ?? 'mcp';
        if (transport !== 'rest')
            return { transport, action: 'host-model-discovery-required', instructions: nativeInstructions(transport), next: 'Discover the live model catalog and selected model detail, complete schemas and quote in the same authenticated session. Offer every suitable currently available model; a catalog entry alone does not prove reference-input support.' };
        return { transport, models: await restClient().listModels(), verification: 'Catalog discovery only; media generation has not been tested by this command.' };
    }
    const count = { init: 3, 'research-import': 3, 'playbook-import': 3, report: 2, approve: 3, generate: 3, resume: 3, retry: 3, review: 3, status: 2, export: 3, 'connection-import': 3, 'build-native-request': 3, 'prepare-native': 3, 'mark-native-dispatched': 3, 'cancel-native-prepared': 3, 'ingest-native-result': 4, 'prepare-native-poll': 4, 'resume-native': 3, 'import-host-copy': 4 };
    if (!(command in count) || parsed.positional.length !== count[command])
        throw new Error(`Invalid command or arguments.\n${help}`);
    if (command === 'init') {
        const inputPath = resolve(first);
        const brief = validateBrief(await json(inputPath));
        const directory = resolve(second);
        try {
            await stat(directory);
            throw new Error('Project directory already exists; choose a new directory to preserve existing work.');
        }
        catch (error) {
            if (error.code !== 'ENOENT')
                throw error;
        }
        // Validate ALL source photos before creating project state or making any external call.
        const images = await Promise.all(brief.references.map(async (ref) => {
            safeId(ref.id);
            const info = await inspectMedia(resolve(dirname(inputPath), ref.path), 'image', 50 * 1024 * 1024);
            if (Math.min(info.width, info.height) < 256)
                throw new Error(`Photo ${ref.id} is too small; provide at least 256x256 pixels.`);
            return { ref, info };
        }));
        await mkdir(join(directory, 'references'), { recursive: true });
        const references = [];
        for (const { ref, info } of images) {
            const extension = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp' }[info.mimeType];
            const path = join(directory, 'references', `${ref.id}.${extension}`);
            await writeFile(path, await readFile(info.path), { flag: 'wx', mode: 0o600 });
            ref.path = path;
            references.push({ ...ref, path, sha256: info.sha256, mimeType: info.mimeType, width: info.width, height: info.height });
        }
        const state = initProject(brief, references, undefined, parsed.transport ?? 'mcp');
        await atomicJson(join(directory, 'project.json'), state);
        return { project: directory, transport: state.transport, stage: 'research-required', photos: references.length, next: 'Inspect the product photos, research the selected platform requirements and comparable creatives, then import the source-backed report.' };
    }
    const directory = resolve(first);
    return lock(directory, async () => {
        let state = await project(directory);
        if (parsed.transport)
            selectedTransport(state, parsed.transport);
        if (command === 'research-import')
            state = setResearch(state, await json(second));
        else if (command === 'playbook-import')
            state = setPlaybook(state, await json(second));
        else if (command === 'approve')
            state = approvePlaybook(state, await json(second));
        else if (command === 'connection-import')
            return importConnection(directory, state, await json(second));
        else if (command === 'build-native-request')
            return buildNativeRequest(directory, state, second, parsed.job);
        else if (command === 'prepare-native')
            return prepareNative(directory, state, await json(second));
        else if (command === 'mark-native-dispatched')
            return markNativeDispatched(directory, state, second);
        else if (command === 'cancel-native-prepared')
            return cancelNativePrepared(directory, state, second);
        else if (command === 'ingest-native-result')
            return ingestNativeResult(directory, state, second, await json(third));
        else if (command === 'prepare-native-poll')
            return prepareNativePoll(directory, state, second, await json(third));
        else if (command === 'resume-native')
            return resumeNative(directory, state, second);
        else if (command === 'import-host-copy')
            return importHostCopy(directory, state, second, await json(third));
        else if (command === 'generate' || command === 'retry') {
            const deliverable = assertReady(state).deliverables.find(item => item.id === second);
            if (!deliverable)
                throw new Error('Unknown deliverable in the approved playbook.');
            if (deliverable.kind === 'image' && deliverable.imageMode === 'preserve')
                return generate(directory, state, second, undefined, command === 'retry');
            const transport = selectedTransport(state, parsed.transport);
            if (transport !== 'rest')
                throw new Error(nativeInstructions(transport));
            return generate(directory, state, second, restClient(state, parsed.transport), command === 'retry');
        }
        else if (command === 'resume') {
            const transport = selectedTransport(state, parsed.transport);
            const job = (await loadLedger(directory)).jobs.filter(item => item.deliverableId === second).at(-1);
            if (transport !== 'rest' && job?.model !== 'local-photo-export')
                return resumeNative(directory, state, second);
            const deliverable = state.playbook?.deliverables.find(item => item.id === second);
            const needsRest = deliverable?.kind === 'video' && job && ['submitted', 'download-pending'].includes(job.status);
            return resume(directory, state, second, needsRest ? restClient(state, parsed.transport) : undefined);
        }
        else if (command === 'review')
            return review(directory, state, await json(second));
        else if (command === 'export')
            return exportPackage(directory, state, resolve(second));
        else if (command === 'status')
            return { transport: state.transport ?? 'legacy-rest', stage: state.approval ? 'approval-recorded' : state.playbook ? 'awaiting-user-approval' : 'research-required', approvalCurrent: state.approval ? state.approval.playbookHash === approvalHash(state) : false, ledger: await loadLedger(directory) };
        await atomicJson(join(directory, 'project.json'), state);
        await reports(directory, state);
        return { project: directory, report: state.research ? join(directory, 'research-report.md') : undefined, playbook: state.playbook ? join(directory, 'playbook.md') : undefined, approvalHash: state.playbook ? approvalHash(state) : undefined, approved: Boolean(state.approval), next: state.playbook && !state.approval ? 'Present both documents and ask the user to confirm or modify this exact playbook. Do not generate previews or final copy yet.' : undefined };
    });
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
    main().then(result => process.stdout.write(typeof result === 'string' ? result : `${JSON.stringify(result, null, 2)}\n`)).catch(error => {
        process.stderr.write(`${JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Command failed.' })}\n`);
        process.exitCode = 1;
    });
}
