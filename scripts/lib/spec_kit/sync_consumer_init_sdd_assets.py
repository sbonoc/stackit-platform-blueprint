#!/usr/bin/env python3
"""Sync/check consumer-init SDD assets from canonical .spec-kit and specs sources."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, display_repo_path, resolve_repo_root  # noqa: E402


FILE_MIRRORS: tuple[tuple[Path, Path], ...] = (
    (Path(".spec-kit/policy-mapping.md"), Path("scripts/templates/consumer/init/.spec-kit/policy-mapping.md.tmpl")),
    (Path(".spec-kit/control-catalog.md"), Path("scripts/templates/consumer/init/.spec-kit/control-catalog.md.tmpl")),
    (Path(".spec-kit/control-catalog.json"), Path("scripts/templates/consumer/init/.spec-kit/control-catalog.json.tmpl")),
    (Path("specs/README.md"), Path("scripts/templates/consumer/init/specs/README.md.tmpl")),
)
SOURCE_TEMPLATE_DIR = Path(".spec-kit/templates/consumer")
TARGET_TEMPLATE_DIR = Path("scripts/templates/consumer/init/.spec-kit/templates/consumer")


def _list_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _sync_file(*, repo_root: Path, source: Path, target: Path, check: bool, out_of_sync: list[str], summary: ChangeSummary) -> None:
    if not source.is_file():
        raise ValueError(f"missing source SDD asset: {source}")

    source_content = source.read_text(encoding="utf-8")
    if target.is_file():
        current_content = target.read_text(encoding="utf-8")
        if current_content == source_content:
            summary.skipped_path(target, "already synchronized")
            return
        if check:
            out_of_sync.append(display_repo_path(repo_root, target))
            return
        target.write_text(source_content, encoding="utf-8")
        summary.updated_path(target)
        return

    if check:
        out_of_sync.append(display_repo_path(repo_root, target))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source_content, encoding="utf-8")
    summary.created_path(target)


def _sync_templates_directory(
    *,
    repo_root: Path,
    source_root: Path,
    target_root: Path,
    check: bool,
    out_of_sync: list[str],
    summary: ChangeSummary,
) -> None:
    if not source_root.is_dir():
        raise ValueError(f"missing canonical consumer template root: {source_root}")

    source_files = _list_files(source_root)
    target_files = _list_files(target_root)

    expected_targets: set[str] = set()

    for relative, source_path in source_files.items():
        target_relative = f"{relative}.tmpl"
        expected_targets.add(target_relative)
        target_path = target_root / target_relative

        source_content = source_path.read_text(encoding="utf-8")
        if target_path.is_file():
            target_content = target_path.read_text(encoding="utf-8")
            if target_content == source_content:
                summary.skipped_path(target_path, "already synchronized")
                continue
            if check:
                out_of_sync.append(display_repo_path(repo_root, target_path))
                continue
            target_path.write_text(source_content, encoding="utf-8")
            summary.updated_path(target_path)
            continue

        if check:
            out_of_sync.append(display_repo_path(repo_root, target_path))
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_content, encoding="utf-8")
        summary.created_path(target_path)

    extra = sorted(set(target_files) - expected_targets)
    for relative in extra:
        target_path = target_root / relative
        if check:
            out_of_sync.append(display_repo_path(repo_root, target_path))
            continue
        target_path.unlink()
        summary.removed_path(target_path)


def _sync(repo_root: Path, check: bool) -> int:
    summary = ChangeSummary("quality-sdd-sync-consumer-init-assets")
    out_of_sync: list[str] = []

    for source_rel, target_rel in FILE_MIRRORS:
        _sync_file(
            repo_root=repo_root,
            source=repo_root / source_rel,
            target=repo_root / target_rel,
            check=check,
            out_of_sync=out_of_sync,
            summary=summary,
        )

    _sync_templates_directory(
        repo_root=repo_root,
        source_root=repo_root / SOURCE_TEMPLATE_DIR,
        target_root=repo_root / TARGET_TEMPLATE_DIR,
        check=check,
        out_of_sync=out_of_sync,
        summary=summary,
    )

    if check:
        if out_of_sync:
            for relative in sorted(set(out_of_sync)):
                print(f"consumer-init SDD asset drift: {relative}", file=sys.stderr)
            print(
                "Run: python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py",
                file=sys.stderr,
            )
            return 1
        return 0

    summary.emit(dry_run=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    return _sync(repo_root=repo_root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
