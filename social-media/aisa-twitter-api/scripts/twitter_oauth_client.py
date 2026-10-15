#!/usr/bin/env python3
from __future__ import annotations

"""
Twitter OAuth client for local authorization and tweet publishing through AIsa API.

Commands:
    python twitter_oauth_client.py authorize [--open-browser] [--quote]
    python twitter_oauth_client.py post --text "Hello" [--thread] [--dry-run]
    python twitter_oauth_client.py status
"""

import argparse
import importlib.util
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_TIMEOUT = 30
DEFAULT_BASE_URL = "https://api.aisa.one/apis/v1"
DEFAULT_CHROME_USER_AGENT = "AIsa-Twitter-OAuth/2.0"


def get_transport():
    """Load the shipped helper relative to this file, including importlib callers."""
    path = Path(__file__).resolve().with_name("aisa_transport.py")
    module_name = "_aisa_twitter_transport"
    if module_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise RelayConfigError("The bundled aisa_transport.py helper is missing.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        script_dir = str(path.parent)
        inserted = script_dir not in sys.path
        if inserted:
            sys.path.insert(0, script_dir)
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise
        finally:
            if inserted:
                sys.path.remove(script_dir)
    return sys.modules[module_name]



class RelayConfigError(ValueError):
    """Configuration is incomplete or invalid."""


def _resolve_aisa_api_key() -> str:
    """Resolve AISA_API_KEY from the environment, then from known credential files.

    os.environ is not always populated. The plugin / OpenClaw install form has no
    profile .env to inherit from, and hermes' sandboxed code-execution path
    strips variables whose name contains "KEY". `~/.aisa/credentials` is the
    cross-harness convention AgentSpec already documents for exactly this case
    (plugin-core/inject.ts: "scripts resolve these as: env var ->
    ~/.aisa/credentials").

    Order: env -> ~/.aisa/credentials
           -> $HERMES_HOME/profiles/$HERMES_PROFILE/.env (when HERMES_PROFILE is set)
           -> $HERMES_HOME/.env

    Under `hermes --profile X`, HERMES_HOME *is* the profile directory and
    HERMES_PROFILE is unset, so the last candidate resolves to that profile's own
    .env; the middle one covers harnesses that identify the profile by name
    instead. Only the running profile is ever read, never a sibling's, so a host
    with several profiles cannot hand back the wrong tenant's key.

    Returns "" when nothing is found; never raises on an unreadable or
    undecodable file.

    Kept byte-identical across the AIsa skills that need it —
    financial/marketpulse/scripts/market_client.py is the canonical copy; change
    it there first, then propagate.
    """
    key = os.environ.get("AISA_API_KEY", "").strip()
    if key:
        return key

    home = os.path.expanduser("~")
    hermes_home = os.environ.get("HERMES_HOME") or os.path.join(home, ".hermes")

    candidates = [os.path.join(home, ".aisa", "credentials")]
    profile = os.environ.get("HERMES_PROFILE", "").strip()
    if profile:
        candidates.append(os.path.join(hermes_home, "profiles", profile, ".env"))
    candidates.append(os.path.join(hermes_home, ".env"))

    for path in candidates:
        try:
            # utf-8-sig drops a BOM; errors="replace" keeps a mis-encoded file
            # from raising UnicodeDecodeError (a ValueError, not an OSError).
            with open(path, encoding="utf-8-sig", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            name, sep, value = line.partition("=")
            if not sep or name.strip() != "AISA_API_KEY":
                continue
            value = value.strip()
            if value[:1] in ("'", '"'):
                # A quoted value ends at its closing quote; whatever follows is
                # a trailing comment, not part of the secret. Checking "starts
                # and ends with a quote" instead would miss `KEY="v" # note`
                # and hand back the value with its quotes still attached.
                end = value.find(value[0], 1)
                value = value[1:end] if end != -1 else value[1:]
            else:
                for marker in (" #", "\t#"):
                    if marker in value:
                        value = value.split(marker, 1)[0]
                value = value.strip()
            # U+FFFD only appears where bytes failed to decode, so the value is
            # corrupt and cannot be a real key — keep looking rather than send
            # garbage as a bearer token.
            if value and "�" not in value:
                return value
    return ""


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise RelayConfigError("AIsa API base URL is required.")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RelayConfigError("AIsa API base URL must be a valid http(s) URL.")
    return value


def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    base_url = normalize_base_url(DEFAULT_BASE_URL)
    aisa_api_key = _resolve_aisa_api_key()
    timeout = DEFAULT_TIMEOUT

    if not aisa_api_key:
        raise RelayConfigError(
            "AISA_API_KEY is required. Set the environment variable or add\n"
            "AISA_API_KEY=<key> to ~/.aisa/credentials."
        )

    transport = get_transport()
    try:
        budget = transport.budget_from_args(args)
    except (transport.costs.CostControlError, OSError) as exc:
        raise RelayConfigError(str(exc)) from exc
    return {
        "base_url": base_url,
        "aisa_api_key": aisa_api_key,
        "timeout": timeout,
        "budget": budget,
        "quote_only": bool(getattr(args, "quote", False)),
    }


def parse_response_body(raw: str, status: Any, default_message: str) -> Dict[str, Any]:
    try:
        result = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        result = None
    if not isinstance(result, dict):
        return {"ok": False, "success": False, "status": status,
                "error": {"code": "INVALID_RESPONSE", "message": "Expected a JSON object from AIsa."}}
    if isinstance(status, int) and not 200 <= status < 300:
        return {"ok": False, "success": False, "status": status, "payload": result}
    return result


def redact_secrets(value: Any, api_key: str = "") -> Any:
    """Do not expose credentials, even if an upstream error echoes the request."""
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if str(key).lower() in {"aisa_api_key", "authorization"}
                      else redact_secrets(item, api_key)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, api_key) for item in value]
    if isinstance(value, str) and api_key:
        return value.replace(api_key, "[REDACTED]")
    return value


