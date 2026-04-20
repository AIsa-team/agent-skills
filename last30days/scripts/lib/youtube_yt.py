"""YouTube search and transcript extraction for the AISA-only pipeline."""

import json
import math
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Depth configurations: how many videos to search / transcribe
DEPTH_CONFIG = {
    "quick": 6,
    "default": 8,
    "deep": 40,
}

TRANSCRIPT_LIMITS = {
    "quick": 0,
    "default": 2,
    "deep": 8,
}

# Max words to keep from each transcript
TRANSCRIPT_MAX_WORDS = 5000

from . import aisa, http, log
from .relevance import token_overlap_relevance as _compute_relevance


def extract_transcript_highlights(transcript: str, topic: str, limit: int = 5) -> list[str]:
    """Extract quotable highlights from a YouTube transcript.

    Filters filler (subscribe, welcome back, etc.), scores sentences by
    specificity (numbers, proper nouns, topic relevance), and returns
    the top highlights.
    """
    if not transcript:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', transcript)

    # Fallback for punctuation-free transcripts (common with auto-captions):
    # chunk into ~20-word segments so they pass the 8-50 word filter.
    if len(sentences) <= 1 and len(transcript.split()) > 50:
        words = transcript.split()
        sentences = [' '.join(words[i:i+20]) for i in range(0, len(words), 20)]

    filler = [
        r"^(hey |hi |what's up|welcome back|in today's video|don't forget to)",
        r"(subscribe|like and comment|hit the bell|check out the link|down below)",
        r"^(so |and |but |okay |alright |um |uh )",
        r"(thanks for watching|see you (next|in the)|bye)",
    ]

    topic_words = [w.lower() for w in topic.lower().split() if len(w) > 2]

    candidates = []
    for sent in sentences:
        sent = sent.strip()
        words = sent.split()
        if len(words) < 8 or len(words) > 50:
            continue
        if any(re.search(p, sent, re.IGNORECASE) for p in filler):
            continue

        score = 0
        if re.search(r'\d', sent):
            score += 2
        if re.search(r'[A-Z][a-z]+', sent):
            score += 1
        if '?' in sent:
            score += 1
        sent_lower = sent.lower()
        if any(w in sent_lower for w in topic_words):
            score += 2

        candidates.append((score, sent))

    candidates.sort(key=lambda x: -x[0])
    return [sent for _, sent in candidates[:limit]]


def _log(msg: str):
    log.source_log("YouTube", msg, tty_only=False)


def is_ytdlp_installed() -> bool:
    """Local binary transcript extraction is disabled in the hosted runtime."""
    return False


