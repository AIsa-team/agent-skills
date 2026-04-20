#!/usr/bin/env python3
"""Run the v3 verification bundle for last30days."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_dev_python() -> str:
    for candidate in (
        "/usr/local/python3.12/bin/python3.12",
        "python3.14",
        "python3.13",
        "python3.12",
        sys.executable,
        "python3",
    ):
        try:
            probe = subprocess.run(
                [candidate, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            continue
        if probe.returncode == 0:
            return candidate
    raise RuntimeError("last30days verification requires Python 3.12+")


PYTHON = resolve_dev_python()
LIVE_SMOKE_TIMEOUT = int(os.environ.get("LAST30DAYS_VERIFY_SMOKE_TIMEOUT", "180"))
MOCK_SMOKE_TIMEOUT = int(os.environ.get("LAST30DAYS_VERIFY_MOCK_TIMEOUT", "120"))

SMOKE_TOPIC = "openclaw skills"
SMOKE_CASES = [
    ("aisa", ["--quick", "--search=grounding,hackernews"]),
    ("aisa", ["--quick", "--search=reddit,hackernews"]),
    ("aisa", ["--quick", "--search=reddit,grounding,hackernews"]),
    ("auto", ["--quick", "--search=reddit,grounding,hackernews"]),
]

LATENCY_TOPICS = [
    "openclaw skills",
    "codex vs claude code",
    "anthropic odds",
]
LATENCY_PROFILES = [
    ("quick", ["--quick", "--search=grounding,hackernews"]),
    ("default", ["--search=grounding,hackernews"]),
    ("deep", ["--deep", "--search=grounding,hackernews"]),
]

CURATED_TESTS = [
    "tests/test_aisa.py",
    "tests/test_env_v3.py",
    "tests/test_providers_v3.py",
    "tests/test_grounding_v3.py",
    "tests/test_setup_openclaw.py",
    "tests/test_setup_wizard.py",
    "tests/test_ui_v3.py",
    "tests/test_quality_nudge.py",
    "tests/test_tiktok.py",
    "tests/test_instagram.py",
    "tests/test_social_sources_v3.py",
    "tests/test_xquik.py",
    "tests/test_pipeline_v3.py",
]


def run_command(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=True,
    )


def verify_unit() -> dict[str, str]:
    existing_tests = [path for path in CURATED_TESTS if (REPO_ROOT / path).exists()]
    if existing_tests:
        run_command([PYTHON, "-m", "pytest", "--capture=no", *existing_tests], timeout=600)
    compile_roots = ["scripts"]
    if (REPO_ROOT / "tests").exists():
        compile_roots.append("tests")
    run_command(
        [
            PYTHON,
            "-m",
            "py_compile",
            *subprocess.run(
                ["rg", "--files", *compile_roots, "-g", "*.py", "-g", "!scripts/lib/vendor/**"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.split(),
        ],
        timeout=600,
    )
    return {"status": "ok" if existing_tests else "skipped-no-tests"}


def verify_diagnose() -> dict[str, object]:
    result = run_command([PYTHON, "scripts/last30days.py", "--diagnose"], timeout=120)
    return json.loads(result.stdout)


def verify_smoke() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    has_live_hosted = bool(os.environ.get("AISA_API_KEY"))
    smoke_timeout = LIVE_SMOKE_TIMEOUT if has_live_hosted else MOCK_SMOKE_TIMEOUT
    for provider, extra in SMOKE_CASES:
        env = os.environ.copy()
        env["LAST30DAYS_REASONING_PROVIDER"] = provider
        smoke_args = [PYTHON, "scripts/last30days.py", SMOKE_TOPIC, "--emit=json", *extra]
        if not has_live_hosted:
            smoke_args.append("--mock")
        start = time.time()
        print(
            f"[verify_v3] smoke start provider={provider} mode={'live' if has_live_hosted else 'mock'} timeout={smoke_timeout}s args={' '.join(extra)}",
            file=sys.stderr,
            flush=True,
        )
        try:
            result = run_command(smoke_args, env=env, timeout=smoke_timeout)
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start, 2)
            print(
                f"[verify_v3] smoke timeout provider={provider} after {duration}s",
                file=sys.stderr,
                flush=True,
            )
            rows.append(
                {
                    "provider": provider,
                    "mode": "live" if has_live_hosted else "mock",
                    "duration_seconds": duration,
                    "reasoning_provider": "aisa" if has_live_hosted else "aisa",
                    "cluster_count": 0,
                    "candidate_count": 0,
                    "error_sources": ["timeout"],
                }
            )
            continue
        duration = round(time.time() - start, 2)
        report = json.loads(result.stdout)
        row = {
            "provider": provider,
            "mode": "live" if has_live_hosted else "mock",
            "duration_seconds": duration,
            "reasoning_provider": (report.get("provider_runtime") or {}).get("reasoning_provider"),
            "cluster_count": len(report.get("clusters") or []),
            "candidate_count": len(report.get("ranked_candidates") or []),
            "error_sources": sorted((report.get("errors_by_source") or {}).keys()),
        }
        print(
            f"[verify_v3] smoke done provider={provider} duration={duration}s candidates={row['candidate_count']} clusters={row['cluster_count']} errors={','.join(row['error_sources']) or 'none'}",
            file=sys.stderr,
            flush=True,
        )
        rows.append(row)
    return rows


def verify_latency() -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for profile, extra in LATENCY_PROFILES:
        timings = []
        for topic in LATENCY_TOPICS:
            start = time.time()
            run_command(
                [PYTHON, "scripts/last30days.py", topic, "--emit=json", *extra],
                timeout=300,
            )
            timings.append(time.time() - start)
        results[profile] = {
            "times": [round(value, 2) for value in timings],
            "median_seconds": round(statistics.median(timings), 2),
            "max_seconds": round(max(timings), 2),
        }
    return results


def verify_eval(
    *,
    baseline: str,
    candidate: str,
    output_dir: str,
    quick: bool,
    limit: int,
    timeout: int,
) -> dict[str, object]:
    cmd = [
        PYTHON,
        "scripts/evaluate_search_quality.py",
        f"--baseline={baseline}",
        f"--candidate={candidate}",
        f"--output-dir={output_dir}",
        f"--limit={limit}",
        f"--timeout={timeout}",
    ]
    if quick:
        cmd.append("--quick")
    run_command(cmd, timeout=max(timeout * 8, 600))
    output = Path(output_dir)
    metrics = json.loads((output / "metrics.json").read_text())
    summary = (output / "summary.md").read_text()
    return {"metrics": metrics, "summary": summary}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the v3 verification bundle")
    parser.add_argument("--skip-eval", action="store_true", help="Skip the judged evaluator")
    parser.add_argument("--skip-latency", action="store_true", help="Skip live latency sampling")
    parser.add_argument("--baseline", default="HEAD~1")
    parser.add_argument("--candidate", default="WORKTREE")
    parser.add_argument("--output-dir", default="/tmp/last30days-v3-verify")
    parser.add_argument("--quick-eval", action="store_true", help="Use evaluator quick mode")
    parser.add_argument("--eval-limit", type=int, default=20)
    parser.add_argument("--eval-timeout", type=int, default=240)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary: dict[str, object] = {}
    summary["unit"] = verify_unit()
    summary["diagnose"] = verify_diagnose()
    summary["smoke"] = verify_smoke()
    if not args.skip_latency:
        summary["latency"] = verify_latency()
    if not args.skip_eval:
        summary["eval"] = verify_eval(
            baseline=args.baseline,
            candidate=args.candidate,
            output_dir=args.output_dir,
            quick=args.quick_eval,
            limit=args.eval_limit,
            timeout=args.eval_timeout,
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