def print_result(result: Dict[str, Any], api_key: str = "") -> None:
    output = get_transport().sanitize(redact_secrets(result, api_key), api_key)
    try:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except UnicodeEncodeError:
        print(json.dumps(output, indent=2, ensure_ascii=True))


def response_failed(result: Any) -> bool:
    if not isinstance(result, dict):
        return True
    if result.get("ok") is False or result.get("success") is False:
        return True
    if result.get("error") or result.get("errors"):
        return True
    code = result.get("code")
    return code is not None and str(code) not in {"200", "201"}


def build_auth_headers(aisa_api_key: str, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {aisa_api_key}",
        "User-Agent": DEFAULT_CHROME_USER_AGENT,
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def send_json_request(
    url: str,
    payload: Dict[str, Any],
    timeout: int,
    aisa_api_key: str,
    budget: Any = None,
    quote_only: bool = False,
) -> Dict[str, Any]:
    return get_transport().request(
        "POST", url, aisa_api_key, json_data=payload,
        headers={"User-Agent": DEFAULT_CHROME_USER_AGENT}, timeout=timeout,
        budget=budget, quote_only=quote_only,
    )


def encode_multipart_form_data(
    fields: Dict[str, Any],
    files: list[Dict[str, Any]],
) -> tuple[bytes, str]:
    boundary = f"----OpenClawTwitterBoundary{uuid.uuid4().hex}"
    body = bytearray()

    def append_text_part(name: str, value: Any) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise RelayConfigError("Invalid multipart field name.")
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for field_name, field_value in fields.items():
        if field_value is None:
            continue
        if isinstance(field_value, list):
            for item in field_value:
                append_text_part(field_name, item)
            continue
        append_text_part(field_name, field_value)

    for file_payload in files:
        field_name = file_payload["field_name"]
        filename = file_payload["filename"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", field_name):
            raise RelayConfigError("Invalid multipart file field name.")
        ascii_filename = "".join(ch if 32 <= ord(ch) < 127 and ch not in {'"', "\\"} else "_" for ch in filename) or "upload.bin"
        quoted_filename = urllib.parse.quote(filename, safe="")
        content_type = file_payload["content_type"]
        if "\r" in content_type or "\n" in content_type:
            raise RelayConfigError("Invalid media content type.")

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{ascii_filename}"; filename*=UTF-8\'\'{quoted_filename}\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_payload["content"])
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), boundary


def send_multipart_request(
    url: str,
    fields: Dict[str, Any],
    files: list[Dict[str, Any]],
    timeout: int,
    aisa_api_key: str,
    budget: Any = None,
    quote_only: bool = False,
) -> Dict[str, Any]:
    body, boundary = encode_multipart_form_data(fields, files)
    return get_transport().request(
        "POST", url, aisa_api_key, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "User-Agent": DEFAULT_CHROME_USER_AGENT},
        timeout=timeout, budget=budget, quote_only=quote_only,
    )


