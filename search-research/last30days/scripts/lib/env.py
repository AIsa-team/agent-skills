"""Environment and runtime configuration for the AISA-only last30days skill."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Allow override via environment variable for testing
# Set LAST30DAYS_CONFIG_DIR="" for clean/no-config mode
# Set LAST30DAYS_CONFIG_DIR="/path/to/dir" for custom config location
_config_override = os.environ.get('LAST30DAYS_CONFIG_DIR')
if _config_override == "":
    # Empty string = no config file (clean mode)
    CONFIG_DIR = None
    CONFIG_FILE = None
elif _config_override:
    CONFIG_DIR = Path(_config_override)
    CONFIG_FILE = CONFIG_DIR / ".env"
else:
    CONFIG_DIR = Path.home() / ".config" / "last30days"
    CONFIG_FILE = CONFIG_DIR / ".env"

def _resolve_from_files(name: str) -> str:
    """Resolve a setting from the environment, then from known AIsa config files.

    os.environ is not always populated. The plugin / OpenClaw install form has no
    profile .env to inherit from, and hermes' sandboxed code-execution path
    strips variables whose name contains "KEY"/"TOKEN"/... `~/.aisa/credentials`
    is the cross-harness convention AgentSpec documents for exactly this case.

    Applies to the model pins as much as the key: without a pin,
    providers._resolve_model_pins raises and the run dies, and the only
    documented recovery (`last30days setup`) is interactive.

    Order: env -> ~/.aisa/credentials
           -> $HERMES_HOME/profiles/$HERMES_PROFILE/.env (when HERMES_PROFILE is set)
           -> $HERMES_HOME/.env

    Under `hermes --profile X`, HERMES_HOME *is* the profile directory and
    HERMES_PROFILE is unset, so the last candidate resolves to that profile's own
    .env. Only the running profile is ever read, never a sibling's.

    Returns "" when nothing is found, when clean mode is active
    (LAST30DAYS_CONFIG_DIR=""), or when a file is unreadable — never raises.
    """
    value = os.environ.get(name, "").strip()
    if value:
        return value

    # LAST30DAYS_CONFIG_DIR="" is clean mode: the caller has built a deliberately
    # minimal environment and expects nothing to be picked up off disk.
    # evaluate_search_quality's create_eval_env() relies on that to compare two
    # revisions hermetically — reading the operator's model pin from
    # ~/.aisa/credentials there would silently change what is being measured.
    if CONFIG_FILE is None:
        return ""

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
            key, sep, val = line.partition("=")
            if not sep or key.strip() != name:
                continue
            val = val.strip()
            if val[:1] in ("'", '"'):
                # A quoted value ends at its closing quote; whatever follows is
                # a trailing comment, not part of the secret. Checking "starts
                # and ends with a quote" instead would miss `KEY="v" # note`
                # and hand back the value with its quotes still attached.
                end = val.find(val[0], 1)
                val = val[1:end] if end != -1 else val[1:]
            else:
                for marker in (" #", "\t#"):
                    if marker in val:
                        val = val.split(marker, 1)[0]
                val = val.strip()
            # U+FFFD only appears where bytes failed to decode, so the value is
            # corrupt and cannot be a real setting — keep looking rather than
            # send garbage as a bearer token or a model id.
            if val and "�" not in val:
                return val
    return ""


def _resolve_aisa_api_key() -> str:
    """Back-compat alias — lib/http.py imports this name."""
    return _resolve_from_files("AISA_API_KEY")


def _check_file_permissions(path: Path) -> None:
    """Warn to stderr if a secrets file has overly permissive permissions."""
    try:
        mode = path.stat().st_mode
        # Check if group or other can read (bits 0o044)
        if mode & 0o044:
            sys.stderr.write(
                f"[last30days] WARNING: {path} is readable by other users. "
                f"Run: chmod 600 {path}\n"
            )
            sys.stderr.flush()
    except OSError as exc:
        sys.stderr.write(f"[last30days] WARNING: could not stat {path}: {exc}\n")
        sys.stderr.flush()


def load_env_file(path: Path) -> dict[str, str]:
    """Load environment variables from a file."""
    env = {}
    if not path or not path.exists():
        return env
    _check_file_permissions(path)

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1]
                if key and value:
                    env[key] = value
    return env

def _find_project_env() -> Path | None:
    """Find per-project .env by walking up from cwd.

    Searches for .claude/last30days.env in each parent directory,
    stopping at the user's home directory or filesystem root.
    """
    if CONFIG_FILE is None:
        return None
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / '.claude' / 'last30days.env'
        if candidate.exists():
            return candidate
        # Stop at filesystem root or home
        if parent == Path.home() or parent == parent.parent:
            break
    return None


def get_config() -> dict[str, Any]:
    """Load configuration from multiple sources.

    Priority (highest wins):
      1. Environment variables (os.environ)
      2. .claude/last30days.env (per-project config)
      3. ~/.config/last30days/.env (global config)
    """
    # Load from global config file
    file_env = load_env_file(CONFIG_FILE) if CONFIG_FILE else {}

    # Load from per-project config (overrides global)
    project_env_path = _find_project_env()
    project_env = load_env_file(project_env_path) if project_env_path else {}

    # Merge: project overrides global
    merged_env = {**file_env, **project_env}

    # Build config: process.env > project .env > global .env
    config = {
        'AISA_API_KEY': (os.environ.get('AISA_API_KEY') or merged_env.get('AISA_API_KEY')
                         or _resolve_from_files('AISA_API_KEY') or None),
        'AISA_BASE_URL': os.environ.get('AISA_BASE_URL') or merged_env.get('AISA_BASE_URL', 'https://api.aisa.one'),
        'GITHUB_TOKEN': (
            os.environ.get('GITHUB_TOKEN')
            or os.environ.get('GH_TOKEN')
            or merged_env.get('GITHUB_TOKEN')
            or merged_env.get('GH_TOKEN')
        ),
    }

    keys = [
        ('AISA_MODEL', None),
        ('XIAOHONGSHU_API_BASE', None),
        ('LAST30DAYS_REASONING_PROVIDER', 'auto'),
        ('LAST30DAYS_PLANNER_MODEL', None),
        ('LAST30DAYS_RERANK_MODEL', None),
        ('LAST30DAYS_FUN_MODEL', None),
        ('LAST30DAYS_X_BACKEND', None),
        ('SETUP_COMPLETE', None),
        ('INCLUDE_SOURCES', None),
        ('LAST30DAYS_YOUTUBE_TRANSCRIPTS', None),
        ('LAST30DAYS_REDDIT_COMMENTS', None),
    ]

    # Settings that also fall back to the AIsa config files. Under a harness
    # that scrubs the environment (hermes), os.environ is empty for all of
    # these, and the model pins are as load-bearing as the key: without one,
    # providers._resolve_model_pins raises and the whole run dies.
    FILE_BACKED = {
        'AISA_MODEL',
        'LAST30DAYS_PLANNER_MODEL',
        'LAST30DAYS_RERANK_MODEL',
        'LAST30DAYS_FUN_MODEL',
    }
    for key, default in keys:
        value = os.environ.get(key) or merged_env.get(key)
        if not value and key in FILE_BACKED:
            value = _resolve_from_files(key)
        config[key] = value or default

    # Track which config source was used
    if project_env_path:
        config['_CONFIG_SOURCE'] = f'project:{project_env_path}'
    elif CONFIG_FILE and CONFIG_FILE.exists():
        config['_CONFIG_SOURCE'] = f'global:{CONFIG_FILE}'
    else:
        config['_CONFIG_SOURCE'] = 'env_only'

    return config


def get_x_source_with_method(config: dict[str, Any]) -> tuple[str | None, str]:
    """Return (source, method) for X search in the AISA-only runtime."""
    if config.get("AISA_API_KEY"):
        return "aisa", "aisa"
    return None, "none"


def config_exists() -> bool:
    """Check if any configuration source exists."""
    if _find_project_env():
        return True
    if CONFIG_FILE:
        return CONFIG_FILE.exists()
    return False


def is_reddit_available(config: dict[str, Any]) -> bool:
    """Check if Reddit search is available.

    Public Reddit is always available.
    """
    del config
    return True


def get_reddit_source(config: dict[str, Any]) -> str | None:
    """Determine which Reddit backend to use."""
    del config
    return 'public'


def get_x_source(config: dict[str, Any]) -> str | None:
    """Determine the active X backend for the AISA-only runtime."""
    preferred = (config.get('LAST30DAYS_X_BACKEND') or '').lower()
    if preferred == 'aisa':
        return 'aisa' if config.get('AISA_API_KEY') else None
    if config.get('AISA_API_KEY'):
        return 'aisa'
    return None


def is_ytdlp_available() -> bool:
    """Legacy compatibility probe for older transcript helpers."""
    from . import youtube_yt
    return youtube_yt.is_ytdlp_installed()


def is_youtube_comments_available(config: dict[str, Any]) -> bool:
    """YouTube comment enrichment is not exposed in the AISA-only runtime."""
    del config
    return False


def is_youtube_sc_available(config: dict[str, Any]) -> bool:
    """Check if AISA YouTube search is available."""
    return bool(config.get('AISA_API_KEY'))


def is_hackernews_available() -> bool:
    """Check if Hacker News source is available.

    Always returns True - HN uses free Algolia API, no key needed.
    """
    return True


def is_polymarket_available() -> bool:
    """Check if Polymarket source is available.

    AISA is required for the hosted Polymarket integration.
    """
    return bool(get_config().get("AISA_API_KEY"))


def is_tiktok_available(config: dict[str, Any]) -> bool:
    """Check if TikTok source is available."""
    return bool(config.get('AISA_API_KEY'))


def get_tiktok_token(config: dict[str, Any]) -> str:
    """Get the AISA token for TikTok discovery."""
    return config.get('AISA_API_KEY') or ''


def _parse_include_sources(config: dict[str, Any]) -> set[str]:
    """Parse INCLUDE_SOURCES config value into a set of lowercase source names."""
    raw = config.get('INCLUDE_SOURCES') or ''
    return {s.strip().lower() for s in raw.split(',') if s.strip()}


def is_threads_available(config: dict[str, Any]) -> bool:
    """Check if Threads source is available."""
    if not config.get('AISA_API_KEY'):
        return False
    return 'threads' in _parse_include_sources(config)


def is_instagram_available(config: dict[str, Any]) -> bool:
    """Check if Instagram source is available."""
    return bool(config.get('AISA_API_KEY'))


def get_instagram_token(config: dict[str, Any]) -> str:
    """Get the AISA token for Instagram discovery."""
    return config.get('AISA_API_KEY') or ''


def get_xiaohongshu_api_base(config: dict[str, Any]) -> str:
    """Get Xiaohongshu HTTP API base URL.

    Defaults to host.docker.internal so OpenClaw Docker can reach host service.
    """
    return (config.get('XIAOHONGSHU_API_BASE') or "http://host.docker.internal:18060").rstrip("/")


def is_xiaohongshu_available(config: dict[str, Any]) -> bool:
    """Check whether Xiaohongshu HTTP API is reachable and logged in."""
    # Import here to avoid heavy imports at module load.
    from . import http

    base = get_xiaohongshu_api_base(config)
    try:
        # Keep health probe snappy, but allow one retry for transient hiccups.
        health = http.get(f"{base}/health", timeout=3, retries=2)
        if not isinstance(health, dict):
            return False
        if not health.get("success"):
            return False

        # Login probe can be slower on some deployments (browser/session checks),
        # so use a slightly longer timeout to avoid false negatives.
        login = http.get(f"{base}/api/v1/login/status", timeout=8, retries=2)
        is_logged_in = (
            login.get("data", {}).get("is_logged_in")
            if isinstance(login, dict) else False
        )
        return bool(is_logged_in)
    except (OSError, http.HTTPError):
        return False
    except Exception as exc:
        sys.stderr.write(
            f"[last30days] WARNING: unexpected error checking Xiaohongshu: "
            f"{type(exc).__name__}: {exc}\n"
        )
        sys.stderr.flush()
        return False


# Backward compat alias
is_apify_available = is_tiktok_available


def get_x_source_status(config: dict[str, Any]) -> dict[str, Any]:
    """Get detailed X source status for UI decisions."""
    if config.get('AISA_API_KEY'):
        source = 'aisa'
    else:
        source = None

    return {
        "source": source,
        "bird_installed": False,
        "bird_authenticated": False,
        "bird_username": "",
        "aisa_available": bool(config.get('AISA_API_KEY')),
        "xai_available": False,
        "can_install_bird": False,
    }


# Pinterest
def is_pinterest_available(config: dict[str, Any]) -> bool:
    """Check if Pinterest source is available."""
    if not config.get('AISA_API_KEY'):
        return False
    return 'pinterest' in _parse_include_sources(config)


def get_pinterest_token(config: dict[str, Any]) -> str:
    """Get the AISA token for Pinterest discovery."""
    return config.get('AISA_API_KEY') or ''
