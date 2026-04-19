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
_default_config_dir = Path(__file__).resolve().parents[2] / ".last30days-config"
if _config_override == "":
    # Empty string = no config file (clean mode)
    CONFIG_DIR = None
    CONFIG_FILE = None
elif _config_override:
    CONFIG_DIR = Path(_config_override)
    CONFIG_FILE = CONFIG_DIR / ".env"
else:
    CONFIG_DIR = _default_config_dir
    CONFIG_FILE = CONFIG_DIR / ".env"

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
      3. ./.last30days-config/.env (bundle-local config)
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
        'AISA_API_KEY': os.environ.get('AISA_API_KEY') or merged_env.get('AISA_API_KEY'),
        'AISA_BASE_URL': os.environ.get('AISA_BASE_URL') or merged_env.get('AISA_BASE_URL', 'https://api.aisa.one'),
    }

    keys = [
        ('XIAOHONGSHU_API_BASE', None),
        ('LAST30DAYS_REASONING_PROVIDER', 'auto'),
        ('LAST30DAYS_PLANNER_MODEL', None),
        ('LAST30DAYS_RERANK_MODEL', None),
        ('LAST30DAYS_X_BACKEND', None),
        ('SETUP_COMPLETE', None),
        ('INCLUDE_SOURCES', None),
        ('LAST30DAYS_YOUTUBE_TRANSCRIPTS', None),
        ('LAST30DAYS_REDDIT_COMMENTS', None),
    ]

    for key, default in keys:
        config[key] = os.environ.get(key) or merged_env.get(key, default)

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
    return bool(os.environ.get("AISA_API_KEY"))


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


# Xquik
def is_xquik_available(config: dict[str, Any]) -> bool:
    """Xquik is no longer exposed in the AISA-only runtime."""
    del config
    return False


def get_xquik_token(config: dict[str, Any]) -> str:
    """Xquik is retired from the default runtime surface."""
    del config
    return ''