TWITTER_MAX_WEIGHT = 280
TWITTER_URL_WEIGHT = 23
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def twitter_char_weight(ch: str) -> int:
    if unicodedata.east_asian_width(ch) in {"W", "F"}:
        return 2
    if unicodedata.category(ch).startswith("M"):
        return 0
    return 1


def twitter_weight_len(text: str) -> int:
    total = 0
    idx = 0
    for matched in URL_PATTERN.finditer(text):
        start, end = matched.span()
        while idx < start:
            total += twitter_char_weight(text[idx])
            idx += 1
        total += TWITTER_URL_WEIGHT
        idx = end

    while idx < len(text):
        total += twitter_char_weight(text[idx])
        idx += 1
    return total


def text_fits(text: str, max_len: int = TWITTER_MAX_WEIGHT) -> bool:
    # The relay additionally enforces a literal 280-codepoint content limit.
    return len(text) <= max_len and twitter_weight_len(text) <= max_len


def split_by_twitter_weight(text: str, max_len: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        if text_fits(candidate, max_len):
            current = candidate
            continue
        if current:
            parts.append(current)
        current = ch
    if current:
        parts.append(current)
    return parts


def split_text_for_twitter(text: str, max_len: int = TWITTER_MAX_WEIGHT) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if text_fits(normalized, max_len):
        return [normalized]

    words = normalized.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        if not text_fits(word, max_len):
            if URL_PATTERN.fullmatch(word):
                raise RelayConfigError("A URL exceeds the relay's 280-character content limit; shorten it before posting.")
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(split_by_twitter_weight(word, max_len))
            continue

        candidate = word if not current else f"{current} {word}"
        if text_fits(candidate, max_len):
            current = candidate
        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)
    return chunks


def extract_tweet_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise RelayConfigError("Quote tweet URL must be a valid http(s) URL.")
    if parsed.netloc.lower() not in {"twitter.com", "www.twitter.com", "x.com", "www.x.com"}:
        raise RelayConfigError("Quote tweet URL must point to twitter.com or x.com.")

    match = re.fullmatch(r"/(?:[A-Za-z0-9_]+|i/web)/status/([0-9]{1,64})/?", parsed.path)
    if not match:
        raise RelayConfigError("Quote tweet URL must contain a valid /status/<tweet_id> path.")
    return match.group(1)


def append_quote_url_to_content(content: str, quote_url: str) -> str:
    normalized_content = content.strip()
    normalized_quote_url = quote_url.strip()
    if not normalized_quote_url:
        return normalized_content
    if normalized_quote_url in normalized_content:
        return normalized_content
    if not normalized_content:
        return normalized_quote_url
    return f"{normalized_content}\n\n{normalized_quote_url}"


def extract_tweet_id(result: Dict[str, Any]) -> Optional[str]:
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, dict):
        return None
    nested_data = data.get("data")
    tweet_id = data.get("tweet_id") or data.get("id")
    if not tweet_id and isinstance(nested_data, dict):
        tweet_id = nested_data.get("id")
    if isinstance(tweet_id, (str, int)) and not isinstance(tweet_id, bool):
        text = str(tweet_id).strip()
        return text if re.fullmatch(r"[0-9]{1,64}", text) else None
    return None


