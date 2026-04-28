#!/usr/bin/env python3
"""
Media Gen — AIsa API Client.

Image generation (3 endpoint paths, routed by model):

  gemini-3-pro-image-preview
      POST https://api.aisa.one/v1/models/{model}:generateContent
      Gemini GenerateContent; images arrive as base64 in candidates[].parts[].inline_data.

  wan2.7-image, wan2.7-image-pro
      POST https://api.aisa.one/v1/chat/completions
      Multimodal chat; images arrive as URLs in choices[].message.content[] parts
      where part.type == "image".

  seedream-4-5-251128
      POST https://api.aisa.one/v1/images/generations
      OpenAI-compatible image endpoint; images arrive in data[].url or data[].b64_json.
      Min image size enforced upstream: 3,686,400 pixels (e.g. 1920x1920).

Video generation (async task, single endpoint, 4 model variants):

  POST https://api.aisa.one/apis/v1/services/aigc/video-generation/video-synthesis
  GET  https://api.aisa.one/apis/v1/services/aigc/tasks/{task_id}

  wan2.6-t2v                     text-to-video (1080 SR)
  wan2.6-i2v  input.img_url      image-to-video (720 SR)
  wan2.7-t2v                     text-to-video (720 SR)
  wan2.7-i2v  input.media[]      image-to-video (720 SR) — NB different image field
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


GEMINI_BASE_URL = "https://api.aisa.one/v1"
VIDEO_BASE_URL = "https://api.aisa.one/apis/v1"

# Image-generation model routing. Any model not in these sets falls back
# to the --endpoint auto-detection in route_image_call().
IMAGE_MODELS_GEMINI = {"gemini-3-pro-image-preview"}
IMAGE_MODELS_WAN_CHAT = {"wan2.7-image", "wan2.7-image-pro"}
IMAGE_MODELS_SEEDREAM = {"seedream-4-5-251128"}

# Video models — determines how the image field is named (if any).
VIDEO_MODELS_T2V = {"wan2.6-t2v", "wan2.7-t2v"}
VIDEO_MODELS_I2V_IMG_URL = {"wan2.6-i2v"}       # input.img_url
VIDEO_MODELS_I2V_MEDIA = {"wan2.7-i2v"}         # input.media (array)


def _get_api_key(explicit: Optional[str] = None) -> str:
    api_key = explicit or os.environ.get("AISA_API_KEY")
    if not api_key:
        raise ValueError("AISA_API_KEY is required (env or --api-key).")
    return api_key


def _http_request_json(
    *,
    method: str,
    url: str,
    api_key: str,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout_s: int = 60,
    user_agent: str = "AIsa-Media-Gen/1.0",
) -> Dict[str, Any]:
    all_headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": user_agent,
    }
    if headers:
        all_headers.update(headers)

    data: Optional[bytes] = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        all_headers.setdefault("Content-Type", "application/json")
    elif method.upper() in {"POST", "PUT", "PATCH"}:
        data = b"{}"
        all_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=all_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"success": False, "error": {"code": str(e.code), "message": raw}}
    except urllib.error.URLError as e:
        return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(getattr(e, "reason", e))}}


def _safe_filename(ext: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"media-gen-{ts}.{ext.lstrip('.')}"


def _download_to_file(url: str, out_path: str, timeout_s: int = 300) -> Dict[str, Any]:
    """
    Download a (possibly signed) URL to local file.
    Designed for OSS signed URLs returned by video generation tasks.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "AIsa-Media-Gen/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp, open(out_path, "wb") as f:
            total = 0
            while True:
                chunk = resp.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        return {"success": True, "saved_to": out_path, "bytes": total}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url, "saved_to": out_path}


def _extract_gemini_inline_images(resp: Dict[str, Any]) -> List[Tuple[str, bytes]]:
    """
    Returns a list of (mime_type, bytes) from Gemini candidates parts.
    Tries to be tolerant to schema variations.
    """
    out: List[Tuple[str, bytes]] = []
    candidates = resp.get("candidates") or []
    for cand in candidates:
        parts = cand.get("parts") or cand.get("content", {}).get("parts") or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline = part.get("inline_data") or part.get("inlineData")
            if not inline or not isinstance(inline, dict):
                continue
            mime = inline.get("mime_type") or inline.get("mimeType") or "application/octet-stream"
            data_b64 = inline.get("data")
            if not data_b64 or not isinstance(data_b64, str):
                continue
            try:
                out.append((mime, base64.b64decode(data_b64)))
            except Exception:
                continue
    return out


def _extract_gemini_text(resp: Dict[str, Any]) -> str:
    candidates = resp.get("candidates") or []
    texts: List[str] = []
    for cand in candidates:
        parts = cand.get("parts") or cand.get("content", {}).get("parts") or []
        for part in parts:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return "\n".join(texts).strip()


