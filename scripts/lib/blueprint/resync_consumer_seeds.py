#!/usr/bin/env python3
"""Resync generated-consumer seeded files from current consumer templates."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import render_template, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.init_repo_contract import load_blueprint_contract_for_init  # noqa: E402


CLASS_UP_TO_DATE = "up-to-date"
CLASS_AUTO_REFRESH = "auto-refresh"
CLASS_MANUAL_MERGE = "manual-merge"

MODE_DRY_RUN = "dry-run"
MODE_APPLY_SAFE = "apply-safe"
MODE_APPLY_ALL = "apply-all"

UNRESOLVED_TEMPLATE_TOKEN_PATTERN = re.compile(r"(?<!\$)\{\{[^{}\n]+\}\}")


@dataclass(frozen=True)
class SeedResyncEntry:
    path: str
    status: str
    action: str
    classification: str
    reason: str
    tracked: bool
    dirty: bool
    commit_count: int | None
    expected_content: str

    def as_report_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "status": self.status,
            "action": self.action,
            "classification": self.classification,
            "reason": self.reason,
            "tracked": self.tracked,
            "dirty": self.dirty,
            "commit_count": self.commit_count,
        }


class GitInspector:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._available: bool | None = None

    def available(self) -> bool:
        if self._available is not None:
            return self._available
        result = self._run_git("rev-parse", "--is-inside-work-tree")
        self._available = result.returncode == 0 and result.stdout.strip() == "true"
        return self._available

    def is_tracked(self, relative_path: str) -> bool:
        if not self.available():
            return False
        result = self._run_git("ls-files", "--error-unmatch", "--", relative_path)
        return result.returncode == 0

    def has_worktree_changes(self, relative_path: str) -> bool:
        if not self.available():
            return False
        result = self._run_git("status", "--porcelain", "--", relative_path)
        return result.returncode == 0 and bool(result.stdout.strip())

    def commit_count(self, relative_path: str) -> int | None:
        if not self.available():
            return None
        result = self._run_git("rev-list", "--count", "HEAD", "--", relative_path)
        if result.returncode != 0:
            return None
        try:
            return int(result.stdout.strip())
        except ValueError:
            return None

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            check=False,
            text=True,
            capture_output=True,
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Defaults to inferring from this script location.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Preview only (default).")
    mode_group.add_argument(
        "--apply-safe",
        action="store_true",
        help="Apply only auto-refresh changes (missing files and untouched seed files).",
    )
    mode_group.add_argument(
        "--apply-all",
        action="store_true",
        help="Apply all detected updates, including files classified as manual-merge.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional JSON report output path (absolute or repo-relative).",
    )
    return parser.parse_args()


def _resolve_mode(args: argparse.Namespace) -> str:
    if args.apply_safe:
        return MODE_APPLY_SAFE
    if args.apply_all:
        return MODE_APPLY_ALL
    return MODE_DRY_RUN


def _template_replacements(repo_root: Path) -> dict[str, str]:
    contract = load_blueprint_contract_for_init(repo_root)
    repo_name = str(contract.raw.get("metadata", {}).get("name", "")).strip() or repo_root.name
    return {
        "REPO_NAME": repo_name,
        "DEFAULT_BRANCH": contract.repository.default_branch,
        "TEMPLATE_VERSION": contract.repository.template_bootstrap.template_version,
    }


def _unresolved_template_tokens(content: str) -> list[str]:
    return sorted({match.group(0) for match in UNRESOLVED_TEMPLATE_TOKEN_PATTERN.finditer(content)})


def _classify_entry(
    *,
    relative_path: str,
    expected_content: str,
    current_content: str | None,
    git: GitInspector,
) -> SeedResyncEntry:
    if current_content is None:
        tracked = git.is_tracked(relative_path)
        dirty = git.has_worktree_changes(relative_path)
        commit_count = git.commit_count(relative_path) if tracked else None
        return SeedResyncEntry(
            path=relative_path,
            status="missing",
            action="create",
            classification=CLASS_AUTO_REFRESH,
            reason="missing file; safe to recreate from template seed",
            tracked=tracked,
            dirty=dirty,
            commit_count=commit_count,
            expected_content=expected_content,
        )

    if current_content == expected_content:
        tracked = git.is_tracked(relative_path)
        commit_count = git.commit_count(relative_path) if tracked else None
        return SeedResyncEntry(
            path=relative_path,
            status="in-sync",
            action="none",
            classification=CLASS_UP_TO_DATE,
            reason="already matches current template seed",
            tracked=tracked,
            dirty=False,
            commit_count=commit_count,
            expected_content=expected_content,
        )

    tracked = git.is_tracked(relative_path)
    dirty = git.has_worktree_changes(relative_path)
    commit_count = git.commit_count(relative_path) if tracked else None

    if not tracked:
        return SeedResyncEntry(
            path=relative_path,
            status="drifted",
            action="update",
            classification=CLASS_MANUAL_MERGE,
            reason="file differs from template and is not tracked by git",
            tracked=False,
            dirty=dirty,
            commit_count=None,
            expected_content=expected_content,
        )

    if dirty:
        return SeedResyncEntry(
            path=relative_path,
            status="drifted",
            action="update",
            classification=CLASS_MANUAL_MERGE,
            reason="file has local working-tree changes",
            tracked=True,
            dirty=True,
            commit_count=commit_count,
            expected_content=expected_content,
        )

    if commit_count is not None and commit_count <= 2:
        return SeedResyncEntry(
            path=relative_path,
            status="drifted",
            action="update",
            classification=CLASS_AUTO_REFRESH,
            reason="one or two commits touched this path; treated as untouched seed/init rewrite",
            tracked=True,
            dirty=False,
            commit_count=commit_count,
            expected_content=expected_content,
        )

    if commit_count is None:
        reason = "git history unavailable; requires manual merge"
    else:
        reason = f"{commit_count} commits touched this path; requires manual merge"
    return SeedResyncEntry(
        path=relative_path,
        status="drifted",
        action="update",
        classification=CLASS_MANUAL_MERGE,
        reason=reason,
        tracked=True,
        dirty=False,
        commit_count=commit_count,
        expected_content=expected_content,
    )


def _should_apply(entry: SeedResyncEntry, mode: str) -> bool:
    if entry.action == "none":
        return False
    if mode == MODE_DRY_RUN:
        return False
    if mode == MODE_APPLY_ALL:
        return True
    return entry.classification == CLASS_AUTO_REFRESH


def _plan_entries(repo_root: Path, git: GitInspector) -> list[SeedResyncEntry]:
    contract = load_blueprint_contract_for_init(repo_root)
    repository = contract.repository
    template_root = repo_root / repository.consumer_init.template_root
    replacements = _template_replacements(repo_root)

    entries: list[SeedResyncEntry] = []
    for relative_path in repository.consumer_seeded_paths:
        target_path = repo_root / relative_path
        template_path = template_root / f"{relative_path}.tmpl"
        if not template_path.is_file():
            raise FileNotFoundError(
                "missing consumer template for seeded path "
                f"{relative_path}: {template_path.relative_to(repo_root).as_posix()}"
            )
        expected_content = render_template(template_path.read_text(encoding="utf-8"), replacements)
        unresolved_tokens = _unresolved_template_tokens(expected_content)
        if unresolved_tokens:
            template_relative_path = template_path.relative_to(repo_root).as_posix()
            raise ValueError(
                "unresolved consumer template token(s) in "
                f"{relative_path} (template {template_relative_path}): {', '.join(unresolved_tokens)}"
            )
        current_content = target_path.read_text(encoding="utf-8") if target_path.is_file() else None
        entries.append(
            _classify_entry(
                relative_path=relative_path,
                expected_content=expected_content,
                current_content=current_content,
                git=git,
            )
        )
    return entries


def _apply_entries(repo_root: Path, entries: list[SeedResyncEntry], mode: str) -> int:
    applied = 0
    for entry in entries:
        if not _should_apply(entry, mode):
            continue
        target_path = repo_root / entry.path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(entry.expected_content, encoding="utf-8")
        applied += 1
    return applied


def _summarize(entries: list[SeedResyncEntry], applied: int) -> dict[str, int]:
    return {
        "total": len(entries),
        "in_sync": sum(entry.status == "in-sync" for entry in entries),
        "missing": sum(entry.status == "missing" for entry in entries),
        "drifted": sum(entry.status == "drifted" for entry in entries),
        "auto_refresh": sum(entry.classification == CLASS_AUTO_REFRESH for entry in entries),
        "manual_merge": sum(entry.classification == CLASS_MANUAL_MERGE for entry in entries),
        "applied": applied,
    }


def _print_report(entries: list[SeedResyncEntry], summary: dict[str, int], mode: str) -> None:
    print(f"consumer-seed-resync mode={mode}")
    for entry in entries:
        print(
            f"{entry.classification}: {entry.path} "
            f"(status={entry.status} action={entry.action}) - {entry.reason}"
        )
    print(
        "summary: "
        f"total={summary['total']} "
        f"in_sync={summary['in_sync']} "
        f"missing={summary['missing']} "
        f"drifted={summary['drifted']} "
        f"auto_refresh={summary['auto_refresh']} "
        f"manual_merge={summary['manual_merge']} "
        f"applied={summary['applied']}"
    )


def _write_json_report(
    report_path_value: str | None,
    repo_root: Path,
    mode: str,
    entries: list[SeedResyncEntry],
    summary: dict[str, int],
) -> None:
    if not report_path_value:
        return
    repo_root_resolved = repo_root.resolve()
    report_path = Path(report_path_value)
    if not report_path.is_absolute():
        report_path = (repo_root / report_path).resolve()
        try:
            report_path.relative_to(repo_root_resolved)
        except ValueError as exc:
            raise ValueError(
                "--report-path must stay within the repository root when using a relative path"
            ) from exc
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "repo_root": str(repo_root),
        "entries": [entry.as_report_dict() for entry in entries],
        "summary": summary,
    }
    report_path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")
    print(f"report: {report_path}")


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    contract = load_blueprint_contract_for_init(repo_root)

    if contract.repository.repo_mode != contract.repository.consumer_init.mode_to:
        print(
            "blueprint-resync-consumer-seeds is only supported for generated-consumer repositories "
            f"(repo_mode={contract.repository.repo_mode})",
            file=sys.stderr,
        )
        return 1

    mode = _resolve_mode(args)
    git = GitInspector(repo_root)
    try:
        entries = _plan_entries(repo_root, git)
        applied = _apply_entries(repo_root, entries, mode)
        summary = _summarize(entries, applied)
        _print_report(entries, summary, mode)
        _write_json_report(args.report_path, repo_root, mode, entries, summary)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