def publish_chunks(
    config: Dict[str, Any],
    chunks: list[str],
    media_ids: Optional[list[str]] = None,
    media_files: Optional[list[Dict[str, Any]]] = None,
    initial_parent_tweet_id: Optional[str] = None,
    post_type: Optional[str] = None,
) -> Dict[str, Any]:
    should_thread = len(chunks) > 1
    previous_tweet_id = initial_parent_tweet_id
    publish_results = []

    for index, chunk in enumerate(chunks):
        current_media_ids = media_ids if index == 0 and media_ids else None
        current_media_files = media_files if index == 0 and media_files else None
        result = post_single_tweet(
            config,
            content=chunk,
            media_ids=current_media_ids,
            media_files=current_media_files,
            parent_tweet_id=previous_tweet_id,
            post_type=post_type if index == 0 else "reply",
        )
        publish_results.append(
            {
                "index": index + 1,
                "content": chunk,
                "parent_tweet_id": previous_tweet_id,
                "result": result,
            }
        )
        if response_failed(result):
            return {
                "ok": False,
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "confirmed_posts": index,
                "retry_guidance": "Do not replay the thread. Inspect the failed request and the account before retrying an uncertain write.",
                "results": publish_results,
            }

        latest_tweet_id = extract_tweet_id(result)
        if not latest_tweet_id:
            return {
                "ok": False,
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "confirmed_posts": index,
                "outcome_unknown": True,
                "error": "The relay did not return a valid tweet ID; the post may already exist. Check the account before retrying.",
                "results": publish_results,
            }
        previous_tweet_id = latest_tweet_id

    return {
        "ok": True,
        "is_thread": should_thread,
        "total_chunks": len(chunks),
        "confirmed_posts": len(chunks),
        "results": publish_results,
    }


def post_single_tweet(
    config: Dict[str, Any],
    *,
    content: Optional[str] = None,
    media_ids: Optional[list[str]] = None,
    media_files: Optional[list[Dict[str, Any]]] = None,
    parent_tweet_id: Optional[str] = None,
    post_type: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "aisa_api_key": config["aisa_api_key"],
    }
    if content:
        payload["content"] = content
    if media_ids:
        payload["media_ids"] = media_ids
    if parent_tweet_id:
        parent_key = "in_reply_to_tweet_id" if post_type == "reply" else "quote_tweet_id"
        payload[parent_key] = parent_tweet_id

    endpoint = f"{config['base_url']}/twitter/post_twitter"
    if media_files:
        raise RelayConfigError("Upload local files with upload_media before publishing their media IDs.")
    return send_json_request(
        endpoint,
        payload,
        timeout=config["timeout"],
        aisa_api_key=config["aisa_api_key"],
        budget=config.get("budget"),
        quote_only=config.get("quote_only", False),
    )


def load_media_files(paths: Optional[list[str]], read_contents: bool = True) -> list[Dict[str, Any]]:
    if not paths:
        return []

    media_files: list[Dict[str, Any]] = []
    media_kinds: set[str] = set()
    seen_paths: set[str] = set()

    for raw_path in paths:
        resolved_path = os.path.realpath(os.path.expanduser(raw_path))
        normalized_path = os.path.normcase(resolved_path)
        if normalized_path in seen_paths:
            continue
        seen_paths.add(normalized_path)

        if not os.path.exists(resolved_path):
            raise RelayConfigError(f"Media file does not exist: {raw_path}")
        if not os.path.isfile(resolved_path):
            raise RelayConfigError(f"Media path is not a file: {raw_path}")

        mime_type = mimetypes.guess_type(resolved_path)[0] or "application/octet-stream"
        media_kind = mime_type.split("/", 1)[0]
        if mime_type not in {"image/png", "image/jpeg", "image/gif", "video/mp4"}:
            raise RelayConfigError(
                f"Unsupported media type for {raw_path}: {mime_type}. Use PNG, JPEG, GIF, or MP4."
            )
        media_kinds.add(media_kind)

        try:
            size = os.path.getsize(resolved_path)
            if not size:
                raise RelayConfigError(f"Media file is empty: {raw_path}")
            content = None
            if read_contents:
                with open(resolved_path, "rb") as file_handle:
                    content = file_handle.read()
        except OSError as exc:
            raise RelayConfigError(f"Cannot read media file: {raw_path}") from exc

        media_files.append(
            {
                "field_name": "media_files",
                "filename": os.path.basename(resolved_path),
                "content_type": mime_type,
                "content": content,
                "size_bytes": size,
            }
        )

    if len(media_kinds) > 1:
        raise RelayConfigError("Do not mix image and video files in a single post request.")

    return media_files


