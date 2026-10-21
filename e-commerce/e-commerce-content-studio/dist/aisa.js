export class AisaError extends Error {
    code;
    httpStatus;
    ambiguous;
    taskId;
    constructor(code, message, httpStatus, ambiguous = false, taskId) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
        this.ambiguous = ambiguous;
        this.taskId = taskId;
        this.name = "AisaError";
    }
}
const ORIGIN = "https://api.aisa.one";
const MAX_RESPONSE = 96 * 1024 * 1024;
const IMAGE_ROUTE = "/v1beta/models/{model}:generateContent";
const IMAGE_EDIT_ROUTE = "/v1/images/edits";
const VIDEO_ROUTE = "/v1/video/generations";
const IMAGE_MIMES = new Set(["image/png", "image/jpeg", "image/webp"]);
function object(value) {
    if (!value || typeof value !== "object" || Array.isArray(value))
        throw new AisaError("invalid_response", "AIsa returned an unexpected response structure.");
    return value;
}
function string(value, label) {
    if (typeof value !== "string" || !value.trim())
        throw new AisaError("invalid_response", `AIsa response is missing ${label}.`);
    return value;
}
function inputString(value, label, max = 100_000) {
    if (typeof value !== "string" || !value.trim() || value.length > max)
        throw new AisaError("invalid_input", `${label} must be nonempty and at most ${max} characters.`);
    return value;
}
function httpsUrl(value) {
    let url;
    try {
        url = new URL(value);
    }
    catch {
        throw new AisaError("invalid_url", "A public HTTPS URL is required.");
    }
    const host = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || url.username || url.password || host === "localhost" || host.endsWith(".local") || host.startsWith("[") || /^\d+(?:\.\d+){3}$/.test(host)) {
        throw new AisaError("invalid_url", "Use a public HTTPS URL without embedded credentials or a literal IP address.");
    }
    return url.href;
}
function imageSignature(bytes, mime) {
    const b = Buffer.from(bytes);
    if (mime === "image/png")
        return b.length > 24 && b.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])) && b.toString("ascii", 12, 16) === "IHDR";
    if (mime === "image/jpeg")
        return b.length > 4 && b[0] === 255 && b[1] === 216 && b[b.length - 2] === 255 && b[b.length - 1] === 217;
    return mime === "image/webp" && b.length > 20 && b.toString("ascii", 0, 4) === "RIFF" && b.toString("ascii", 8, 12) === "WEBP";
}
function imageBytes(encoded, mime) {
    if (typeof mime !== "string" || !IMAGE_MIMES.has(mime) || typeof encoded !== "string" || !encoded || encoded.length % 4 !== 0 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(encoded)) {
        throw new AisaError("invalid_media", "AIsa returned invalid image encoding or an unsupported image type.");
    }
    const data = Buffer.from(encoded, "base64");
    if (data.toString("base64") !== encoded || !imageSignature(data, mime))
        throw new AisaError("invalid_media", "AIsa returned image bytes that do not match the declared type.");
    return { data, mimeType: mime };
}
export class AisaClient {
    apiKey;
    fetcher;
    timeoutMs;
    catalog;
    constructor(options) {
        if (!options.apiKey?.trim() || /[\r\n]/.test(options.apiKey))
            throw new AisaError("missing_key", "Set AISA_API_KEY to use AIsa.");
        this.apiKey = options.apiKey;
        this.fetcher = options.fetch ?? globalThis.fetch;
        this.timeoutMs = options.timeoutMs ?? 180_000;
        if (!Number.isFinite(this.timeoutMs) || this.timeoutMs < 1 || this.timeoutMs > 600_000)
            throw new AisaError("invalid_input", "Request timeout must be between 1 and 600000 milliseconds.");
    }
    async request(path, body) {
        const method = body === undefined ? "GET" : "POST";
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeoutMs);
        try {
            const response = await this.fetcher(ORIGIN + path, {
                method, headers: { Authorization: `Bearer ${this.apiKey}`, Accept: "application/json", ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
                ...(body === undefined ? {} : { body: JSON.stringify(body) }), redirect: "error", signal: controller.signal,
            });
            if (!response.ok) {
                await response.body?.cancel();
                // Provider messages can echo prompts, signed URLs, or credentials: never print them.
                throw new AisaError("http_error", `AIsa request failed (HTTP ${response.status}).`, response.status, method === "POST" && response.status >= 500);
            }
            if (!/\bapplication\/(?:[\w.+-]+\+)?json\b/i.test(response.headers.get("content-type") ?? "")) {
                await response.body?.cancel();
                throw new AisaError("invalid_response", "AIsa returned a non-JSON response.", undefined, method === "POST");
            }
            const reader = response.body?.getReader();
            if (!reader)
                throw new AisaError("invalid_response", "AIsa returned an empty response.", undefined, method === "POST");
            const chunks = [];
            let length = 0;
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                length += value.byteLength;
                if (length > MAX_RESPONSE) {
                    await reader.cancel();
                    throw new AisaError("response_too_large", "AIsa response exceeded the 96 MiB limit.", undefined, method === "POST");
                }
                chunks.push(value);
            }
            let result;
            try {
                result = object(JSON.parse(Buffer.concat(chunks).toString("utf8")));
            }
            catch {
                throw new AisaError("invalid_response", "AIsa returned malformed JSON.", undefined, method === "POST");
            }
            if (result.error || result.success === false)
                throw new AisaError("provider_error", "AIsa returned a provider error; inspect the provider dashboard using the saved request record.", undefined, method === "POST");
            return result;
        }
        catch (error) {
            if (error instanceof AisaError)
                throw error;
            throw new AisaError(controller.signal.aborted ? "timeout" : "network_error", controller.signal.aborted ? "AIsa request timed out. Do not automatically resubmit a generation request." : "AIsa request failed before a usable response was received. Do not automatically resubmit a generation request.", undefined, method === "POST");
        }
        finally {
            clearTimeout(timer);
        }
    }
    async listModels() {
        const result = await this.request("/v1/models");
        if (!Array.isArray(result.data))
            throw new AisaError("invalid_response", "AIsa model catalog is missing its data array.");
        const models = result.data.map((item) => {
            const row = object(item);
            const id = string(row.id, "model ID");
            if (!row.aisa)
                return { id };
            const aisa = object(row.aisa);
            const routes = Array.isArray(aisa.routes) ? aisa.routes.map((route) => {
                const r = object(route);
                return { method: string(r.method, "route method"), path: string(r.path, "route path"), ...(typeof r.key === "string" ? { key: r.key } : {}) };
            }) : [];
            return { id, aisa: { ...(typeof aisa.model_type === "string" ? { model_type: aisa.model_type } : {}), capabilities: Array.isArray(aisa.capabilities) ? aisa.capabilities.filter((x) => typeof x === "string") : [], routes } };
        });
        this.catalog = { at: Date.now(), models };
        return structuredClone(models);
    }
    async requireModel(id, type, path) {
        inputString(id, "Model ID", 200);
        if (!this.catalog || Date.now() - this.catalog.at > 300_000)
            await this.listModels();
        const model = this.catalog.models.find((row) => row.id === id);
        if (!model || model.aisa?.model_type !== type || !model.aisa.routes?.some((route) => route.method.toUpperCase() === "POST" && (route.path === path || route.path === path.replace("{model}", encodeURIComponent(id))))) {
            throw new AisaError("unsupported_model", "The selected model does not advertise the required type and route in the current AIsa catalog.");
        }
    }
    async search(input) {
        inputString(input.query, "Search query", 4000);
        const maxResults = input.maxResults ?? 5;
        if (!Number.isInteger(maxResults) || maxResults < 1 || maxResults > 20)
            throw new AisaError("invalid_input", "Search maxResults must be 1–20.");
        if (input.includeDomains && (!Array.isArray(input.includeDomains) || input.includeDomains.length > 300 || input.includeDomains.some((x) => typeof x !== "string" || !/^[a-z0-9.-]+$/i.test(x))))
            throw new AisaError("invalid_input", "Search domains must be host names.");
        const result = await this.request("/apis/v1/tavily/search", { query: input.query, search_depth: input.depth ?? "basic", max_results: maxResults, include_answer: false, include_raw_content: true, ...(input.includeDomains?.length ? { include_domains: input.includeDomains } : {}) });
        if (!Array.isArray(result.results))
            throw new AisaError("invalid_response", "AIsa search response is missing results.");
        return result.results.map((item) => {
            const row = object(item);
            return { title: string(row.title, "search title"), url: httpsUrl(string(row.url, "search URL")), content: typeof row.raw_content === "string" && row.raw_content.trim() ? row.raw_content : string(row.content, "search content"), ...(typeof row.score === "number" && Number.isFinite(row.score) ? { score: row.score } : {}) };
        });
    }
    async extract(input) {
        if (!Array.isArray(input.urls) || input.urls.length < 1 || input.urls.length > 20)
            throw new AisaError("invalid_input", "Extract requires 1–20 public HTTPS URLs.");
        const urls = input.urls.map(httpsUrl);
        const result = await this.request("/apis/v1/tavily/extract", { urls, extract_depth: "basic", format: "markdown" });
        if (!Array.isArray(result.results))
            throw new AisaError("invalid_response", "AIsa extract response is missing results.");
        const results = result.results.map((item) => { const row = object(item); return { url: httpsUrl(string(row.url, "extract URL")), content: string(row.raw_content, "extracted content") }; });
        const returned = new Set(results.map((r) => r.url));
        return { results, failedUrls: urls.filter((url) => !returned.has(url)) };
    }
    async copy(input) {
        inputString(input.system, "System instructions");
        inputString(input.prompt, "Copy prompt");
        if (input.maxTokens !== undefined && (!Number.isInteger(input.maxTokens) || input.maxTokens < 1))
            throw new AisaError("invalid_input", "maxTokens must be a positive integer.");
        await this.requireModel(input.model, "text", "/v1/chat/completions");
        const result = await this.request("/v1/chat/completions", { model: input.model, messages: [{ role: "system", content: input.system }, { role: "user", content: input.prompt }], stream: false, ...(input.maxTokens ? { max_tokens: input.maxTokens } : {}) });
        if (!Array.isArray(result.choices) || !result.choices.length)
            throw new AisaError("invalid_response", "AIsa returned no copy choices.");
        const texts = result.choices.map((choice) => {
            const row = object(choice);
            if (row.finish_reason && row.finish_reason !== "stop")
                throw new AisaError("incomplete_output", "Copy generation did not finish normally; no partial copy was accepted.");
            return string(object(row.message).content, "copy text");
        });
        return { text: texts.join("\n\n"), ...(result.usage === undefined ? {} : { usage: result.usage }) };
    }
    async generateImages(input) {
        inputString(input.prompt, "Image prompt");
        if (!Array.isArray(input.references) || !input.references.length)
            throw new AisaError("product_photos_required", "At least one validated product photo is required for image generation.");
        let total = 0;
        for (const ref of input.references) {
            if (!(ref.data instanceof Uint8Array) || !IMAGE_MIMES.has(ref.mimeType) || !imageSignature(ref.data, ref.mimeType))
                throw new AisaError("invalid_media", "A product reference does not match its declared image type.");
            total += ref.data.byteLength;
        }
        if (total > 14 * 1024 * 1024)
            throw new AisaError("invalid_input", "Combined product references exceed the 14 MiB inline-image limit; prepare smaller reviewed copies.");
        const ratios = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"];
        if (input.aspectRatio !== undefined && !ratios.includes(input.aspectRatio))
            throw new AisaError("invalid_input", "Unsupported Gemini image aspect ratio.");
        if (input.imageSize !== undefined && !["512", "1K", "2K", "4K"].includes(input.imageSize))
            throw new AisaError("invalid_input", "Gemini imageSize must be 512, 1K, 2K, or 4K; confirm chosen-model support and cost first.");
        // GPT Image uses a different reference-image contract from Gemini. Select
        // only the explicitly requested model; never retry on a different provider.
        if (/^gpt-image-2(?:\.5-(?:flare|sunburst))?(?:-\d{4}-\d{2}-\d{2})?$/.test(input.model)) {
            const sizes = {
                "1K/1:1": "1024x1024", "1K/3:2": "1536x1024", "1K/2:3": "1024x1536", "2K/1:1": "2048x2048",
            };
            const size = sizes[`${input.imageSize ?? "1K"}/${input.aspectRatio ?? "1:1"}`];
            if (!size)
                throw new AisaError("invalid_input", "The GPT Image adapter supports 1K square/3:2/2:3 and 2K square generation. Choose a supported native size separately from final export dimensions.");
            if (input.references.length > 16)
                throw new AisaError("invalid_input", "GPT Image editing supports at most 16 product references.");
            await this.requireModel(input.model, "image", IMAGE_EDIT_ROUTE);
            const result = await this.request(IMAGE_EDIT_ROUTE, {
                model: input.model, prompt: input.prompt,
                images: input.references.map(ref => ({ image_url: `data:${ref.mimeType};base64,${Buffer.from(ref.data).toString("base64")}` })),
                n: 1, size, quality: "medium", output_format: "png", stream: false,
            });
            if (!Array.isArray(result.data) || !result.data.length)
                throw new AisaError("no_images", "AIsa returned no edited images; an empty or text-only response is not a completed image deliverable.");
            const images = [];
            const texts = [];
            for (const item of result.data) {
                const row = object(item);
                if (typeof row.b64_json !== "string")
                    throw new AisaError("invalid_media", "The GPT Image edit response is missing inline image bytes; a URL alone has not been downloaded or validated.");
                images.push(imageBytes(row.b64_json, "image/png"));
                if (typeof row.revised_prompt === "string")
                    texts.push(row.revised_prompt);
            }
            return { images, text: texts.join("\n") };
        }
        await this.requireModel(input.model, "image", IMAGE_ROUTE);
        const result = await this.request(IMAGE_ROUTE.replace("{model}", encodeURIComponent(input.model)), {
            contents: [{ role: "user", parts: [{ text: input.prompt }, ...input.references.map((ref) => ({ inline_data: { mime_type: ref.mimeType, data: Buffer.from(ref.data).toString("base64") } }))] }],
            generationConfig: { responseModalities: ["TEXT", "IMAGE"], ...(input.aspectRatio || input.imageSize ? { imageConfig: { ...(input.aspectRatio ? { aspectRatio: input.aspectRatio } : {}), ...(input.imageSize ? { imageSize: input.imageSize } : {}) } } : {}) },
        });
        if (!Array.isArray(result.candidates))
            throw new AisaError("invalid_response", "AIsa returned no image candidates.");
        const images = [];
        const texts = [];
        for (const candidate of result.candidates) {
            const c = object(candidate);
            if (c.finishReason && c.finishReason !== "STOP")
                throw new AisaError("incomplete_output", "Image generation did not finish normally; inspect the provider job before retrying.");
            const parts = object(c.content).parts;
            if (!Array.isArray(parts))
                throw new AisaError("invalid_response", "AIsa image candidate is missing parts.");
            for (const part of parts) {
                const p = object(part);
                if (p.thought === true)
                    continue;
                if (typeof p.text === "string")
                    texts.push(p.text);
                const inline = p.inline_data ?? p.inlineData;
                if (inline !== undefined) {
                    const data = object(inline);
                    images.push(imageBytes(data.data, data.mime_type ?? data.mimeType));
                }
            }
        }
        if (!images.length)
            throw new AisaError("no_images", "AIsa returned no usable images; text-only output is not a completed image deliverable.");
        return { images, text: texts.join("\n") };
    }
    async submitVideo(input) {
        inputString(input.prompt, "Video prompt");
        if (input.model !== "wan2.7-i2v")
            throw new AisaError("unsupported_model", "Only the documented wan2.7-i2v reference-video adapter is implemented; other video models need their own verified request contract.");
        if (!Array.isArray(input.referenceUrls) || !input.referenceUrls.length)
            throw new AisaError("product_photos_required", "Video generation requires an HTTPS URL for a verified product photo; no upload route is assumed.");
        const references = input.referenceUrls.map(httpsUrl);
        const duration = input.duration ?? 5;
        if (!Number.isInteger(duration) || duration < 2 || duration > 15)
            throw new AisaError("invalid_input", "Video duration must be a whole number from 2 to 15 seconds; confirm model limits and pricing before approval.");
        if (input.ratio !== undefined && !["16:9", "9:16", "1:1"].includes(input.ratio))
            throw new AisaError("invalid_input", "Video ratio must be 16:9, 9:16, or 1:1; confirm availability in the approved provider contract.");
        await this.requireModel(input.model, "video", VIDEO_ROUTE);
        const model = this.catalog.models.find((row) => row.id === input.model);
        if (!model.aisa?.routes?.some((route) => route.method.toUpperCase() === "GET" && route.path === `${VIDEO_ROUTE}/{task_id}`))
            throw new AisaError("unsupported_model", "The selected video model does not advertise a supported task-status route.");
        const result = await this.request(VIDEO_ROUTE, { model: input.model, content: [{ type: "text", text: input.prompt }, ...references.map((url) => ({ type: "image_url", image_url: { url }, role: "reference_image" }))], duration, ratio: input.ratio ?? "16:9", generate_audio: false });
        try {
            return parseVideoJob(result, undefined, true);
        }
        catch (error) {
            const row = result.output && typeof result.output === "object" ? result.output : result.data && typeof result.data === "object" ? result.data : result;
            const id = row.task_id ?? row.id ?? result.task_id ?? result.id;
            const taskId = typeof id === "string" && /^[a-zA-Z0-9_-]+$/.test(id) ? id : undefined;
            throw new AisaError(error instanceof AisaError ? error.code : "invalid_response", error instanceof AisaError ? error.message : "Video submission returned an unexpected response.", undefined, true, taskId);
        }
    }
    async getVideoJob(id) {
        inputString(id, "Video task ID", 300);
        if (!/^[a-zA-Z0-9_-]+$/.test(id))
            throw new AisaError("invalid_input", "Video task ID contains unsupported characters.");
        return parseVideoJob(await this.request(`${VIDEO_ROUTE}/${encodeURIComponent(id)}`), id, false);
    }
}
/** Accept known provider envelopes; reject unknown states instead of treating them as success. */
export function parseVideoJob(value, expectedId, submission = false) {
    const root = object(value);
    const row = root.output ? object(root.output) : root.data && !Array.isArray(root.data) ? object(root.data) : root;
    const id = string(row.task_id ?? row.id ?? root.task_id ?? root.id ?? expectedId, "video task ID");
    if (!/^[a-zA-Z0-9_-]+$/.test(id) || (expectedId && id !== expectedId))
        throw new AisaError("invalid_response", "AIsa returned an unexpected video task ID.");
    const raw = row.task_status ?? row.status ?? root.status;
    const statuses = { pending: "queued", queued: "queued", submitted: "queued", running: "running", processing: "running", succeeded: "succeeded", completed: "succeeded", failed: "failed", cancelled: "cancelled", canceled: "cancelled" };
    const status = raw === undefined && submission ? "queued" : typeof raw === "string" ? statuses[raw.toLowerCase()] : undefined;
    if (!status)
        throw new AisaError("unknown_job_status", "AIsa returned an unknown video task state; keep the task ID and inspect it before taking further action.");
    const urls = [];
    function collect(entry) {
        if (!entry || typeof entry !== "object" || Array.isArray(entry))
            return;
        const item = entry;
        if (typeof item.video_url === "string")
            urls.push(httpsUrl(item.video_url));
        if (item.content && typeof item.content === "object" && !Array.isArray(item.content))
            collect(item.content);
        if (Array.isArray(item.results))
            for (const r of item.results)
                collect(r);
        if (Array.isArray(item.videos))
            for (const video of item.videos) {
                if (typeof video === "string")
                    urls.push(httpsUrl(video));
                else {
                    const r = object(video);
                    if (typeof r.url === "string")
                        urls.push(httpsUrl(r.url));
                    else
                        collect(r);
                }
            }
    }
    collect(row);
    const unique = [...new Set(urls)];
    if (status === "succeeded" && !unique.length)
        throw new AisaError("missing_video", "The video task reports success without a usable video URL; keep its ID and inspect the provider result.");
    return { id, status, urls: unique };
}