def transcript_enrichment_enabled() -> bool:
    """Return True when optional transcript enrichment is explicitly enabled."""
    raw = (os.environ.get("LAST30DAYS_YOUTUBE_TRANSCRIPTS") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for YouTube search.

    NOTE: 'tips', 'tricks', 'tutorial', 'guide', 'review', 'reviews'
    are intentionally KEPT — they're YouTube content types that improve search.
    """
    from .query import extract_core_subject
    # YouTube-specific noise set: smaller than default, keeps content-type words
    _YT_NOISE = frozenset({
        'best', 'top', 'good', 'great', 'awesome', 'killer',
        'latest', 'new', 'news', 'update', 'updates',
        'trending', 'hottest', 'popular', 'viral',
        'practices', 'features',
        'recommendations', 'advice',
        'prompt', 'prompts', 'prompting',
        'methods', 'strategies', 'approaches',
        # Temporal/meta words — planner generates these but they don't
        # appear in YouTube titles, so strip them for better search.
        'last', 'days', 'recent', 'recently', 'month', 'week',
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        '2025', '2026', '2027',
        'music', 'public', 'appearances', 'developments', 'discussions', 'coverage',
    })
    return extract_core_subject(topic, noise=_YT_NOISE)


def _infer_query_intent(topic: str) -> str:
    """Tiny local intent classifier for YouTube query expansion."""
    text = topic.lower().strip()
    if re.search(r"\b(vs|versus|compare|difference between)\b", text):
        return "comparison"
    if re.search(r"\b(how to|tutorial|guide|setup|step by step|deploy|install|configure|troubleshoot|error|fix|debug)\b", text):
        return "how_to"
    if re.search(r"\b(thoughts on|worth it|should i|opinion|review)\b", text):
        return "opinion"
    if re.search(r"\b(pricing|feature|features|best .* for)\b", text):
        return "product"
    return "breaking_news"


def expand_youtube_queries(topic: str, depth: str) -> List[str]:
    """Generate multiple YouTube search queries from a topic.

    Mirrors reddit.py's expand_reddit_queries() pattern:
    1. Extract core subject (strip noise words)
    2. Include original topic if different from core
    3. Add intent-specific OR-joined content-type variants
    4. Cap by depth: 1 for quick, 2 for default, 3 for deep

    Returns 1-3 query strings depending on depth.
    """
    core = _extract_core_subject(topic)
    queries = [core]

    # Include cleaned original topic as variant if different from core
    original_clean = topic.strip().rstrip('?!.')
    if core.lower() != original_clean.lower() and len(original_clean.split()) <= 8:
        queries.append(original_clean)

    qtype = _infer_query_intent(topic)

    # Intent-specific YouTube content-type variants
    if qtype == "opinion":
        queries.append(f"{core} review OR reaction OR breakdown")
    elif qtype == "product":
        queries.append(f"{core} review OR comparison OR unboxing")
    elif qtype == "comparison":
        queries.append(f"{core} vs OR compared OR head to head")
    elif qtype == "how_to":
        queries.append(f"{core} tutorial OR guide OR explained")
    else:
        # breaking_news / general — YouTube content types
        queries.append(f"{core} review OR reaction OR breakdown")

    # Deep depth: add full-length content variant
    if depth == "deep":
        queries.append(f"{core} full OR complete OR official")

    # Cap by depth budget
    caps = {"quick": 1, "default": 2, "deep": 3}
    cap = caps.get(depth, 2)
    return queries[:cap]


def search_youtube(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
) -> Dict[str, Any]:
    """Search YouTube via the AISA proxy.

    Args:
        topic: Search topic
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'

    Returns:
        Dict with 'items' list of video metadata dicts.
    """
    del to_date
    api_key = os.environ.get("AISA_API_KEY", "")
    if not api_key:
        return {"items": [], "error": "AISA_API_KEY not configured"}
    core_topic = _extract_core_subject(topic)
    _log(f"Searching YouTube via AISA for '{core_topic}'")
    items = aisa.parse_youtube_response(
        aisa.search_youtube(api_key, core_topic, depth=depth),
        topic=core_topic,
        from_date=from_date,
    )
    items.sort(key=lambda x: x.get("engagement", {}).get("views", 0), reverse=True)
    return {"items": items}


def _clean_vtt(vtt_text: str) -> str:
    """Convert VTT subtitle format to clean plaintext."""
    # Strip VTT header
    text = re.sub(r'^WEBVTT.*?\n\n', '', vtt_text, flags=re.DOTALL)
    # Strip timestamps
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*\n', '', text)
    # Strip position/alignment tags
    text = re.sub(r'<[^>]+>', '', text)
    # Strip cue numbers
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    # Deduplicate overlapping lines
    lines = text.strip().split('\n')
    seen = set()
    unique = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique.append(stripped)
    return re.sub(r'\s+', ' ', ' '.join(unique)).strip()


_YT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def _fetch_transcript_direct(video_id: str, timeout: int = 30) -> Optional[str]:
    """Fetch YouTube transcript via direct HTTP without local binary helpers.

    Scrapes the watch page HTML for the captions track URL in
    ytInitialPlayerResponse, then fetches the VTT subtitle file.

    Args:
        video_id: YouTube video ID
        timeout: HTTP request timeout in seconds

    Returns:
        Raw VTT text, or None if captions are unavailable.
    """
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": _YT_USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Step 1: Fetch the watch page HTML
    req = urllib.request.Request(watch_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
        _log(f"Direct transcript: failed to fetch watch page for {video_id}: {exc}")
        return None

    # Step 2: Extract captions URL from ytInitialPlayerResponse
    # YouTube embeds this as a JS variable in the page HTML
    match = re.search(
        r'ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;(?:\s*var\s|\s*<\/script>)',
        html,
    )
    if not match:
        # Fallback: try the JSON embedded in the script tag
        match = re.search(
            r'var\s+ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;',
            html,
        )
    if not match:
        _log(f"Direct transcript: no ytInitialPlayerResponse found for {video_id}")
        return None

    try:
        player_response = json.loads(match.group(1))
    except json.JSONDecodeError:
        _log(f"Direct transcript: failed to parse ytInitialPlayerResponse for {video_id}")
        return None

    # Navigate to caption tracks
    captions = player_response.get("captions", {})
    renderer = captions.get("playerCaptionsTracklistRenderer", {})
    caption_tracks = renderer.get("captionTracks", [])

    if not caption_tracks:
        _log(f"Direct transcript: no caption tracks for {video_id}")
        return None

    # Find English track (prefer exact 'en', then any en variant, then first track)
    base_url = None
    for track in caption_tracks:
        lang = track.get("languageCode", "")
        if lang == "en":
            base_url = track.get("baseUrl")
            break
    if not base_url:
        for track in caption_tracks:
            lang = track.get("languageCode", "")
            if lang.startswith("en"):
                base_url = track.get("baseUrl")
                break
    if not base_url:
        # Fall back to first available track
        base_url = caption_tracks[0].get("baseUrl")
    if not base_url:
        _log(f"Direct transcript: no baseUrl in caption tracks for {video_id}")
        return None

    # Step 3: Fetch the VTT subtitle file
    sep = "&" if "?" in base_url else "?"
    vtt_url = f"{base_url}{sep}fmt=vtt"
    vtt_req = urllib.request.Request(vtt_url, headers=headers)
    try:
        with urllib.request.urlopen(vtt_req, timeout=timeout) as resp:
            vtt_text = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as exc:
        _log(f"Direct transcript: failed to fetch VTT for {video_id}: {exc}")
        return None

    if not vtt_text or not vtt_text.strip():
        return None

    return vtt_text


def _fetch_transcript_ytdlp(video_id: str, temp_dir: str) -> Optional[str]:
    """Local-binary transcript extraction is disabled.

    Args:
        video_id: YouTube video ID
        temp_dir: Temporary directory for subtitle files

    Returns:
        Raw VTT text, or None if no captions available.
    """
    del video_id, temp_dir
    return None


def fetch_transcript(video_id: str, temp_dir: str) -> Optional[str]:
    """Fetch auto-generated transcript for a YouTube video.

    Uses the direct HTTP transcript path only.

    Args:
        video_id: YouTube video ID
        temp_dir: Temporary directory for subtitle files

    Returns:
        Plaintext transcript string, or None if no captions available.
    """
    del temp_dir
    _log("Using direct HTTP transcript fetch")
    raw_vtt = _fetch_transcript_direct(video_id)

    if not raw_vtt:
        _log(f"No transcript available for {video_id} (no captions found)")
        return None

    transcript = _clean_vtt(raw_vtt)

    # Truncate to max words
    words = transcript.split()
    if len(words) > TRANSCRIPT_MAX_WORDS:
        transcript = ' '.join(words[:TRANSCRIPT_MAX_WORDS]) + '...'

    return transcript if transcript else None


def fetch_transcripts_parallel(
    video_ids: List[str],
    max_workers: int = 5,
) -> Dict[str, Optional[str]]:
    """Fetch transcripts for multiple videos in parallel.

    Args:
        video_ids: List of YouTube video IDs
        max_workers: Max parallel fetches

    Returns:
        Dict mapping video_id to transcript text (or None).
    """
    if not video_ids:
        return {}

    _log(f"Fetching transcripts for {len(video_ids)} videos")

    results = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(fetch_transcript, vid, temp_dir): vid
                for vid in video_ids
            }
            for future in as_completed(futures):
                vid = futures[future]
                try:
                    results[vid] = future.result()
                except (OSError, subprocess.SubprocessError) as exc:
                    _log(f"Transcript fetch error for {vid}: {exc}")
                    results[vid] = None
                except Exception as exc:
                    _log(f"Unexpected transcript error for {vid}: {type(exc).__name__}: {exc}")
                    results[vid] = None

    got = sum(1 for v in results.values() if v)
    errors = sum(1 for v in results.values() if v is None)
    _log(f"Got transcripts for {got}/{len(video_ids)} videos ({errors} failed)")
    return results


def search_and_transcribe(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    *,
    enrich_transcripts: bool | None = None,
) -> Dict[str, Any]:
    """Full YouTube search using the hosted AISA path.

    Uses expand_youtube_queries() to generate multiple search queries, runs the
    hosted AISA search path for each, and merges/deduplicates results by video ID.
    Transcript enrichment is optional and disabled by default so the primary
    runtime path stays fully AISA-only.

    Args:
        topic: Search topic
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: 'quick', 'default', or 'deep'

    Returns:
        Dict with 'items' list. Each item has a 'transcript_snippet' field.
    """
    if enrich_transcripts is None:
        enrich_transcripts = transcript_enrichment_enabled()

    # Step 1: Multi-query search via the hosted AISA YouTube path
    queries = expand_youtube_queries(topic, depth)
    seen_ids: Set[str] = set()
    items: List[Dict[str, Any]] = []
    for q in queries:
        search_result = search_youtube(q, from_date, to_date, depth)
        for item in search_result.get("items", []):
            vid = item.get("video_id", "")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                items.append(item)

    # Sort merged results by views descending
    items.sort(key=lambda x: x.get("engagement", {}).get("views", 0), reverse=True)

    if not items:
        return search_result

    transcripts: Dict[str, Optional[str]] = {}
    transcript_limit = TRANSCRIPT_LIMITS.get(depth, TRANSCRIPT_LIMITS["default"])
    if enrich_transcripts and transcript_limit > 0:
        # Try more candidates than the limit because some videos (music videos,
        # short clips) lack captions. Attempt up to 3x the limit so we have a
        # good chance of reaching the target number of successful transcripts.
        attempt_count = min(len(items), transcript_limit * 3)
        candidate_ids = [item["video_id"] for item in items[:attempt_count]]
        _log(f"Fetching transcripts for up to {attempt_count} videos (target: {transcript_limit}): {candidate_ids}")
        transcripts = fetch_transcripts_parallel(candidate_ids)
    elif enrich_transcripts:
        _log(f"Transcript limit is 0 for depth={depth}, skipping transcript fetch")
    else:
        _log("Transcript enrichment disabled; using AISA YouTube search results only")

    # Step 3: Attach transcripts and extract highlights
    core_topic = _extract_core_subject(topic)
    for item in items:
        vid = item["video_id"]
        transcript = transcripts.get(vid)
        item["transcript_snippet"] = transcript or ""
        item["transcript_highlights"] = extract_transcript_highlights(
            transcript or "", core_topic,
        )

    return {"items": items}


def parse_youtube_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse YouTube search response to normalized format.

    Returns:
        List of item dicts ready for normalization.
    """
    return response.get("items", [])


# ---------------------------------------------------------------------------
# Optional YouTube enrichers
# ---------------------------------------------------------------------------


def _total_engagement(item: Dict[str, Any]) -> int:
    """Combined engagement score for ranking which videos to enrich."""
    eng = item.get("engagement", {})
    views = eng.get("views", 0) or 0
    likes = eng.get("likes", 0) or 0
    comments = eng.get("comments", 0) or 0
    return views + likes + comments


def enrich_with_comments(
    items: List[Dict[str, Any]],
    token: str,
    max_videos: int = 3,
    max_comments: int = 5,
) -> List[Dict[str, Any]]:
    """Comment enrichment is disabled in the AISA-only runtime.

    Args:
        items: YouTube items from search_and_transcribe() or search_youtube_sc()
        token: Unused; kept for local compatibility
        max_videos: How many videos to enrich with comments
        max_comments: Max comments to keep per video

    Returns:
        Items list (mutated in place) with top_comments added to enriched items.
    """
    del token, max_videos, max_comments
    return items


def _fetch_video_comments(
    video_id: str,
    token: str,
    max_comments: int = 5,
) -> List[Dict[str, Any]]:
    """Comment fetch helper is disabled in the AISA-only runtime."""
    del video_id, token, max_comments
    return []


def search_youtube_sc(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    token: str = None,
) -> Dict[str, Any]:
    """Compatibility wrapper around the AISA YouTube search path."""
    del token
    return search_youtube(topic, from_date, to_date, depth=depth)


def _sc_youtube_search(keyword: str, token: str) -> List[Dict[str, Any]]:
    """Compatibility wrapper around the AISA YouTube search path."""
    del token
    return search_youtube(keyword, "", "", depth="default").get("items", [])


def _sc_fetch_transcript(video_id: str, token: str) -> Optional[str]:
    """Transcript compatibility helper is disabled in the AISA-only runtime."""
    del video_id, token
    return None
