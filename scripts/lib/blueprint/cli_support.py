#!/usr/bin/env python3
"""Shared helpers for repo-rooted blueprint CLI tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def resolve_repo_root(explicit_repo_root: Path | str | None, script_path: str) -> Path:
    if explicit_repo_root is not None:
        return Path(explicit_repo_root).resolve()
    return Path(script_path).resolve().parents[3]


def resolve_repo_path(repo_root: Path, value: Path | str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def display_repo_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def render_template(content: str, replacements: dict[str, str]) -> str:
    rendered = content
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


@dataclass
class ChangeSummary:
    label: str
    created: int = 0
    updated: int = 0
    removed: int = 0
    skipped: int = 0

    def created_path(self, path: Path) -> None:
        self.created += 1
        print(f"created: {path}")

    def updated_path(self, path: Path) -> None:
        self.updated += 1
        print(f"updated: {path}")

    def removed_path(self, path: Path) -> None:
        self.removed += 1
        print(f"removed: {path}")

    def skipped_path(self, path: Path, reason: str) -> None:
        self.skipped += 1
        print(f"skipped: {path} ({reason})")

    def emit(self, dry_run: bool = False) -> None:
        prefix = "[dry-run] summary" if dry_run else "summary"
        print(
            f"{prefix}: {self.label} "
            f"(created={self.created} updated={self.updated} removed={self.removed} skipped={self.skipped})"
        )