def gemini_generate_image(*, api_key: str, model: str, prompt: str) -> Dict[str, Any]:
    """POST /v1/models/{model}:generateContent — Gemini image models."""
    model_id = model[len("models/") :] if model.startswith("models/") else model
    url = f"{GEMINI_BASE_URL}/models/{urllib.parse.quote(model_id, safe='')}:generateContent"
    body = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]},
        ]
    }
    return _http_request_json(method="POST", url=url, api_key=api_key, body=body, timeout_s=90)


def wan_chat_generate_image(
    *,
    api_key: str,
    model: str,
    prompt: str,
    n: int = 1,
) -> Dict[str, Any]:
    """POST /v1/chat/completions — Wan 2.7 image models (wan2.7-image, wan2.7-image-pro).

    Schema rule: messages[].content MUST be an array of typed parts. Passing
    a plain string returns HTTP 400 invalid_parameter_error.
    """
    url = f"{GEMINI_BASE_URL}/chat/completions"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "n": n,
    }
    return _http_request_json(method="POST", url=url, api_key=api_key, body=body, timeout_s=120)


def seedream_generate_image(
    *,
    api_key: str,
    model: str,
    prompt: str,
    n: int = 1,
    size: str = "2048x2048",
) -> Dict[str, Any]:
    """POST /v1/images/generations — ByteDance Seedream.

    Upstream enforces a minimum of 3,686,400 pixels. Defaults to 2048x2048
    to stay above the threshold. Requests smaller than ~1920x1920 return
    HTTP 400 InvalidParameter.
    """
    url = f"{GEMINI_BASE_URL}/images/generations"
    body = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
    }
    return _http_request_json(method="POST", url=url, api_key=api_key, body=body, timeout_s=120)


def route_image_call(
    *,
    api_key: str,
    model: str,
    prompt: str,
    n: int,
    size: Optional[str],
) -> Tuple[str, Dict[str, Any]]:
    """Dispatch to the correct endpoint based on model. Returns (route, response)."""
    if model in IMAGE_MODELS_GEMINI or model.startswith("gemini-"):
        return "gemini", gemini_generate_image(api_key=api_key, model=model, prompt=prompt)
    if model in IMAGE_MODELS_WAN_CHAT or model.startswith("wan2.7-image"):
        return "wan-chat", wan_chat_generate_image(api_key=api_key, model=model, prompt=prompt, n=n)
    if model in IMAGE_MODELS_SEEDREAM or model.startswith("seedream"):
        return "seedream", seedream_generate_image(
            api_key=api_key, model=model, prompt=prompt, n=n,
            size=size or "2048x2048",
        )
    # Unknown — default to Gemini path but surface the uncertainty.
    return "gemini-default", gemini_generate_image(api_key=api_key, model=model, prompt=prompt)


def _extract_wan_chat_image_urls(resp: Dict[str, Any]) -> List[str]:
    """Pull image URLs from a /v1/chat/completions response for Wan 2.7 image models.

    Images come back as parts with type='image' containing an 'image' field
    whose value is a URL (or sometimes a dict with {"url": ...}).
    """
    urls: List[str] = []
    for choice in resp.get("choices", []) or []:
        msg = choice.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") != "image":
                continue
            img = part.get("image") or part.get("image_url")
            if isinstance(img, str):
                urls.append(img)
            elif isinstance(img, dict) and isinstance(img.get("url"), str):
                urls.append(img["url"])
    return urls


def _extract_seedream_images(resp: Dict[str, Any]) -> List[Tuple[str, Optional[bytes], Optional[str]]]:
    """Pull images from a /v1/images/generations response.

    Returns a list of (kind, bytes_if_b64, url_if_any). kind is 'b64' or 'url'.
    """
    out: List[Tuple[str, Optional[bytes], Optional[str]]] = []
    for item in resp.get("data", []) or []:
        if not isinstance(item, dict):
            continue
        b64 = item.get("b64_json")
        url = item.get("url")
        if isinstance(b64, str):
            try:
                out.append(("b64", base64.b64decode(b64), None))
                continue
            except Exception:
                pass
        if isinstance(url, str):
            out.append(("url", None, url))
    return out


