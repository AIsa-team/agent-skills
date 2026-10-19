# Media Gen 🎬

> **DEPRECATED (2026-10-20).** This skill's bundled client (`scripts/media_gen_client.py`) and the examples below target routes that are no longer in the published AIsa contract (https://aisa.one/openapi.json): `POST /v1/models/{model}:generateContent` (Gemini GenerateContent is served under `https://api.aisa.one/v1beta`), `POST /apis/v1/services/aigc/video-generation/video-synthesis` and `GET /apis/v1/services/aigc/tasks/{task_id}` (the model guide documents `POST /v1/video/generations` and `GET /v1/video/generations/{task_id}` instead). The listed model IDs may also be retired. Do not run this skill as-is: list the current image and video models with `GET /v1/models` (free) and call the route in each model's `aisa.routes`, following https://aisa.one/docs/guides/models. The skill stays in the catalog until its owner rewrites the client against the current contract; its stale routes are reported as warnings by `scripts/validate_skills.py`.

**Generate images and videos with a single AIsa API key.** Covers every
image and video model AIsa currently exposes, across three different
endpoint paths.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: **Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**,
**Gemini CLI**, **OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and
others that implement the
[Agent Skills specification](https://agentskills.io/specification).

Requires Python 3, a POSIX shell, and `AISA_API_KEY`.

## Supported models

### Image (4 models across 3 endpoints)

- `gemini-3-pro-image-preview` (Google) — via `POST /v1/models/{model}:generateContent`
- `wan2.7-image`, `wan2.7-image-pro` (Alibaba) — via `POST /v1/chat/completions`
- `seedream-4-5-251128` (ByteDance) — via `POST /v1/images/generations` (OpenAI-compatible; minimum 3,686,400 pixels)

### Video (4 Wan variants, 1 async endpoint)

- `wan2.6-t2v`, `wan2.7-t2v` — text-to-video
- `wan2.6-i2v` — image-to-video (uses `input.img_url`)
- `wan2.7-i2v` — image-to-video (uses `input.media[]` — different field name, the client handles it)

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

### Generate an image (any model)

```bash
# Gemini
python scripts/media_gen_client.py image \
  --model gemini-3-pro-image-preview \
  --prompt "A cute red panda, cinematic lighting" \
  --out out.png

# Wan 2.7 (pro = higher fidelity)
python scripts/media_gen_client.py image \
  --model wan2.7-image-pro \
  --prompt "Ultra-detailed product shot, studio lighting" \
  --out out.png

# Seedream (needs ≥ 3,686,400 px)
python scripts/media_gen_client.py image \
  --model seedream-4-5-251128 \
  --prompt "Neo-noir detective portrait" \
  --size 2048x2048 \
  --out out.png
```

### Generate a video

```bash
# Text-to-video
python scripts/media_gen_client.py video-create \
  --model wan2.7-t2v \
  --prompt "Sweeping shot of a neon cyberpunk skyline"

# Image-to-video (client routes --img-url into the right field per model)
python scripts/media_gen_client.py video-create \
  --model wan2.7-i2v \
  --prompt "gentle camera push-in" \
  --img-url "https://example.com/reference.jpg" \
  --duration 5
```

### Poll the task and download

```bash
python scripts/media_gen_client.py video-status --task-id <task_id>

python scripts/media_gen_client.py video-wait \
  --task-id <task_id> --poll 10 --timeout 600

python scripts/media_gen_client.py video-wait \
  --task-id <task_id> --download --out out.mp4
```

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.
