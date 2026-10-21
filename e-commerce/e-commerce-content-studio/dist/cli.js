#!/usr/bin/env node
import { mkdir, open, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { AisaClient } from './aisa.js';
import { PLATFORM_SUPPORT, PLACEMENTS } from './types.js';
import { approvePlaybook, approvalHash, initProject, renderPlaybook, renderResearch, setPlaybook, setResearch, validateBrief, validateProject } from './workflow.js';
import { atomicJson, inspectMedia } from './media.js';
import { exportPackage, generate, loadLedger, resume, review, safeId, verifyReferences } from './production.js';
const help = `E-commerce Content Studio — version 1.0.0

Node.js 22+, ffmpeg and ffprobe are required. Paths may be absolute.
  platforms                                  Current profiles and future roadmap
  init <brief.json> <project-dir>             Decode and copy required product photos
  research-import <project-dir> <research.json>
  playbook-import <project-dir> <playbook.json>
  report <project-dir>                       Write research/playbook reports and hash
  approve <project-dir> <approval.json>       Record the user's exact-version approval
  generate <project-dir> <deliverable-id>     One approved production attempt
  resume <project-dir> <deliverable-id>       One status check / resume saved output
  retry <project-dir> <deliverable-id>        Retry confirmed failure within allowance
  review <project-dir> <review.json>          Record actual inspections of all outputs
  status <project-dir>                       Show approval and generation status
  export <project-dir> <new-destination>      Export only a fully reviewed package
  models                                    Discover AIsa model routes (API key needed)

Research runs through the host's AIsa MCP tools, with current schema and quote checks.
Import the source-backed research and proposed playbook; show both to the user before
recording approval. No product photos means stop, including for copy-only requests.
For direct REST generation set AISA_API_KEY in the environment. Never pass keys as
arguments. This tool does not publish listings or claim live account integration.
Video requires a public HTTPS remoteUrl for the same approved reference photograph.
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
function client() {
    return process.env.AISA_API_KEY ? new AisaClient({ apiKey: process.env.AISA_API_KEY }) : undefined;
}
export async function main(args = process.argv.slice(2)) {
    const [command, first, second, ...extra] = args;
    if (!command || ['--help', '-h', 'help'].includes(command))
        return help;
    if (command === 'platforms') {
        if (args.length !== 1)
            throw new Error('platforms takes no arguments.');
        return { version: '1.0.0', ...PLATFORM_SUPPORT, placements: PLACEMENTS, meaning: 'Content workflow profiles and validated exports; no seller-account or publishing integrations. Future platforms are rejected at intake.' };
    }
    if (command === 'models') {
        if (args.length !== 1)
            throw new Error('models takes no arguments.');
        const connection = client();
        if (!connection)
            throw new Error('Set AISA_API_KEY for model discovery.');
        return { models: await connection.listModels(), verification: 'Catalog discovery only; media generation has not been tested by this command.' };
    }
    const count = { init: 3, 'research-import': 3, 'playbook-import': 3, report: 2, approve: 3, generate: 3, resume: 3, retry: 3, review: 3, status: 2, export: 3 };
    if (!(command in count) || args.length !== count[command] || extra.length)
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
        const state = initProject(brief, references);
        await atomicJson(join(directory, 'project.json'), state);
        return { project: directory, stage: 'research-required', photos: references.length, next: 'Inspect the product photos, research the selected platform requirements and comparable creatives, then import the source-backed report.' };
    }
    const directory = resolve(first);
    return lock(directory, async () => {
        let state = await project(directory);
        if (command === 'research-import')
            state = setResearch(state, await json(second));
        else if (command === 'playbook-import')
            state = setPlaybook(state, await json(second));
        else if (command === 'approve')
            state = approvePlaybook(state, await json(second));
        else if (command === 'generate' || command === 'retry')
            return generate(directory, state, second, client(), command === 'retry');
        else if (command === 'resume')
            return resume(directory, state, second, client());
        else if (command === 'review')
            return review(directory, state, await json(second));
        else if (command === 'export')
            return exportPackage(directory, state, resolve(second));
        else if (command === 'status')
            return { stage: state.approval ? 'approval-recorded' : state.playbook ? 'awaiting-user-approval' : 'research-required', approvalCurrent: state.approval ? state.approval.playbookHash === approvalHash(state) : false, ledger: await loadLedger(directory) };
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
