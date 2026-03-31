#!/usr/bin/env python3
"""Shared unresolved merge-marker scanning helpers."""

from __future__ import annotations

from pathlib import Path


DEFAULT_EXCLUDED_PREFIXES = ("artifacts/blueprint/conflicts/",)
DEFAULT_EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "artifacts",
}


def _is_scan_excluded(
    relative_path: str,
    *,
    excluded_prefixes: tuple[str, ...],
    excluded_dir_names: set[str],
) -> bool:
    if any(relative_path.startswith(prefix) for prefix in excluded_prefixes):
        return True
    parts = Path(relative_path).parts
    return any(part in excluded_dir_names for part in parts)


def find_merge_markers(
    repo_root: Path,
    *,
    excluded_prefixes: tuple[str, ...] = DEFAULT_EXCLUDED_PREFIXES,
    excluded_dir_names: set[str] | None = None,
) -> list[str]:
    """Return unresolved merge marker locations as ``path:line:content`` strings."""
    effective_excluded_dir_names = (
        DEFAULT_EXCLUDED_DIR_NAMES if excluded_dir_names is None else excluded_dir_names
    )
    markers: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root).as_posix()
        if _is_scan_excluded(
            relative,
            excluded_prefixes=excluded_prefixes,
            excluded_dir_names=effective_excluded_dir_names,
        ):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()
        except OSError:
            continue
        in_conflict = False
        for line_number, line in enumerate(lines, start=1):
            stripped = line.rstrip()
            if stripped.startswith("<<<<<<<"):
                in_conflict = True
                markers.append(f"{relative}:{line_number}:{line}")
                continue
            if stripped == "=======" and in_conflict:
                markers.append(f"{relative}:{line_number}:{line}")
                continue
            if stripped.startswith(">>>>>>>") and in_conflict:
                markers.append(f"{relative}:{line_number}:{line}")
                in_conflict = False
    return markers
