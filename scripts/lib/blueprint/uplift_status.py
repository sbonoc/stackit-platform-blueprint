#!/usr/bin/env python3
"""Report blueprint uplift convergence status for tracked issues in consumer backlog."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

# Matches Markdown link form: [#NNN](https://github.com/<org>/<repo>/issues/NNN)
# The org/repo portion is filled in at call time via _backlog_pattern().
_UNCHECKED_LINE = re.compile(r"^\s*-\s+\[ \]")


def _backlog_pattern(uplift_repo: str) -> re.Pattern[str]:
    """Return compiled regex for Markdown issue links in the given repo."""
    escaped = re.escape(uplift_repo)
    return re.compile(
        r"\[#(\d+)\]\(https://github\.com/" + escaped + r"/issues/\d+\)"
    )


@dataclass(frozen=True)
class UpliftEntry:
    issue_id: int
    line_text: str
    line_no: int


def _parse_backlog(backlog_path: Path, uplift_repo: str) -> list[UpliftEntry]:
    """Return one UpliftEntry per unchecked Markdown issue link in the backlog."""
    if not backlog_path.is_file():
        return []
    pattern = _backlog_pattern(uplift_repo)
    entries: list[UpliftEntry] = []
    for line_no, line in enumerate(
        backlog_path.read_text(encoding="utf-8", errors="surrogateescape").splitlines(),
        start=1,
    ):
        if not _UNCHECKED_LINE.match(line):
            continue
        for match in pattern.finditer(line):
            entries.append(UpliftEntry(int(match.group(1)), line.strip(), line_no))
    return entries


def _query_issue_state(issue_id: int, repo: str) -> str:
    """Query issue state via gh CLI. Returns OPEN, CLOSED, or UNKNOWN."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_id), "--repo", repo, "--json", "state", "--jq", ".state"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return "UNKNOWN"
        state = result.stdout.strip().upper()
        return state if state in ("OPEN", "CLOSED") else "UNKNOWN"
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _build_report(
    entries: list[UpliftEntry],
    issue_states: dict[int, str],
    query_failures: int,
    uplift_repo: str,
    backlog_path: str,
    strict_mode: bool,
    repo_root: Path,
) -> dict[str, object]:
    """Aggregate entries into the uplift status report dict."""
    # Deduplicate: group unresolved lines per issue_id
    unresolved_by_id: dict[int, int] = {}
    for entry in entries:
        unresolved_by_id[entry.issue_id] = unresolved_by_id.get(entry.issue_id, 0) + 1

    issues: list[dict[str, object]] = []
    open_count = 0
    closed_count = 0
    unknown_count = 0
    aligned_closed_count = 0
    action_required_count = 0
    action_required_issues: list[int] = []

    for issue_id in sorted(unresolved_by_id):
        state = issue_states.get(issue_id, "UNKNOWN")
        unresolved = unresolved_by_id[issue_id]

        if state == "OPEN":
            classification = "none"
            open_count += 1
        elif state == "CLOSED":
            closed_count += 1
            if unresolved > 0:
                classification = "required"
                action_required_count += 1
                action_required_issues.append(issue_id)
            else:
                classification = "aligned"
                aligned_closed_count += 1
        else:
            classification = "none"
            unknown_count += 1

        issues.append(
            {
                "issue_id": issue_id,
                "state": state,
                "unresolved_lines": unresolved,
                "classification": classification,
            }
        )

    tracked_total = len(unresolved_by_id)
    status = "failure" if (action_required_count > 0 or query_failures > 0 or unknown_count > 0) and strict_mode else "success"

    return {
        "repo_root": str(repo_root),
        "uplift_repo": uplift_repo,
        "backlog_path": backlog_path,
        "strict_mode": strict_mode,
        "tracked_total": tracked_total,
        "open_count": open_count,
        "closed_count": closed_count,
        "unknown_count": unknown_count,
        "aligned_closed_count": aligned_closed_count,
        "action_required_count": action_required_count,
        "action_required_issues": action_required_issues,
        "query_failures": query_failures,
        "timestamp_utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issues": issues,
        "status": status,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _print_table(report: dict[str, object]) -> None:
    issues = report.get("issues", [])
    if not isinstance(issues, list) or not issues:
        print("[blueprint-uplift-status] No tracked blueprint issues found in backlog.")
        return
    print(f"\n[blueprint-uplift-status] Uplift convergence status — repo: {report['uplift_repo']}")
    print(f"{'Issue':<10} {'State':<10} {'Unresolved':<12} {'Action'}")
    print("-" * 50)
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        print(
            f"#{issue['issue_id']:<9} {issue['state']:<10} {issue['unresolved_lines']:<12} {issue['classification']}"
        )
    print()
    print(
        f"  tracked={report['tracked_total']}  open={report['open_count']}"
        f"  closed={report['closed_count']}  aligned={report['aligned_closed_count']}"
        f"  action_required={report['action_required_count']}"
        f"  unknown={report['unknown_count']}  query_failures={report['query_failures']}"
    )
    if report["action_required_count"]:
        ids = ", ".join(f"#{i}" for i in report["action_required_issues"])
        print(f"\n  Action required for closed issues: {ids}")
        print("  Check off the relevant backlog lines or remove them once the upstream capability is adopted.")
    print()


def _emit_metrics(report: dict[str, object]) -> None:
    """Print key=value metric lines for the shell wrapper to consume."""
    for key in (
        "tracked_total",
        "open_count",
        "closed_count",
        "unknown_count",
        "aligned_closed_count",
        "action_required_count",
        "query_failures",
    ):
        print(f"{key}={report.get(key, 0)}")
    print(f"status={report.get('status', 'unknown')}")


def main(
    repo_root: Path | None = None,
    _issue_states_override: dict[int, str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--uplift-repo", default=None, help="GitHub org/repo of the upstream blueprint")
    parser.add_argument("--backlog-path", default="AGENTS.backlog.md")
    parser.add_argument("--output-path", type=Path, default=Path("artifacts/blueprint/uplift_status.json"))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--emit-metrics", action="store_true", help="Print key=value metric lines instead of table")
    args = parser.parse_args()

    if repo_root is None:
        repo_root = args.repo_root if args.repo_root is not None else REPO_ROOT

    uplift_repo: str = args.uplift_repo or ""
    if not uplift_repo:
        print(
            "[blueprint-uplift-status] BLUEPRINT_UPLIFT_REPO is not set; "
            "set it to <org>/<repo> of the upstream blueprint",
            file=sys.stderr,
        )
        return 1

    backlog_path = repo_root / args.backlog_path
    output_path = args.output_path if args.output_path.is_absolute() else repo_root / args.output_path

    entries = _parse_backlog(backlog_path, uplift_repo)

    # Collect unique issue IDs
    unique_ids = sorted({e.issue_id for e in entries})

    if _issue_states_override is not None:
        issue_states = _issue_states_override
        query_failures = 0
    else:
        issue_states: dict[int, str] = {}
        query_failures = 0
        for issue_id in unique_ids:
            state = _query_issue_state(issue_id, uplift_repo)
            issue_states[issue_id] = state
            if state == "UNKNOWN":
                query_failures += 1

    report = _build_report(
        entries=entries,
        issue_states=issue_states,
        query_failures=query_failures,
        uplift_repo=uplift_repo,
        backlog_path=args.backlog_path,
        strict_mode=args.strict,
        repo_root=repo_root,
    )

    _write_json(output_path, report)

    if args.emit_metrics:
        _emit_metrics(report)
    else:
        _print_table(report)

    if args.strict and (
        report["action_required_count"] > 0
        or report["query_failures"] > 0
        or report["unknown_count"] > 0
    ):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