def video_create_task(
    *,
    api_key: str,
    model: str,
    prompt: str,
    img_url: Optional[str],
    negative_prompt: Optional[str],
    resolution: str,
    duration: int,
    shot_type: str,
    watermark: bool,
    seed: Optional[int],
) -> Dict[str, Any]:
    """POST /apis/v1/services/aigc/video-generation/video-synthesis.

    Routes the image field based on the model:
      - wan2.6-t2v, wan2.7-t2v:  no image field (text-to-video)
      - wan2.6-i2v:              input.img_url (single URL string)
      - wan2.7-i2v:              input.media   (array of URL strings)

    Missing input.media on wan2.7-i2v silently returns a task_id but the
    task then fails downstream with 'Field required: input.media'.
    """
    url = f"{VIDEO_BASE_URL}/services/aigc/video-generation/video-synthesis"
    headers = {"X-DashScope-Async": "enable"}
    body: Dict[str, Any] = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "resolution": resolution,
            "duration": duration,
            "shot_type": shot_type,
            "watermark": watermark,
        },
    }

    if model in VIDEO_MODELS_I2V_MEDIA:
        if not img_url:
            return {"success": False, "error": f"{model} requires --img-url (goes into input.media)"}
        body["input"]["media"] = [img_url]
    elif model in VIDEO_MODELS_I2V_IMG_URL:
        if not img_url:
            return {"success": False, "error": f"{model} requires --img-url"}
        body["input"]["img_url"] = img_url
    elif model in VIDEO_MODELS_T2V:
        # Text-to-video: ignore --img-url if supplied; silently allow it.
        pass
    else:
        # Unknown model — pass-through; user is on their own.
        if img_url:
            body["input"]["img_url"] = img_url

    if negative_prompt:
        body["input"]["negative_prompt"] = negative_prompt
    if seed is not None:
        body["parameters"]["seed"] = seed
    return _http_request_json(method="POST", url=url, api_key=api_key, headers=headers, body=body, timeout_s=90)


def video_task_status(*, api_key: str, task_id: str) -> Dict[str, Any]:
    # task_id is a PATH parameter, not a query string. The query-string form
    # returns HTTP 500 "unsupported uri".
    safe_id = urllib.parse.quote(task_id, safe="")
    url = f"{VIDEO_BASE_URL}/services/aigc/tasks/{safe_id}"
    return _http_request_json(method="GET", url=url, api_key=api_key, timeout_s=60)


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _ext_from_mime(mime: str) -> str:
    m = (mime or "").lower()
    if "jpeg" in m or "jpg" in m:
        return "jpg"
    if "webp" in m:
        return "webp"
    if "gif" in m:
        return "gif"
    return "png"


def cmd_image(args: argparse.Namespace) -> int:
    api_key = _get_api_key(args.api_key)
    route, resp = route_image_call(
        api_key=api_key,
        model=args.model,
        prompt=args.prompt,
        n=getattr(args, "n", 1),
        size=getattr(args, "size", None),
    )

    # Each route yields a different response shape; unify to (saved_path, detail).
    if route in {"gemini", "gemini-default"}:
        images = _extract_gemini_inline_images(resp)
        if not images:
            text = _extract_gemini_text(resp)
            _print_json({"success": False, "route": route, "error": "No inline image data returned",
                         **({"text": text} if text else {"raw": resp})})
            return 1
        mime, data = images[0]
        out_path = args.out or _safe_filename(_ext_from_mime(mime))
        with open(out_path, "wb") as f:
            f.write(data)
        _print_json({"success": True, "route": route, "model": args.model, "mime_type": mime,
                     "saved_to": out_path, "images_returned": len(images)})
        return 0

    if route == "wan-chat":
        urls = _extract_wan_chat_image_urls(resp)
        if not urls:
            _print_json({"success": False, "route": route,
                         "error": "No image parts in chat response", "raw": resp})
            return 1
        out_path = args.out or _safe_filename("png")
        dl = _download_to_file(urls[0], out_path)
        _print_json({"success": dl.get("success", False), "route": route, "model": args.model,
                     "url": urls[0], "saved_to": out_path, "images_returned": len(urls),
                     "download": dl})
        return 0 if dl.get("success") else 1

    if route == "seedream":
        images = _extract_seedream_images(resp)
        if not images:
            _print_json({"success": False, "route": route,
                         "error": "No images in /v1/images/generations response", "raw": resp})
            return 1
        kind, data, url = images[0]
        out_path = args.out or _safe_filename("png")
        if kind == "b64" and data is not None:
            with open(out_path, "wb") as f:
                f.write(data)
            _print_json({"success": True, "route": route, "model": args.model,
                         "saved_to": out_path, "images_returned": len(images),
                         "source": "b64_json"})
            return 0
        if kind == "url" and url:
            dl = _download_to_file(url, out_path)
            _print_json({"success": dl.get("success", False), "route": route, "model": args.model,
                         "url": url, "saved_to": out_path, "images_returned": len(images),
                         "download": dl})
            return 0 if dl.get("success") else 1

    _print_json({"success": False, "route": route, "error": "unknown response shape", "raw": resp})
    return 1


