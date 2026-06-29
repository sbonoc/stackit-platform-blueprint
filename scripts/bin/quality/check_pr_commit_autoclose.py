#!/usr/bin/env python3
"""Pre-push check: scan PR title/body and branch commit messages for GitHub
auto-close keywords targeting must-not-auto-close issues.

Protected issue source (REQ-001):
  1. `Tracks #N` markers in the open PR body (via `gh pr view`).
  2. `.github/no-auto-close-issues.yml` fallback when no open PR exists.
  3. Exit 0 (no-op) when both are absent.

Scanned surfaces (REQ-002):
  - PR title
  - PR body
  - Every commit subject + body on the branch since origin/main.

Override (REQ-005): `#allow-auto-close: #N1,#N2` in PR body excludes those
issue numbers from the protected set for this invocation.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.quality.autoclose_regex import build_pattern  # noqa: E402

# Default config path relative to repo root (REQ-001 fallback).
_DEFAULT_CONFIG = REPO_ROOT / ".github" / "no-auto-close-issues.yml"

_TRACKS_RE = re.compile(r"Tracks\s+#(\d+)", re.IGNORECASE)
_ALLOW_RE = re.compile(r"#allow-auto-close:\s*((?:#\d+(?:,\s*)?)+)", re.IGNORECASE)
_ALLOW_NUM_RE = re.compile(r"#(\d+)")


# ---------------------------------------------------------------------------
# Public API (imported by tests)
# ---------------------------------------------------------------------------

def fetch_pr_body_title() -> dict[str, str] | None:
    """Call `gh pr view` once and return {body, title}, or None on failure.

    NFR-REL-001: returns None (instead of raising) when gh is unavailable or
    no open PR exists so the caller can fall back gracefully.
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "body,title"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        import json
        return json.loads(result.stdout)
    except Exception:
        return None


def parse_protected_issues(pr_body: str) -> set[int]:
    """Extract protected issue numbers from *pr_body* (Tracks #N minus overrides)."""
    protected: set[int] = set(_int(m) for m in _TRACKS_RE.findall(pr_body))
    # Apply per-PR allow-override (REQ-005).
    for allow_match in _ALLOW_RE.finditer(pr_body):
        for num_match in _ALLOW_NUM_RE.finditer(allow_match.group(1)):
            protected.discard(_int(num_match.group(1)))
    return protected


def load_protected_from_config(config_path: Path) -> set[int]:
    """Read issue numbers from a YAML config file; returns empty set when absent."""
    if not config_path.exists():
        return set()
    try:
        import yaml  # type: ignore[import]
        data = yaml.safe_load(config_path.read_text()) or {}
        return {int(n) for n in data.get("issues", [])}
    except Exception:
        return set()


def get_protected_issues(config_path: Path = _DEFAULT_CONFIG) -> set[int]:
    """Resolve protected issue set from PR body or config fallback."""
    pr = fetch_pr_body_title()
    if pr is not None:
        body = pr.get("body") or ""
        protected = parse_protected_issues(body)
        return protected
    # Fallback: config file.
    return load_protected_from_config(config_path)


def scan_surface(text: str, surface_label: str, protected: set[int]) -> list[dict[str, Any]]:
    """Scan *text* for auto-close keywords targeting any protected issue."""
    findings: list[dict[str, Any]] = []
    for line in text.splitlines():
        for issue in protected:
            if build_pattern(issue).search(line):
                findings.append({"surface": surface_label, "line": line, "issue": issue})
    return findings


def scan_commit_log(log: str, protected: set[int]) -> list[dict[str, Any]]:
    """Scan git log output (format: hash\\nsubject\\nbody) for violations.

    REQ-002: scans subject + body of every commit; does NOT scan diffs.
    """
    if not protected:
        return []
    findings: list[dict[str, Any]] = []
    current_hash = None
    for raw_line in log.splitlines():
        # A 7–40 char hex token on its own line is a commit hash.
        if re.fullmatch(r"[0-9a-f]{7,40}", raw_line.strip()):
            current_hash = raw_line.strip()
            continue
        for issue in protected:
            if build_pattern(issue).search(raw_line):
                label = f"commit:{current_hash}" if current_hash else "commit:unknown"
                findings.append({"surface": label, "line": raw_line, "issue": issue})
    return findings


def _get_commit_log() -> str:
    """Return git log for commits on branch since origin/main."""
    try:
        result = subprocess.run(
            ["git", "log", "origin/main..HEAD", "--pretty=format:%H%n%s%n%b"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def _int(val: str) -> int:
    return int(val)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    protected = get_protected_issues()
    if not protected:
        print("[autoclose-check] no protected issues — skipping (exit 0)", flush=True)
        return 0

    all_findings: list[dict[str, Any]] = []

    # Scan PR title + body.
    pr = fetch_pr_body_title()
    if pr is not None:
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        all_findings.extend(scan_surface(title, "PR title", protected))
        all_findings.extend(scan_surface(body, "PR body", protected))

    # Scan commit log (REQ-002).
    log = _get_commit_log()
    all_findings.extend(scan_commit_log(log, protected))

    if not all_findings:
        print("[autoclose-check] clean — no auto-close violations found (exit 0)", flush=True)
        return 0

    print("[autoclose-check] VIOLATIONS FOUND:", flush=True)
    for f in all_findings:
        print(
            f"  surface={f['surface']!r}  issue=#{f['issue']}  line={f['line']!r}",
            flush=True,
        )
        print(
            f"  -> Add '#allow-auto-close: #{f['issue']}' to the PR body to suppress.",
            flush=True,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
