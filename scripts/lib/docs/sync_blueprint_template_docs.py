#!/usr/bin/env python3
"""Sync/check blueprint docs mirrored into bootstrap template docs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


SINGLE_FILE_MIRRORS: tuple[tuple[Path, Path], ...] = (
    (Path("docs/README.md"), Path("scripts/templates/blueprint/bootstrap/docs/README.md")),
)
BLUEPRINT_DOCS_ROOT = Path("docs/blueprint")
DIRECTORY_MIRRORS: tuple[tuple[Path, Path], ...] = (
    (BLUEPRINT_DOCS_ROOT, Path("scripts/templates/blueprint/bootstrap/docs/blueprint")),
)


def resolve_blueprint_docs_template_allowlist(repo_root: Path) -> tuple[str, ...]:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    allowlist = tuple(contract.docs_contract.blueprint_docs.template_sync_allowlist)
    if not allowlist:
        raise ValueError(
            "missing spec.docs_contract.blueprint_docs.template_sync_allowlist "
            "in blueprint/contract.yaml"
        )
    return allowlist


def _list_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _sync_single_file(
    *,
    repo_root: Path,
    source_path: Path,
    target_path: Path,
    check: bool,
    summary: ChangeSummary,
    out_of_sync: list[str],
) -> None:
    if not source_path.is_file():
        raise ValueError(f"missing source blueprint docs file: {source_path}")
    source_content = source_path.read_text(encoding="utf-8")
    if target_path.is_file():
        target_content = target_path.read_text(encoding="utf-8")
        if target_content == source_content:
            summary.skipped_path(target_path, "already synchronized")
            return
        if check:
            out_of_sync.append(display_repo_path(repo_root, target_path))
            return
        target_path.write_text(source_content, encoding="utf-8")
        summary.updated_path(target_path)
        return
    if check:
        out_of_sync.append(display_repo_path(repo_root, target_path))
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(source_content, encoding="utf-8")
    summary.created_path(target_path)


def _sync_directory(
    *,
    repo_root: Path,
    source_root: Path,
    template_root: Path,
    allowlist: tuple[str, ...] | None,
    check: bool,
    summary: ChangeSummary,
    out_of_sync: list[str],
) -> None:
    if not source_root.is_dir():
        raise ValueError(f"missing source blueprint docs root: {source_root}")

    source_files = _list_files(source_root)
    if allowlist is not None:
        allowed = set(allowlist)
        source_files = {relative: path for relative, path in source_files.items() if relative in allowed}
        missing = sorted(allowed - set(source_files))
        if missing:
            missing_joined = ", ".join(missing)
            raise ValueError(f"missing required blueprint docs source files for template sync: {missing_joined}")
    template_files = _list_files(template_root)

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


def _sync(repo_root: Path, check: bool) -> int:
    summary = ChangeSummary("quality-docs-sync-blueprint-template")
    out_of_sync: list[str] = []
    blueprint_docs_allowlist = resolve_blueprint_docs_template_allowlist(repo_root)

    for source_rel, target_rel in SINGLE_FILE_MIRRORS:
        _sync_single_file(
            repo_root=repo_root,
            source_path=repo_root / source_rel,
            target_path=repo_root / target_rel,
            check=check,
            summary=summary,
            out_of_sync=out_of_sync,
        )

    for source_rel, target_rel in DIRECTORY_MIRRORS:
        _sync_directory(
            repo_root=repo_root,
            source_root=repo_root / source_rel,
            template_root=repo_root / target_rel,
            allowlist=blueprint_docs_allowlist if source_rel == BLUEPRINT_DOCS_ROOT else None,
            check=check,
            summary=summary,
            out_of_sync=out_of_sync,
        )

    if check:
        if out_of_sync:
            for relative in sorted(set(out_of_sync)):
                print(f"blueprint docs template drift: {relative}", file=sys.stderr)
            print(
                "Run: python3 scripts/lib/docs/sync_blueprint_template_docs.py",
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
        help="Exit non-zero when blueprint docs and template docs are out of sync.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    return _sync(repo_root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
