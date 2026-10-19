---
name: media-gen
description: Generate images and videos with AIsa. Four image models (Google Gemini 3 Pro Image, Alibaba Wan 2.7 image + image-pro, ByteDance Seedream) and four Wan video variants (wan2.6/2.7 × t2v/i2v). One API key; the client routes each model to the correct endpoint automatically.
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY.
metadata:
  version: "1.0.1"
  aisa:
    emoji: 🎬
    homepage: https://aisa.one
    requires:
      bins:
      - python3
      - curl
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---
# Media Gen 🎬

<!-- aisa-rules:start -->
## AIsa agent rules (shared)

<!-- Generated from _shared/aisa-rules.md by scripts/sync_shared_rules.py. Do not edit this block in place. -->

These rules apply to every AIsa-backed skill and are copied from https://aisa.one/llms.txt, the single authoritative agent rule source. When this block and the rest of this skill disagree, follow this block.

### Connect (MCP first)

Pick the first option that applies. Run the command yourself; the user only approves the browser sign-in.

- **A. Your client supports remote MCP and can open a browser (default).** Add a remote MCP server named `AIsa` with URL `https://mcp.aisa.one/mcp` (Streamable HTTP), using your client's own command or config file. Auth: browser OAuth, no key needed. In a chat app (Claude, ChatGPT), the user adds it as a custom connector in settings. If you cannot add the connector yourself (sandbox, permission denied), give the user the server name and URL above and wait. Do not fall back to another method.
- **B. Your client supports remote MCP but has no browser (CI, SSH, container).** Same endpoint, with the header `Authorization: Bearer $AISA_API_KEY` set in your client's MCP config instead of browser sign-in. If `AISA_API_KEY` is not set, ask the user to create a key at https://console.aisa.one/api-keys and set it in the environment; never ask them to paste it into chat. Never print, log, or commit the key.
- **C. The client has no MCP support.** Use the CLI: `npm install -g @aisa-one/cli && aisa login` (Node.js 18+). Guide: https://aisa.one/docs/get-started/cli.md
- **D. Calling AIsa over HTTP from your own code.** LLMs, OpenAI-compatible: `https://api.aisa.one/v1` (Gemini GenerateContent: `https://api.aisa.one/v1beta`). Data APIs: `https://api.aisa.one/apis/v1`. Auth: `Authorization: Bearer $AISA_API_KEY`. Exact paths and schemas: https://aisa.one/docs/api-reference