def upload_media(config: Dict[str, Any], media_files: list[Dict[str, Any]]) -> Dict[str, Any]:
    """Upload each file once; never post after an unconfirmed upload."""
    media_ids = []
    results = []
    for index, media_file in enumerate(media_files):
        result = send_multipart_request(
            f"{config['base_url']}/twitter/upload_media", {}, [media_file],
            timeout=config["timeout"], aisa_api_key=config["aisa_api_key"],
            budget=config.get("budget"), quote_only=config.get("quote_only", False),
        )
        results.append({"index": index + 1, "filename": media_file["filename"], "result": result})
        if response_failed(result):
            return {"ok": False, "failed_at_upload": index + 1, "results": results,
                    "media_ids": media_ids, "post_attempted": False}
        if config.get("quote_only"):
            continue
        data = result.get("data")
        media_id = data.get("media_id") if isinstance(data, dict) else None
        if not isinstance(media_id, (str, int)) or isinstance(media_id, bool) or not re.fullmatch(r"[0-9]{1,64}", str(media_id)):
            return {"ok": False, "failed_at_upload": index + 1, "outcome_unknown": True,
                    "error": "Upload returned no valid media ID. No post was attempted; inspect the upload before retrying.",
                    "media_ids": media_ids, "results": results, "post_attempted": False}
        media_ids.append(str(media_id))
    return {"ok": True, "media_ids": media_ids, "results": results, "post_attempted": False}


def command_authorize(args: argparse.Namespace) -> None:
    if args.open_browser and getattr(args, "quote", False):
        raise RelayConfigError("--open-browser cannot be combined with --quote.")
    scopes = list(dict.fromkeys((scope or "").strip() for scope in (getattr(args, "scope", None) or ["tweet.read", "tweet.write", "users.read"])))
    if any(not scope or any(ch.isspace() for ch in scope) for scope in scopes):
        raise RelayConfigError("OAuth scopes must be nonempty individual scope names.")
    if getattr(args, "media", False) and "media.write" not in scopes:
        scopes.append("media.write")
    config = load_config(args)
    payload = {"aisa_api_key": config["aisa_api_key"],
               "scopes": scopes}
    result = send_json_request(
        f"{config['base_url']}/twitter/auth_twitter",
        payload,
        timeout=config["timeout"],
        aisa_api_key=config["aisa_api_key"],
        budget=config.get("budget"),
        quote_only=config.get("quote_only", False),
    )

    if response_failed(result):
        print_result(result, config["aisa_api_key"])
        sys.exit(1)

    if config.get("quote_only"):
        print_result({"ok": True, "quote_only": True, "authorization_requested": False, "result": result}, config["aisa_api_key"])
        return
    data = result.get("data")
    auth_url = result.get("auth_url") or (data.get("auth_url") if isinstance(data, dict) else None)
    valid_url = False
    if isinstance(auth_url, str):
        parsed = urllib.parse.urlparse(auth_url)
        valid_url = parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password
    output = {
        "ok": valid_url,
        "authorization_url": auth_url if valid_url else None,
        "raw_response": result,
    }
    if not valid_url:
        output["error"] = "The relay returned no valid HTTPS authorization URL."
    print_result(output, config["aisa_api_key"])

    if output["ok"] and args.open_browser:
        webbrowser.open(auth_url)

    if not output["ok"]:
        sys.exit(1)


