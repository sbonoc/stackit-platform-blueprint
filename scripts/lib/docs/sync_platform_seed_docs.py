#!/usr/bin/env python3
"""Sync/check docs/platform seed docs mirrored into bootstrap template docs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, display_repo_path, resolve_repo_root  # noqa: E402


SOURCE_ROOT = Path("docs/platform")
TEMPLATE_ROOT = Path("scripts/templates/blueprint/bootstrap/docs/platform")


def _list_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _sync(repo_root: Path, check: bool) -> int:
    source_root = repo_root / SOURCE_ROOT
    template_root = repo_root / TEMPLATE_ROOT

    if not source_root.is_dir():
        raise ValueError(f"missing source platform docs root: {source_root}")

    source_files = _list_files(source_root)
    template_files = _list_files(template_root)
    summary = ChangeSummary("quality-docs-sync-platform-seed")
    out_of_sync: list[str] = []

    for relative, source_path in source_files.items():
        target_path = template_root / relative
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

    extra_template = sorted(set(template_files) - set(source_files))
    for relative in extra_template:
        target_path = template_root / relative
        if check:
            out_of_sync.append(display_repo_path(repo_root, target_path))
            continue
        target_path.unlink()
        summary.removed_path(target_path)

    if check:
        if out_of_sync:
            for relative in sorted(set(out_of_sync)):
                print(f"platform docs template drift: {relative}", file=sys.stderr)
            print(
                "Run: python3 scripts/lib/docs/sync_platform_seed_docs.py",
                file=sys.stderr,
            )
            return 1
        return 0

    summary.emit(dry_run=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve docs paths.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when docs/platform/** and the template seed docs drift.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    return _sync(repo_root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
