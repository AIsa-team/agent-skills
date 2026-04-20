"""Post-research quality score and upgrade nudge.

Computes a quality score based on 5 core sources and builds
a nudge message describing what the user missed and how to fix it.
"""

from typing import List


# The 5 core sources
CORE_SOURCES = ["hn", "polymarket", "x", "youtube", "reddit"]

# Labels for display
SOURCE_LABELS = {
    "hn": "Hacker News",
    "polymarket": "Polymarket",
    "x": "X/Twitter",
    "youtube": "YouTube",
    "reddit": "Reddit",
}


def _is_x_active(config: dict, research_results: dict) -> bool:
    """Check if X source is active (has credentials AND didn't error)."""
    has_creds = bool(config.get("AISA_API_KEY"))
    if not has_creds:
        return False
    # If X errored this run, it's configured but broken
    if research_results.get("x_error"):
        return False
    return True


def _is_youtube_active(config: dict, research_results: dict) -> bool:
    """Check if YouTube source is active (AISA configured)."""
    if not config.get("AISA_API_KEY"):
        return False
    if research_results.get("youtube_error"):
        return False
    return True


def compute_quality_score(config: dict, research_results: dict) -> dict:
    """Compute research quality score based on 5 core sources.

    Args:
        config: Configuration dict from env.get_config()
        research_results: Dict with keys like x_error, youtube_error,
            reddit_error reflecting what happened this run.

    Returns:
        {
            "score_pct": 40-100,
            "core_active": ["hn", "polymarket", ...],
            "core_missing": ["x", "youtube"],
            "core_errored": [],  # configured but errored
            "nudge_text": "..." or None if 100%
        }
    """
    core_active: List[str] = []
    core_missing: List[str] = []
    core_errored: List[str] = []

    # HN and Reddit are always active
    core_active.append("hn")
    core_active.append("reddit")

    if config.get("AISA_API_KEY"):
        core_active.append("polymarket")
    else:
        core_missing.append("polymarket")

    # X
    has_x_creds = bool(config.get("AISA_API_KEY"))
    if _is_x_active(config, research_results):
        core_active.append("x")
    else:
        core_missing.append("x")
        if has_x_creds and research_results.get("x_error"):
            core_errored.append("x")

    # YouTube
    yt_active = _is_youtube_active(config, research_results)
    if yt_active:
        core_active.append("youtube")
    else:
        core_missing.append("youtube")
        if config.get("AISA_API_KEY") and research_results.get("youtube_error"):
            core_errored.append("youtube")

    score_pct = int(len(core_active) / 5 * 100)

    active_sources = research_results.get("active_sources") or []
    nudge_text = _build_nudge_text(core_missing, core_errored, active_sources=active_sources) if core_missing else None

    return {
        "score_pct": score_pct,
        "core_active": core_active,
        "core_missing": core_missing,
        "core_errored": core_errored,
        "nudge_text": nudge_text,
    }


def _build_nudge_text(core_missing: List[str], core_errored: List[str], active_sources: list = None) -> str:
    """Build human-readable nudge text describing what was missed.

    Prioritizes the hosted AISA path. Bonus sources that still rely on
    compatibility integrations are mentioned as optional legacy add-ons.
    """
    lines: List[str] = []

    # Describe what was missed
    missed_parts: List[str] = []
    for src in core_missing:
        label = SOURCE_LABELS[src]
        if src in core_errored:
            missed_parts.append(f"{label} (errored this run)")
        else:
            missed_parts.append(label)

    active_count = 5 - len(core_missing)
    lines.append(f"Research quality: {active_count}/5 core sources.")
    lines.append(f"Missing: {', '.join(missed_parts)}.")
    lines.append("")

    # Free suggestions
    free_suggestions: List[str] = []

    if "x" in core_missing:
        if "x" in core_errored:
            free_suggestions.append(
                "X/Twitter errored - verify AISA_API_KEY and retry."
            )
        else:
            free_suggestions.append(
                "X/Twitter: real-time posts with likes and reposts - the fastest "
                "signal for breaking topics. Add AISA_API_KEY to unlock the AISA Twitter proxy."
            )

    if "youtube" in core_missing:
        if "youtube" in core_errored:
            free_suggestions.append(
                "YouTube errored - verify your AISA API key and retry."
            )
        else:
            free_suggestions.append(
                "YouTube: video transcripts with key moments - often the deepest "
                "explanations on any topic. Add AISA_API_KEY to unlock the AISA YouTube proxy."
            )

    if free_suggestions:
        lines.append("Free fixes:")
        for s in free_suggestions:
            lines.append(f"  - {s}")
        lines.append("")

    lines.append(
        "Bonus: Reddit and Hacker News already work on public paths. GitHub still uses its official API path "
        "and may need GH_TOKEN/GITHUB_TOKEN. Optional social extras such as Threads and Pinterest "
        "need AISA plus INCLUDE_SOURCES to be enabled."
    )

    return "\n".join(lines)