def command_post(args: argparse.Namespace) -> None:
    """Validate before credentials/network, then preview, quote, or publish."""
    media_ids = list(dict.fromkeys((value or "").strip() for value in (getattr(args, "media_id", None) or [])))
    if any(not re.fullmatch(r"[0-9]{1,64}", value) for value in media_ids):
        raise RelayConfigError("Media IDs must be numeric IDs of 1 to 64 digits.")
    dry_run = bool(getattr(args, "dry_run", False))
    quote_only = bool(getattr(args, "quote", False))
    if dry_run and quote_only:
        raise RelayConfigError("Choose --dry-run for an offline preview or --quote for a gateway quote.")
    normalized_text = (args.text or "").strip()
    quote_tweet_url = (getattr(args, "quote_tweet_url", None) or "").strip()
    initial_parent_tweet_id = None

    if quote_tweet_url:
        if args.type == "reply" or args.in_reply_to_tweet_id:
            raise RelayConfigError(
                "A quote URL cannot be combined with a reply parent or --type reply."
            )
        initial_parent_tweet_id = extract_tweet_id_from_url(quote_tweet_url)
        normalized_text = append_quote_url_to_content(normalized_text, quote_tweet_url)
        effective_post_type = "quote"
    elif args.in_reply_to_tweet_id:
        if args.type == "quote":
            raise RelayConfigError("Quote references require --quote-tweet-url; reply parents require --type reply.")
        initial_parent_tweet_id = args.in_reply_to_tweet_id.strip()
        if not re.fullmatch(r"[0-9]{1,64}", initial_parent_tweet_id):
            raise RelayConfigError("The reply tweet ID must contain 1 to 64 digits.")
        effective_post_type = "reply"
    else:
        if args.type == "quote":
            raise RelayConfigError("--type quote requires --quote-tweet-url.")
        if args.type == "reply":
            raise RelayConfigError("--type reply requires --in-reply-to-tweet-id. Omit --type for a new top-level post or thread.")
        effective_post_type = None

    media_paths = getattr(args, "media_file", None) or []
    if media_ids and media_paths:
        raise RelayConfigError("Use either --media-file or --media-id in one post, not both.")
    if quote_tweet_url and (media_ids or media_paths):
        raise RelayConfigError("The relay does not support combining a quote reference with media.")
    if not normalized_text and not media_ids and not media_paths:
        raise RelayConfigError("Post content must not be empty unless media files or media IDs are provided.")
    if not text_fits(normalized_text) and not getattr(args, "thread", False):
        raise RelayConfigError("Content exceeds the single-post limit. Use --thread --dry-run to review an explicit thread before publishing.")

    chunks = split_text_for_twitter(normalized_text) if normalized_text else [""]
    media_files = load_media_files(media_paths, read_contents=not dry_run)
    if len(media_ids) + len(media_files) > 4:
        raise RelayConfigError("A post supports at most four media attachments.")
    if dry_run:
        print_result({"ok": True, "dry_run": True, "network_requests": 0,
                      "total_chunks": len(chunks), "is_thread": len(chunks) > 1,
                      "chunks": [{"index": index + 1, "content": chunk,
                                  "characters": len(chunk), "estimated_weight": twitter_weight_len(chunk),
                                  "relationship": effective_post_type if index == 0 else "reply",
                                  "parent_tweet_id": initial_parent_tweet_id if index == 0 else None}
                                 for index, chunk in enumerate(chunks)],
                      "media_ids": media_ids,
                      "uploads": [{key: item[key] for key in ("filename", "content_type", "size_bytes")}
                                  for item in media_files],
                      "cost": "Not quoted; this preview is offline."})
        return

    config = load_config(args)
    uploads = None
    if media_files:
        uploads = upload_media(config, media_files)
        if not uploads["ok"]:
            print_result(uploads, config["aisa_api_key"])
            sys.exit(1)
        if quote_only:
            print_result({"ok": True, "quote_only": True, "partial_quote": True,
                          "uploads": uploads["results"], "total_chunks": len(chunks),
                          "unquoted_posts": len(chunks), "post_attempted": False,
                          "reason": "Only uploads were quoted. Post requests need media IDs returned by actual uploads; their cost is not included."}, config["aisa_api_key"])
            return
        media_ids.extend(uploads["media_ids"])

    if quote_only:
        result = post_single_tweet(config, content=chunks[0], media_ids=media_ids,
                                   parent_tweet_id=initial_parent_tweet_id, post_type=effective_post_type)
        output = {"ok": not response_failed(result), "quote_only": True,
                  "post_attempted": False, "quoted_chunks": 1, "total_chunks": len(chunks),
                  "remaining_chunks_unquoted": len(chunks) - 1, "partial_quote": len(chunks) > 1,
                  "result": result}
        if len(chunks) > 1:
            output["reason"] = "Later reply IDs do not yet exist; this quote covers only the first post."
        print_result(output, config["aisa_api_key"])
        if not output["ok"]:
            sys.exit(1)
        return

    output = publish_chunks(
        config,
        chunks,
        media_ids=media_ids,
        post_type=effective_post_type,
        initial_parent_tweet_id=initial_parent_tweet_id,
    )
    if uploads:
        output["uploads"] = uploads["results"]
    print_result(output, config["aisa_api_key"])
    if not output["ok"]:
        sys.exit(1)


