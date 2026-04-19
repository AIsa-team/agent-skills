"""First-run setup helpers for the AISA-only last30days skill."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def is_first_run(config: dict[str, Any]) -> bool:
    """Return True when setup has not been completed."""
    return not config.get("SETUP_COMPLETE")


def run_auto_setup(config: dict[str, Any]) -> dict[str, Any]:
    """Return the current AISA setup state."""
    return {
        "aisa_configured": bool(config.get("AISA_API_KEY")),
        "env_written": False,
    }


def write_setup_config(env_path: Path) -> bool:
    """Write SETUP_COMPLETE to the .env file without overwriting existing keys."""
    try:
        env_path = Path(env_path)
        env_path.parent.mkdir(parents=True, exist_ok=True)

        existing_keys: set[str] = set()
        existing_content = ""
        if env_path.exists():
            existing_content = env_path.read_text(encoding="utf-8")
            for line in existing_content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    existing_keys.add(stripped.split("=", 1)[0].strip())

        if "SETUP_COMPLETE" in existing_keys:
            return True

        with open(env_path, "a", encoding="utf-8") as handle:
            if existing_content and not existing_content.endswith("\n"):
                handle.write("\n")
            handle.write("SETUP_COMPLETE=true\n")
        return True
    except OSError as exc:
        logger.error("Failed to write setup config to %s: %s", env_path, exc)
        return False


def get_setup_status_text(results: dict[str, Any]) -> str:
    """Return a human-readable summary of setup results."""
    lines = [
        "Setup complete! Here's what I found:",
        "",
        "  - AISA API key configured" if results.get("aisa_configured") else "  - AISA API key not configured",
    ]
    if results.get("env_written"):
        lines.extend(["", "Configuration saved. Future runs will use the AISA-only setup defaults."])
    return "\n".join(lines)


def _has_python312_plus() -> bool:
    candidates = [
        "/usr/local/python3.12/bin/python3.12",
        shutil.which("python3.14"),
        shutil.which("python3.13"),
        shutil.which("python3.12"),
        shutil.which("python3"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            proc = subprocess.run(
                [candidate, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"],
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError:
            continue
        if proc.returncode == 0:
            return True
    return False


def run_openclaw_setup(config: dict[str, Any]) -> dict[str, Any]:
    """Server-side setup probe: no browser auth, just tool + key availability."""
    return {
        "node": shutil.which("node") is not None,
        "python3": _has_python312_plus(),
        "keys": {"aisa": bool(config.get("AISA_API_KEY"))},
        "aisa_configured": bool(config.get("AISA_API_KEY")),
        "x_method": "aisa" if config.get("AISA_API_KEY") else None,
    }


def run_github_auth() -> dict[str, Any]:
    """GitHub auth is no longer brokered by this skill."""
    return {"supported": False, "reason": "GitHub auth is handled by GH_TOKEN/GITHUB_TOKEN."}


def run_full_device_auth() -> dict[str, Any]:
    """Device auth is no longer exposed by the AISA-only runtime."""
    return {"supported": False, "reason": "Legacy device auth was removed from the AISA-only runtime."}
