---
name: openclaw-media-gen
description: 'Generate images and videos with AIsa. Four image models (Google Gemini 3 Pro Image, Alibaba Wan 2.7 image + image-pro, ByteDance Seedream) and four Wan video variants (wan2.6/2.7 × t2v/i2v). One API key; the client routes each model to the correct endpoint automatically. Use when: the user needs AI image or video generation workflows.'
license: MIT
compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, curl, environment variables AISA_API_KEY and internet access to api.aisa.one.
metadata:
  aisa:
    emoji: 🎬
    requires:
      bins:
      - python3
      - curl
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    compatibility: Designed for Agent Skills compatible clients such as OpenClaw, Claude Code, Hermes, and GitHub-backed skill catalogs. Requires system binaries python3, curl, environment variables AISA_API_KEY and internet access to api.aisa.one.
---

# OpenClaw Media Gen 🎬

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
python3 scripts/media_gen_client.py image \
  --model gemini-3-pro-image-preview \
  --prompt "A cute red panda, cinematic lighting" \
  --out out.png

python3 scripts/media_gen_client.py image \
  --model wan2.7-image-pro \
  --prompt "Ultra-detailed product shot of a red panda" \
  --out out.png

python3 scripts/media_gen_client.py image \
  --model seedream-4-5-251128 \
  --prompt "Neo-noir detective portrait, film grain" \
  --size 2048x2048 \
  --out out.png

# Video — text-to-video (no image needed)
python3 scripts/media_gen_client.py video-create \
  --model wan2.7-t2v \
  --prompt "Sweeping shot of a neon cyberpunk skyline"

# Video — image-to-video on wan2.7-i2v (client routes to input.media[])
python3 scripts/media_gen_client.py video-create \
  --model wan2.7-i2v \
  --prompt "gentle zoom with parallax" \
  --img-url "https://example.com/reference.jpg" \
  --duration 5

# Wait and download
python3 scripts/media_gen_client.py video-wait \
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
python3 scripts/media_gen_client.py image \
  --model <gemini-3-pro-image-preview | wan2.7-image | wan2.7-image-pro | seedream-4-5-251128> \
  --prompt "..." \
  --out out.png

# Video — create task
python3 scripts/media_gen_client.py video-create \
  --model <wan2.6-t2v | wan2.6-i2v | wan2.7-t2v | wan2.7-i2v> \
  --prompt "..." \
  [--img-url https://... (required for -i2v models)] \
  [--duration 5|10] \
  [--resolution 720P|1080P]

# Video — poll / wait / download
python3 scripts/media_gen_client.py video-status --task-id <id>
python3 scripts/media_gen_client.py video-wait --task-id <id> --poll 10 --timeout 600
python3 scripts/media_gen_client.py video-wait --task-id <id> --download --out out.mp4
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