def command_status(args: argparse.Namespace) -> None:
    response = {
        "ok": True,
        "relay_base_url": DEFAULT_BASE_URL,
        "aisa_api_key_present": bool(_resolve_aisa_api_key()),
        "timeout": DEFAULT_TIMEOUT,
        "supported_commands": ["authorize", "post", "status"],
        "supported_endpoints": ["/twitter/auth_twitter", "/twitter/upload_media", "/twitter/post_twitter"],
        "media_upload": {
            "field_name": "media_files",
            "transport": "multipart/form-data",
            "supported_media_types": ["image/png", "image/jpeg", "image/gif", "video/mp4"],
            "flow": "upload_media returns media IDs, then post_twitter receives JSON",
        },
    }
    print_result(response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Twitter OAuth client for local AIsa posting flows",
    )
    get_transport().add_cost_arguments(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize = subparsers.add_parser("authorize", help="Request an authorization URL from the AIsa service")
    authorize.add_argument("--open-browser", action="store_true", help="Open the authorization URL in the default browser")
    authorize.add_argument("--scope", action="append", help="Explicit OAuth scope override; repeat for each scope. Defaults to tweet.read, tweet.write, users.read.")
    authorize.add_argument("--media", action="store_true", help="Also request media.write for local file uploads.")
    get_transport().add_cost_arguments(authorize)
    authorize.set_defaults(func=command_authorize)

    post = subparsers.add_parser("post", help="Publish a post through the AIsa service")
    post.add_argument("--text", default="", help="Post content. Optional when media is provided.")
    post.add_argument("--thread", action="store_true", help="Allow oversized text to be split into a reply thread.")
    post.add_argument("--dry-run", action="store_true", help="Preview validated chunks and attachments offline without credentials.")
    get_transport().add_cost_arguments(post)
    post.add_argument(
        "--media-id",
        action="append",
        help="Media ID to attach. Repeat the flag to send multiple media IDs.",
    )
    post.add_argument(
        "--media-file",
        action="append",
        help="Local PNG, JPEG, GIF, or MP4 path. Uploads first, then attaches the returned media ID.",
    )
    post.add_argument(
        "--type",
        choices=["quote", "reply"],
        default=None,
        help="Relationship to the first external parent. Thread continuation always uses replies.",
    )
    post.add_argument(
        "--quote-tweet-url",
        help="Quoted tweet URL for quote-style posting. When provided, the URL is appended to the published content and used as the first quoted tweet.",
    )

    post.add_argument(
        "--in-reply-to-tweet-id",
        help="Optional external parent tweet ID for reply-style posting. When provided with --type reply, the first chunk starts from that tweet before continuing the thread.",
    )

    post.set_defaults(func=command_post)

    status = subparsers.add_parser("status", help="Show current relay client configuration")
    status.set_defaults(func=command_status)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except RelayConfigError as exc:
        print_result({"ok": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
