import { createHash, randomUUID } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { lookup } from 'node:dns/promises';
import { isIP } from 'node:net';
import { mkdir, readFile, rename, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
const exec = promisify(execFile);
export class MediaValidationError extends Error {
}
export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
export async function atomicJson(path, value) {
    await mkdir(dirname(path), { recursive: true });
    const temporary = `${path}.${randomUUID()}.tmp`;
    try {
        await writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600, flag: 'wx' });
        await rename(temporary, path);
    }
    finally {
        await rm(temporary, { force: true });
    }
}
export function detectMime(bytes) {
    const b = Buffer.from(bytes);
    if (b.length >= 8 && b.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])))
        return 'image/png';
    if (b.length >= 3 && b[0] === 255 && b[1] === 216 && b[2] === 255)
        return 'image/jpeg';
    if (b.length >= 12 && b.toString('ascii', 0, 4) === 'RIFF' && b.toString('ascii', 8, 12) === 'WEBP')
        return 'image/webp';
    if (b.length >= 12 && b.toString('ascii', 4, 8) === 'ftyp')
        return 'video/mp4';
    throw new MediaValidationError('Unsupported or corrupt media: expected PNG, JPEG, WebP or MP4 bytes.');
}
export function strictBase64(value) {
    if (!value || value.length % 4 !== 0 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
        throw new MediaValidationError('Invalid base64 media payload.');
    }
    const result = Buffer.from(value, 'base64');
    if (!result.length)
        throw new MediaValidationError('Empty media payload.');
    return result;
}
export async function inspectMedia(path, kind, maxBytes = 512 * 1024 * 1024) {
    const fullPath = resolve(path);
    const info = await stat(fullPath);
    if (!info.isFile() || info.size <= 0 || info.size > maxBytes)
        throw new MediaValidationError('Media must be a nonempty regular file within the allowed size.');
    const bytes = await readFile(fullPath);
    const mimeType = detectMime(bytes);
    if (!mimeType.startsWith(`${kind}/`))
        throw new MediaValidationError(`Expected ${kind} media, received ${mimeType}.`);
    let raw;
    try {
        ({ stdout: raw } = await exec('ffprobe', ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', fullPath], { timeout: 30_000, maxBuffer: 1024 * 1024 }));
        await exec('ffmpeg', ['-v', 'error', '-xerror', '-nostdin', '-i', fullPath, '-map', '0:v:0', '-f', 'null', '-'], { timeout: 120_000, maxBuffer: 1024 * 1024 });
    }
    catch (error) {
        const code = error.code;
        if (code === 'ENOENT')
            throw new Error('Install ffmpeg and ffprobe before processing media.');
        throw new MediaValidationError('Media decoding failed; the file is incomplete, invalid, or exceeded the decode deadline.');
    }
    const probe = JSON.parse(raw);
    const stream = probe.streams?.find(s => s.codec_type === 'video');
    if (!stream?.width || !stream.height || stream.width * stream.height > 100_000_000)
        throw new MediaValidationError('Missing or excessive media dimensions.');
    if (kind === 'image' && Number(stream.nb_frames ?? 1) > 1)
        throw new MediaValidationError('Product references and image outputs must be still images.');
    const durationSeconds = kind === 'video' ? Number(probe.format?.duration ?? stream.duration) : undefined;
    if (kind === 'video' && (!durationSeconds || !Number.isFinite(durationSeconds)))
        throw new MediaValidationError('Video has no valid duration.');
    return { path: fullPath, sha256: sha256(bytes), mimeType, bytes: bytes.length, width: stream.width, height: stream.height, ...(durationSeconds ? { durationSeconds } : {}) };
}
function publicAddress(address) {
    if (address.includes(':')) {
        const a = address.toLowerCase();
        return !a.startsWith('::') && !a.startsWith('fc') && !a.startsWith('fd') && !a.startsWith('fe8') && !a.startsWith('fe9') && !a.startsWith('fea') && !a.startsWith('feb') && !a.startsWith('ff');
    }
    const [a, b] = address.split('.').map(Number);
    return a !== 0 && a !== 10 && a !== 127 && a < 224 && !(a === 169 && b === 254) && !(a === 172 && b >= 16 && b <= 31) && !(a === 192 && b === 168) && !(a === 100 && b >= 64 && b <= 127);
}
export async function validateRemoteUrl(value) {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443'))
        throw new Error('Media downloads require a public HTTPS URL without credentials.');
    const host = url.hostname.replace(/^\[|\]$/g, '');
    const addresses = isIP(host) ? [{ address: host }] : await lookup(host, { all: true });
    if (!addresses.length || addresses.some(a => !publicAddress(a.address)))
        throw new Error('Private or local media download URLs are not allowed.');
    return url;
}
export async function downloadBytes(value, maxBytes, fetchImpl = fetch) {
    let url = await validateRemoteUrl(value);
    const signal = AbortSignal.timeout(120_000);
    for (let redirects = 0; redirects <= 3; redirects++) {
        const response = await fetchImpl(url, { redirect: 'manual', signal });
        if (response.status >= 300 && response.status < 400) {
            const location = response.headers.get('location');
            await response.body?.cancel();
            if (!location || redirects === 3)
                throw new Error('Media download redirect limit exceeded.');
            url = await validateRemoteUrl(new URL(location, url).href);
            continue;
        }
        if (!response.ok || !response.body)
            throw new Error(`Media download failed (HTTP ${response.status}); resume the saved job instead of regenerating.`);
        if (Number(response.headers.get('content-length')) > maxBytes) {
            await response.body.cancel();
            throw new MediaValidationError('Media download exceeds the transport safety limit.');
        }
        const reader = response.body.getReader();
        const chunks = [];
        let total = 0;
        try {
            while (true) {
                const chunk = await reader.read();
                if (chunk.done)
                    break;
                total += chunk.value.length;
                if (total > maxBytes)
                    throw new MediaValidationError('Media download exceeds the transport safety limit.');
                chunks.push(chunk.value);
            }
        }
        finally {
            await reader.cancel().catch(() => undefined);
        }
        if (!total)
            throw new MediaValidationError('Empty media download.');
        return Buffer.concat(chunks);
    }
    throw new Error('Media download did not complete.');
}
export async function saveMedia(bytes, outputStem, kind) {
    const mime = detectMime(bytes);
    const extension = { 'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'video/mp4': 'mp4' };
    const path = `${outputStem}.${extension[mime]}`;
    await mkdir(dirname(path), { recursive: true });
    const temporary = `${outputStem}.${randomUUID()}.tmp.${extension[mime]}`;
    try {
        await writeFile(temporary, bytes, { flag: 'wx', mode: 0o600 });
        const inspected = await inspectMedia(temporary, kind);
        // Refuse accidental overwrites; job resumption should reuse an existing hash-matched artifact.
        try {
            await stat(path);
            throw new Error(`Output already exists: ${path}`);
        }
        catch (error) {
            if (error.code !== 'ENOENT')
                throw error;
        }
        await rename(temporary, path);
        return { ...inspected, path: resolve(path) };
    }
    finally {
        await rm(temporary, { force: true });
    }
}
export async function preservePhoto(source, size, outputStem) {
    const match = /^(\d+)x(\d+)$/.exec(size);
    if (!match)
        throw new Error('Photo export requires WIDTHxHEIGHT.');
    const [width, height] = match.slice(1).map(Number);
    if (Math.min(width, height) < 256 || Math.max(width, height) > 8192)
        throw new Error('Photo export dimensions must be between 256 and 8192.');
    await inspectMedia(source, 'image', 50 * 1024 * 1024);
    await mkdir(dirname(outputStem), { recursive: true });
    const temporary = `${outputStem}.${randomUUID()}.png`;
    try {
        // Fit the supplied photograph without cropping, redrawing or inventing unseen product surfaces.
        await exec('ffmpeg', ['-v', 'error', '-nostdin', '-i', resolve(source), '-filter_complex', `[0:v]scale=${width}:${height}:force_original_aspect_ratio=decrease,format=rgba[product];color=c=white:s=${width}x${height}[background];[background][product]overlay=(W-w)/2:(H-h)/2:format=auto,format=rgb24`, '-frames:v', '1', temporary], { timeout: 60_000, maxBuffer: 1024 * 1024 });
        return await saveMedia(await readFile(temporary), outputStem, 'image');
    }
    finally {
        await rm(temporary, { force: true });
    }
}
