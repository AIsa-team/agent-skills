---
name: media-gen
description: "Generate images & videos with AIsa. Gemini 3 Pro Image (image) + Qwen Wan 2.6 (video) via one API key."
license: MIT
compatibility: "Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3, a POSIX shell, and AISA_API_KEY."
metadata: {"aisa": {"emoji": "🎬", "homepage": "https://aisa.one", "requires": {"bins": ["python3", "curl"], "env": ["AISA_API_KEY"]}, "primaryEnv": "AISA_API_KEY", "harnesses": ["claude-code", "claude", "opencode", "cursor", "codex", "gemini-cli", "openclaw", "hermes", "goose"]}}
---
# Media Gen 🎬

Generate **images** and **videos** with a single AIsa API key:

- **Image**: `gemini-3-pro-image-preview` (Gemini GenerateContent)
- **Video**: `wan2.6-t2v` (Qwen Wan 2.6, async task)

API documentation index: [AIsa API Reference](https://aisa.one/docs/api-reference/) (all pages can be found at `https://aisa.one/docs/llms.txt`).

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

### Image Generation (Gemini)
```
"Generate a cyberpunk-style city nightscape with neon lights, rainy night, cinematic feel"
```

### Video Generation (Wan 2.6)
```
"Generate a 5-second shot from a reference image: slow camera push-in, wind blowing through hair, cinematic feel, shallow depth of field"
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

---

## 🖼️ Image Generation (Gemini)

### Endpoint

- Base URL: `https://api.aisa.one/v1`
- `POST /models/{model}:generateContent`

Documentation: `google-gemini-chat` (GenerateContent) at `https://aisa.one/docs/api-reference/chat/generatecontent`.

### curl Example (response contains inline_data for images)

```bash
curl -X POST "https://api.aisa.one/v1/models/gemini-3-pro-image-preview:generateContent" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents":[
      {"role":"user","parts":[{"text":"A cute red panda, ultra-detailed, cinematic lighting"}]}
    ]
  }'
```

> Note: The response from this endpoint may include `candidates[].parts[].inline_data` (typically containing base64 data and a MIME type); the client script will automatically parse and save the file.

---

## 🎞️ Video Generation (Qwen Wan 2.6 / Tongyi Wanxiang)

### Create task

- Base URL: `https://api.aisa.one/apis/v1`
- `POST /services/aigc/video-generation/video-synthesis`
- Header: `X-DashScope-Async: enable` (required, async)

Documentation: `video-generation` at `https://aisa.one/docs/api-reference/video/post_services-aigc-video-generation-video-synthesis`.

```bash
curl -X POST "https://api.aisa.one/apis/v1/services/aigc/video-generation/video-synthesis" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-DashScope-Async: enable" \
  -d '{
    "model":"wan2.6-t2v",
    "input":{
      "prompt":"cinematic close-up, slow push-in, shallow depth of field",
      "img_url":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg"
    },
    "parameters":{
      "resolution":"720P",
      "duration":5,
      "shot_type":"single",
      "watermark":false
    }
  }'
```

### Poll task

- `GET /services/aigc/tasks/{task_id}` — `task_id` is a **path parameter**. The query-string form `?task_id=...` returns HTTP 500 `unsupported uri`.

Documentation: [Get video generation task result](https://aisa.one/docs/api-reference/video/get_services-aigc-tasks).

```bash
curl "https://api.aisa.one/apis/v1/services/aigc/tasks/YOUR_TASK_ID" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

---

## Python Client

```bash
# Generate image (save to local file)
python3 {baseDir}/scripts/media_gen_client.py image \
  --prompt "A cute red panda, cinematic lighting" \
  --out "out.png"

# Create video task (requires img_url)
python3 {baseDir}/scripts/media_gen_client.py video-create \
  --prompt "cinematic close-up, slow push-in" \
  --img-url "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/320px-Cat03.jpg" \
  --duration 5

# Poll task status
python3 {baseDir}/scripts/media_gen_client.py video-status --task-id YOUR_TASK_ID

# Wait until success (optional: print video_url on success)
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id YOUR_TASK_ID --poll 10 --timeout 600

# Wait until success and auto-download mp4
python3 {baseDir}/scripts/media_gen_client.py video-wait --task-id YOUR_TASK_ID --download --out out.mp4
```