Direct HTTP (D) is a gated fallback, not the default. Gate (https://aisa.one/docs/get-started/cli.md#direct-http-fallback): "CLI and MCP are both unavailable, HTTP requests are supported, and a valid existing AIsa API key is already available." The curl and script examples in this skill exist for that fallback; when a connection exists, run the same operation through MCP (`search` → `batch_get_schema` → `batch_quote` → `batch_use`) or the CLI (`aisa search` → `aisa schema` → `aisa quote` → `aisa call`). Take tool names and arguments from `search` or `batch_get_schema`. Never invent them.

### Verify

Make one free authenticated call on the interface you connected:

- MCP (A, B): call `account` (no arguments). If it is not in the tool list, call `use` with `{"operation_id": "account"}` instead. Returns the key, balance, and usage.
- CLI (C): `aisa balance`. (`aisa whoami` is local only and does not count.)
- HTTP (D): `GET https://api.aisa.one/v1/models` with the Bearer header returns 200.

AIsa is connected only when this call succeeds. A tool list or a 401 response does not count.

### Spending (approval before paid calls)

- Free: docs, `GET /v1/models`, MCP `search`, `list_categories`, `batch_get_schema`, `batch_quote`, `account`, and CLI `aisa search`, `aisa schema`, `aisa quote`, `aisa balance`.
- Quote the exact calls before running them: MCP `batch_quote`, CLI `aisa quote --json`. Run only what you quoted; re-quote if the tools or arguments change. Neither `batch_use` nor `aisa call` takes a price cap.
- If the quote reports `auto_execute_eligible: true` (a small total), run it without asking, unless the user set a tighter limit or asked only for a quote.
- Otherwise, before the first such call, tell the user in one message what you plan to call, the quoted price, and a total budget for the task in USD. Wait for approval, then run calls within that budget without asking again. Ask again only if the task changes or the next call would exceed the remaining budget.
- For operations billed by rows or credits, also set the operation's own limit (for example `limit`) so the cost stays bounded.
- Do not retry a failed paid call without telling the user.
- Direct HTTP (D) follows the stricter rule at https://aisa.one/docs/get-started/cli.md#direct-http-fallback: read the endpoint's reference and published pricing first; state the exact endpoint and scope, formula or rate, and documented maximum USD exposure; then wait for a separate user message explicitly approving that scope and cap. Do not make paid calls to test availability. Docs, `/v1/models`, and capability or MCP discovery are allowed before approval.

### Cost accounting

The settled cost of a direct HTTP call is reported by the response header `X-AISA-Customer-Cost-Micros-USD` (integer micro-USD; 1 USD = 1,000,000 micro-USD), or by a successful native Tool result's `customer_cost_micros_usd`. Missing cost metadata means unknown, not free. Response bodies do not carry `usage.cost` or `usage.credits_remaining`; do not report those fields as the charge. Reference: https://aisa.one/docs/guides/pricing

### Errors

- `401`: not signed in or invalid key. Redo Connect option A (step 1A in llms.txt) or check the key.
- `402`: low balance, or the operation requires the Go-to-Market plan. The response says which and where to resolve it. Tell the user which one it is (top up the balance, or subscribe to the plan) with the link from the response; do not retry.
- `429`: rate limited. Wait and retry with backoff. Details: https://aisa.one/docs/api-reference/rate-limits
<!-- aisa-rules:end -->

**Generate images and videos with a single AIsa API key.** Full support
for every image and video model AIsa routes through its Unified LLM
Gateway, across three different endpoint paths.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills
  specification](https://agentskills.io/specification)

Requires Python 3, a POSIX shell, and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## 🔥 What You Can Do

### Image — Gemini (base64 inline)
```text
"Generate a cyberpunk-style city nightscape, neon lights, rainy night, cinematic feel"
```

### Image — Wan 2.7 (URL in chat response)
```text
"Generate an ultra-detailed product shot of a red panda, studio lighting, sharp focus"
```

### Image — Seedream (OpenAI-compatible, large format)
```text
"Generate a 2048×2048 magazine cover: neo-noir detective portrait, film grain"
```

### Video — text-to-video (Wan t2v)
```text
"Sweeping establishing shot of a neon cyberpunk skyline at dusk, 5 seconds"
```

### Video — image-to-video (Wan i2v)
```text
"Starting from this reference image, gentle camera push-in with parallax"
```

## Supported Models

### Image generation — 4 models, 3 endpoints

| Model | Developer | Endpoint | Notes |
|---|---|---|---|
| `gemini-3-pro-image-preview` | Google | `POST /v1/models/{model}:generateContent` | Images returned as base64 in `candidates[].parts[].inline_data` |
| `wan2.7-image` | Alibaba | `POST /v1/chat/completions` | Images returned as URL parts in `choices[].message.content[]` (type=`image`). $0.030/image |
| `wan2.7-image-pro` | Alibaba | `POST /v1/chat/completions` | Higher fidelity. $0.075/image |
| `seedream-4-5-251128` | ByteDance | `POST /v1/images/generations` | OpenAI-compatible. **Minimum 3,686,400 pixels** (e.g. 1920×1920). $0.040/image |

### Video generation — 4 Wan variants, 1 endpoint

| Model | Kind | Image field | Output SR |
|---|---|---|---|
| `wan2.6-t2v` | text-to-video | *none* | 1080 |
| `wan2.6-i2v` | image-to-video | `input.img_url` (string) | 720 |
| `wan2.7-t2v` | text-to-video | *none* | 720 |
| `wan2.7-i2v` | image-to-video | **`input.media`** (array) ⚠ | 720 |

> ⚠ **Schema trap on `wan2.7-i2v`.** It takes the reference image in
> `input.media` (array of URLs), **not** `input.img_url` like
> `wan2.6-i2v`. Submissions without `media` return HTTP 200 with a
> `task_id`, then fail downstream with `InvalidParameter: Field required:
> input.media`. The bundled client routes this automatically — just
> pass `--img-url` and pick the model.

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Any image model — client routes to the right endpoint
python3 {baseDir}/scripts/media_gen_client.py image \
  --model gemini-3-pro-image-preview \
  --prompt "A cute red panda, cinematic lighting" \
  --out out.png

python3 {baseDir}/scripts/media_gen_client.py image \
  --model wan2.7-image-pro \
  --prompt "Ultra-detailed product shot of a red panda" \
  --out out.png

python3 {baseDir}/scripts/media_gen_client.py image \
  --model seedream-4-5-251128 \
  --prompt "Neo-noir detective portrait, film grain" \
  --size 2048x2048 \
  --out out.png

# Video — text-to-video (no image needed)
python3 {baseDir}/scripts/media_gen_client.py video-create \
  --model wan2.7-t2v \
  --prompt "Sweeping shot of a neon cyberpunk skyline"

# Video — image-to-video on wan2.7-i2v (client routes to input.media[])
python3 {baseDir}/scripts/media_gen_client.py video-create \
  --model wan2.7-i2v \
  --prompt "gentle zoom with parallax" \
  --img-url "https://example.com/reference.jpg" \
  --duration 5

# Wait and download
python3 {baseDir}/scripts/media_gen_client.py video-wait \
  --task-id <task_id> --download --out out.mp4
```

---

## 🖼️ Image Generation — endpoint reference

### Gemini family → `POST /v1/models/{model}:generateContent`

Documentation: [Google Gemini Chat](https://aisa.one/docs/api-reference/chat/generatecontent).

```bash
curl -X POST "https://api.aisa.one/v1/models/gemini-3-pro-image-preview:generateContent" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents":[
      {"role":"user","parts":[{"text":"A cute red panda, cinematic lighting"}]}
    ]
  }'