def cmd_video_create(args: argparse.Namespace) -> int:
    api_key = _get_api_key(args.api_key)
    resp = video_create_task(
        api_key=api_key,
        model=args.model,
        prompt=args.prompt,
        img_url=args.img_url,
        negative_prompt=args.negative_prompt,
        resolution=args.resolution,
        duration=args.duration,
        shot_type=args.shot_type,
        watermark=args.watermark,
        seed=args.seed,
    )
    _print_json(resp)
    return 0


def cmd_video_status(args: argparse.Namespace) -> int:
    api_key = _get_api_key(args.api_key)
    resp = video_task_status(api_key=api_key, task_id=args.task_id)
    _print_json(resp)
    return 0


def cmd_video_wait(args: argparse.Namespace) -> int:
    api_key = _get_api_key(args.api_key)
    start = time.time()
    while True:
        resp = video_task_status(api_key=api_key, task_id=args.task_id)
        status = (
            (resp.get("output") or {}).get("task_status")
            or (resp.get("output") or {}).get("taskStatus")
            or resp.get("task_status")
        )
        if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
            if status == "SUCCEEDED" and getattr(args, "download", False):
                video_url = (resp.get("output") or {}).get("video_url") or (resp.get("output") or {}).get("videoUrl")
                if video_url:
                    out_path = args.out or _safe_filename("mp4")
                    dl = _download_to_file(video_url, out_path)
                    resp = {**resp, "download": dl}
            _print_json(resp)
            return 0 if status == "SUCCEEDED" else 1

        if time.time() - start > args.timeout:
            _print_json({"success": False, "error": "timeout", "last_response": resp})
            return 1

        time.sleep(args.poll)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Media Gen - image & video generation")
    p.add_argument("--api-key", help="Override AISA_API_KEY")

    sub = p.add_subparsers(dest="command")

    img = sub.add_parser(
        "image",
        help="Generate an image. Model determines endpoint: Gemini / Wan-chat / Seedream.",
    )
    img.add_argument(
        "--model",
        default="gemini-3-pro-image-preview",
        help=(
            "Image model. Supported: "
            "gemini-3-pro-image-preview (Google), "
            "wan2.7-image / wan2.7-image-pro (Alibaba), "
            "seedream-4-5-251128 (ByteDance). "
            "Default: gemini-3-pro-image-preview."
        ),
    )
    img.add_argument("--prompt", required=True, help="Image prompt")
    img.add_argument("--out", help="Output file path (png/jpg/webp)")
    img.add_argument("--n", type=int, default=1, help="Number of images (wan-chat / seedream only).")
    img.add_argument(
        "--size",
        default=None,
        help="Seedream only. WxH in pixels; default 2048x2048. Minimum 3,686,400 pixels upstream.",
    )
    img.set_defaults(func=cmd_image)

    vc = sub.add_parser(
        "video-create",
        help="Create a Wan video generation task (any of 4 variants).",
    )
    vc.add_argument(
        "--model",
        default="wan2.7-i2v",
        choices=["wan2.6-t2v", "wan2.6-i2v", "wan2.7-t2v", "wan2.7-i2v"],
        help=(
            "Video model. t2v models take prompt only; i2v models require --img-url. "
            "Default: wan2.7-i2v (current flagship)."
        ),
    )
    vc.add_argument("--prompt", required=True, help="Video prompt")
    vc.add_argument(
        "--img-url",
        default=None,
        help=(
            "Reference image URL. Required for *-i2v; ignored for *-t2v. "
            "Routed to input.img_url for wan2.6-i2v or input.media[] for wan2.7-i2v."
        ),
    )
    vc.add_argument("--negative-prompt", help="Negative prompt")
    vc.add_argument("--resolution", default="720P", help="Resolution (e.g., 720P, 1080P)")
    vc.add_argument("--duration", type=int, default=5, choices=[5, 10], help="Duration seconds")
    vc.add_argument("--shot-type", default="single", choices=["single", "multi"], help="Shot type")
    vc.add_argument("--watermark", action="store_true", help="Enable watermark")
    vc.add_argument("--seed", type=int, help="Random seed")
    vc.set_defaults(func=cmd_video_create)

    vs = sub.add_parser("video-status", help="Query video task status")
    vs.add_argument("--task-id", required=True, help="Task id")
    vs.set_defaults(func=cmd_video_status)

    vw = sub.add_parser("video-wait", help="Wait until video task finishes")
    vw.add_argument("--task-id", required=True, help="Task id")
    vw.add_argument("--poll", type=int, default=10, help="Poll interval seconds")
    vw.add_argument("--timeout", type=int, default=600, help="Timeout seconds")
    vw.add_argument("--download", action="store_true", help="Download video on SUCCEEDED")
    vw.add_argument("--out", help="Output .mp4 path when using --download")
    vw.set_defaults(func=cmd_video_wait)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

