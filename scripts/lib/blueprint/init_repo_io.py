"""Filesystem helpers for blueprint init-repo orchestration."""

from __future__ import annotations

from pathlib import Path
import shutil

from scripts.lib.blueprint.cli_support import ChangeSummary


def read_existing_or_template(
    repo_root: Path,
    path: Path,
    template_root: Path,
    template_rel: str,
) -> tuple[str | None, str]:
    if path.is_file():
        original = path.read_text(encoding="utf-8")
        return original, original
    template_path = repo_root / template_root / template_rel
    return None, template_path.read_text(encoding="utf-8")


def apply_file_update(
    path: Path,
    original: str | None,
    updated: str,
    dry_run: bool,
    summary: ChangeSummary,
) -> bool:
    original_content = original if original is not None else ""
    changed = original is None or updated != original_content
    if not changed:
        summary.skipped_path(path, "no change required")
        return False

    if dry_run:
        if original is None:
            summary.created_path(path)
        else:
            summary.updated_path(path)
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    if original is None:
        summary.created_path(path)
    else:
        summary.updated_path(path)
    return True


def remove_path(path: Path, dry_run: bool, summary: ChangeSummary) -> bool:
    if not path.exists() and not path.is_symlink():
        summary.skipped_path(path, "already absent")
        return False

    if dry_run:
        summary.removed_path(path)
        return True

    # Never follow symlinked directories while pruning scaffolded paths.
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    summary.removed_path(path)
    return True