```

Response contains `candidates[].parts[].inline_data` with `{mime_type, data}`
where `data` is a base64 PNG.

### Wan 2.7 family → `POST /v1/chat/completions`

Documentation: [Image Generation via Chat](https://aisa.one/docs/api-reference/chat/image-generation).

**Critical rule:** `messages[].content` must be an **array of typed parts**.
A plain string returns HTTP 400 `invalid_parameter_error`.

```bash
curl -X POST "https://api.aisa.one/v1/chat/completions" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "wan2.7-image",
    "messages": [
      {"role":"user","content":[
        {"type":"text","text":"A cute red panda, ultra-detailed, cinematic lighting"}
      ]}
    ],
    "n": 1
  }'
```

Images come back as `{type: "image", image: "<url>"}` parts inside
`choices[].message.content[]`.

### Seedream → `POST /v1/images/generations`

Documentation: [OpenAI-Compatible Image Generations](https://aisa.one/docs/api-reference/chat/openai-image-generations).

```bash
curl -X POST "https://api.aisa.one/v1/images/generations" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "seedream-4-5-251128",
    "prompt": "A cute red panda, ultra-detailed, cinematic lighting",
    "n": 1,
    "size": "2048x2048"
  }'
```

Response: `data[].url` or `data[].b64_json`. **Upstream enforces a
minimum of 3,686,400 pixels.** `1024×1024` and `1536×1536` get rejected.
Any aspect ratio works as long as `width × height ≥ 3,686,400`.

---

## 🎞️ Video Generation — endpoint reference

### Create task → `POST /apis/v1/services/aigc/video-generation/video-synthesis`

Documentation: [Create video generation task](https://aisa.one/docs/api-reference/video/post_services-aigc-video-generation-video-synthesis).
Header `X-DashScope-Async: enable` is required.

```bash
# wan2.6-t2v — text-to-video
curl -X POST "https://api.aisa.one/apis/v1/services/aigc/video-generation/video-synthesis" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-DashScope-Async: enable" \
  -d '{
    "model":"wan2.6-t2v",
    "input":{"prompt":"cinematic close-up, slow push-in"},
    "parameters":{"resolution":"720P","duration":5}
  }'

# wan2.7-i2v — image-to-video (⚠ input.media not input.img_url)
curl -X POST "https://api.aisa.one/apis/v1/services/aigc/video-generation/video-synthesis" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-DashScope-Async: enable" \
  -d '{
    "model":"wan2.7-i2v",
    "input":{
      "prompt":"gentle zoom with parallax",
      "media":["https://example.com/reference.jpg"]
    },
    "parameters":{"resolution":"720P","duration":5}
  }'
```

### Poll task → `GET /apis/v1/services/aigc/tasks/{task_id}`

Documentation: [Get video generation task result](https://aisa.one/docs/api-reference/video/get_services-aigc-tasks).

> `task_id` is a **path parameter**. The query-string form
> `?task_id=...` returns HTTP 500 `unsupported uri`.

```bash
curl "https://api.aisa.one/apis/v1/services/aigc/tasks/YOUR_TASK_ID" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Python Client

The bundled client at `scripts/media_gen_client.py` auto-routes each
image model to the correct endpoint and normalizes the response to a
saved file.

```bash
# Image — model picks the endpoint
python3 {baseDir}/scripts/media_gen_client.py image \
  --model <gemini-3-pro-image-preview | wan2.7-image | wan2.7-image-pro | seedream-4-5-251128> \
  --prompt "..." \
  --out out.png

# Video — create task
python3 {baseDir}/scripts/media_gen_client.py video-create \
  --model <wan2.6-t2v | wan2.6-i2v | wan2.7-t2v | wan2.7-i2v> \
  --prompt "..." \
  [--img-url https://... (required for -i2v models)] \
  [--duration 5|10] \
  [--resolution 720P|1080P]

# Video — poll / wait / download
python3 {baseDir}/scripts/media_gen_client.py video-status --task-id <id>
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id <id> --poll 10 --timeout 600
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id <id> --download --out out.mp4
```

## API Reference

This skill calls the following AIsa endpoints directly:

- [Google Gemini Chat — `generateContent`](https://aisa.one/docs/api-reference/chat/generatecontent) — Gemini image models
- [Image Generation via Chat](https://aisa.one/docs/api-reference/chat/image-generation) — Wan 2.7 image family
- [OpenAI-Compatible Image Generations](https://aisa.one/docs/api-reference/chat/openai-image-generations) — Seedream
- [Create video generation task](https://aisa.one/docs/api-reference/video/post_services-aigc-video-generation-video-synthesis) — all 4 Wan video variants
- [Get video generation task result](https://aisa.one/docs/api-reference/video/get_services-aigc-tasks) — async polling

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
