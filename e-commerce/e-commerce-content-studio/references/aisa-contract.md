# AIsa adapter contracts

Reviewed **2026-10-21**. The authenticated catalog check found GPT Image edit routes but no image model compatible with the existing Gemini adapter. One direct `gpt-image-2` adapter call returned a decoded 1024×1024 PNG through AIsa. This verifies that request path only: it does not establish other models/sizes, the full CLI workflow or acceptable product fidelity. These REST contracts do not establish native MCP capability for the separately packaged WorkBuddy expert.

## Discovery and authorization

Follow the shared AIsa connection and spending rules in `SKILL.md`. The bundled runtime is REST-only and does not bridge to MCP/CLI. When those interfaces are available, discover and quote native operations; missing native media generation is a capability gap, not permission to bypass the fallback gate.

For an eligible HTTP fallback, use `GET https://api.aisa.one/v1/models` with `Authorization: Bearer $AISA_API_KEY`. The [current catalog guide](https://aisa.one/docs/guides/models) describes the free response as `data[]` with `id` and `aisa.model_type`, `aisa.capabilities`, and `aisa.routes[]` (`method`, `path`, optional `key`). Every production adapter checks the selected model's type and exact route; unknown models/routes fail before generation. Catalog entries are cached for five minutes within a client instance.

Use AIsa MCP discovery with the complete goal first, then atomic capabilities; request full schemas and current quotes before paid research. Tools are discovered dynamically, not assumed from static names. Model generation must have a product reference, approved playbook, selected model, price evidence, and approved cost scope. `AisaClient` is the transport layer: use the gated studio workflow rather than calling it independently to bypass those checks.

## Implemented routes

| Operation | Route and request | Response |
| --- | --- | --- |
| Search | `POST /apis/v1/tavily/search`: `query`, `search_depth`, `max_results`, optional `include_domains`, `include_answer:false`, `include_raw_content:true` | `results[]`: title, URL, content/raw_content, optional relevance score. A relevance score is not commerce performance. |
| Extract | `POST /apis/v1/tavily/extract`: `urls`, `extract_depth:"basic"`, `format:"markdown"` | `results[]`: URL and raw_content. Missing requested URLs are returned separately as failures. |
| Copy | `POST /v1/chat/completions`: selected `model`, system/user `messages`, `stream:false`, optional `max_tokens` | Every text choice is retained; nonterminal/truncated choices fail. |
| GPT Image product edits | `POST /v1/images/edits`: selected GPT Image 2 model, `prompt`, required inline `images[]`, `n:1`, supported `size`, `quality:"medium"`, `output_format:"png"`, `stream:false` | Decode and validate every `data[].b64_json` PNG; retain optional `revised_prompt`. URL-only and empty outputs fail. |
| Gemini product edits | `POST /v1beta/models/{model}:generateContent`: text plus required inline product photos; currently no compatible model in the checked catalog | All non-thought image parts across every candidate are retained. |
| Product video, experimental | `POST /v1/video/generations`: only the documented `wan2.7-i2v` adapter | Save the returned task ID immediately, then query it; never resubmit to poll. |
| Video status, experimental | `GET /v1/video/generations/{task_id}` | Known queued/running/terminal states only; successful jobs require usable video URLs. |

Search/extract request and response fields were checked in AIsa's [complete OpenAPI contract](https://aisa.one/openapi.json), including its `/apis/v1/tavily/search` and `/apis/v1/tavily/extract` operations. See also the [search reference](https://aisa.one/docs/api-reference/search/post_tavily-search) and [extraction catalog](https://aisa.one/api/tavily-extract). The contract supports quote/max-price headers for Tavily; use MCP quotes for research authorization. This skill does not infer a fixed price from old examples.

## GPT Image reference request

The [AIsa GPT Image 2 page](https://aisa.one/models/gpt-image-2) advertises `/v1/images/edits`. Its displayed chat-style example is not a usable image-edit contract, and AIsa's downloaded OpenAPI omits this operation. The adapter uses the JSON `images[].image_url` data-URL shape documented in [OpenAI's image-edit reference](https://developers.openai.com/api/reference/resources/images/methods/edit); the live test confirmed this shape for `gpt-image-2` at medium quality and 1024×1024.

The selected GPT Image 2 model must advertise the exact edit route in the authenticated catalog. The adapter sends reviewed JPEG, PNG or WebP references inline, at most 16 and 14 MiB combined. It requests one PNG at medium quality with this bounded native-size mapping:

| `imageSize` / aspect ratio | Native request size |
| --- | --- |
| `1K` / `1:1` | `1024x1024` |
| `1K` / `3:2` | `1536x1024` |
| `1K` / `2:3` | `1024x1536` |
| `2K` / `1:1` | `2048x2048` |

Unsupported aspect ratios and native-size combinations fail during playbook validation, before any attempt or estimate is reserved. GPT Image native dimensions must cover the requested export; hidden upscaling is rejected. Final export dimensions are separate from generation size, but the runtime derives the requested aspect ratio from the export dimensions. The adapter never falls back to another model, text-only generation, remote photo hosting or an unverified URL response. Every returned PNG must decode and pass technical and visual review.

Live test receipt: **2026-10-21**, HTTP 200 in 34,459 ms; request ID `1792515035362642611-362642662`; PNG 1,233,199 bytes; SHA-256 `74d9cf83a1476fc0dbec4aa7a6f54032b9a97ef06ffe1013d4a8385e4a164c4d`. This called the source `AisaClient` directly with the unchanged 222×222 product photo, which is below the full CLI workflow's 256-pixel intake minimum. Visual review found that the generated scene reinterpreted the tumbler lid/rim; the image is not listing-approved. The receipt verifies transport and output decoding, not a completed research/approval/production/QA workflow.

## Gemini reference-image request

The adapter remains implemented, but the authenticated **2026-10-21** catalog check found no compatible image model. Refresh discovery before using it; do not treat historical model examples as working choices.

The AIsa OpenAPI `GenerateContentRequest` confirms `contents`, parts with `inline_data`, and `generationConfig`; its operation server is `/v1beta`. The nested binary shape is confirmed by Google's [generateContent reference](https://ai.google.dev/api/generate-content):

```json
{
  "contents": [{
    "role": "user",
    "parts": [
      {"text": "Approved instruction preserving the supplied product."},
      {"inline_data": {"mime_type": "image/png", "data": "BASE64_PRODUCT_PHOTO"}}
    ]
  }],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {"aspectRatio": "1:1"}
  }
}
```

JPEG, PNG, and WebP are accepted. Inline references are capped at 14 MiB combined to leave space for base64 expansion and prompts. Confirm the chosen model's reference count and dimension limits before approving production. Optional `imageConfig.imageSize` accepts `512`, `1K`, `2K`, or `4K` under Google's contract; model support and price must be checked before selecting larger outputs. Response parsing accepts both `inline_data.mime_type` and `inlineData.mimeType`, validates base64 and file signatures, and rejects text-only output. Full decoding, dimensions, OCR, product fidelity, and visual review remain mandatory in the studio quality workflow; a signature check alone is insufficient.

## Video evidence and limitations

The [AIsa Wan 2.7 model page](https://aisa.one/models/wan2.7-i2v) documents `content[]` containing text and HTTPS `image_url` objects with `role:"reference_image"`, plus `duration`, `ratio`, and `generate_audio`. The adapter sends those fields and defaults to five seconds without generated audio. It requires the catalog to advertise both submission and task-status routes.

**Contract gap:** AIsa's downloaded OpenAPI omitted video generation and image edits. Its Wan example uses a shared multimedia shape, while [Alibaba's upstream Wan 2.7 contract](https://www.alibabacloud.com/help/en/model-studio/image-to-video-general-api-reference) uses `input.media` and describes aspect ratio following the first frame. The adapter follows AIsa's published gateway example; it must remain experimental until an authorized reference-conditioned live call confirms gateway translation, portrait/square ratios, response envelope, and output quality. AIsa's example demonstrates 16:9; portrait and square are request options, not verified capability claims. Upstream duration is 2–15 seconds; gateway availability and cost still require confirmation.

Video references require user-accessible HTTPS URLs. The studio verifies that a remote reference matches the inspected local photo before sending it. No upload endpoint, local file URL, or video data-URI support is invented. No text-to-video fallback is allowed. Output URLs may expire; download promptly and preserve the job ID for recovery.

## Failure behavior and unsupported adapters

Production responses preserve allowlisted request IDs and valid `X-AISA-Customer-Cost-Micros-USD` headers in generation receipts. Jobs and exported manifests distinguish known settled micro-USD from unknown costs; missing or invalid cost headers are never treated as free. Estimates remain separate from settled charges.

If a successful synchronous response cannot be written to its cache file, its recovery data is retained in the job ledger when possible. `resume` restores that cache and processes the original result without another paid POST. If no response can be persisted, reconcile the job rather than blindly retrying.

Requests have a body-inclusive deadline, a 96 MiB response limit, and disabled redirects. Authentication only goes to `api.aisa.one`; provider error bodies are not printed. Network/timeout failures after POST are ambiguous and are never automatically retried. `AisaError.taskId`, when present, preserves a recoverable video job identifier even when submission parsing fails. HTTP/auth errors stop immediately. A finished video without a usable URL fails validation.

Seedream image editing, Wan image editing, masks, dedicated image uploads, additional video models, and automatic model fallback are **not implemented**. Add one only after checking its complete request contract, reference conditioning, current route, pricing, and response handling. Do not treat an “Edit” catalog badge as a schema or claim that the untested model is production ready.
