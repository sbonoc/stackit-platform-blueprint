#!/usr/bin/env python3
"""Sync/check platform docs ownership boundaries across repo modes."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.docs.repo_mode import (  # noqa: E402
    REPO_MODE_GENERATED_CONSUMER,
    REPO_MODE_TEMPLATE_SOURCE,
    resolve_docs_repo_context,
)


def _resolve_platform_docs_contract(repo_root: Path) -> tuple[str, Path, Path, tuple[str, ...]]:
    context = resolve_docs_repo_context(repo_root)
    platform_docs = context.contract.docs_contract.platform_docs
    source_root = Path(platform_docs.root)
    template_root = Path(platform_docs.template_root)
    if not source_root.as_posix().strip():
        raise ValueError("docs_contract.platform_docs.root must be set")
    if not template_root.as_posix().strip():
        raise ValueError("docs_contract.platform_docs.template_root must be set")

    required_seed_files = tuple(platform_docs.required_seed_files)
    if not required_seed_files:
        raise ValueError("docs_contract.platform_docs.required_seed_files must define at least one file")

    required_relative: list[str] = []
    source_prefix = f"{source_root.as_posix().rstrip('/')}/"
    for absolute_path in required_seed_files:
        normalized = absolute_path.strip()
        if not normalized.startswith(source_prefix):
            raise ValueError(
                "docs_contract.platform_docs.required_seed_files entry must be under configured root "
                f"{source_root.as_posix()}: {normalized}"
            )
        relative = normalized.removeprefix(source_prefix).strip("/")
        if not relative:
            raise ValueError(
                "docs_contract.platform_docs.required_seed_files entry must resolve to a file under "
                f"{source_root.as_posix()}: {normalized}"
            )
        required_relative.append(relative)

    return (
        context.repo_mode,
        source_root,
        template_root,
        tuple(sorted(set(required_relative))),
    )


def _list_files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _sync_template_source(
    *,
    repo_root: Path,
    source_root: Path,
    template_root: Path,
    required_relative_files: tuple[str, ...],
    check: bool,
) -> int:
    if not source_root.is_dir():
        raise ValueError(f"missing source platform docs root: {source_root}")
    if not template_root.is_dir():
        raise ValueError(f"missing template platform docs root: {template_root}")

    required_set = set(required_relative_files)
    template_files = _list_files(template_root)
    summary = ChangeSummary("quality-docs-sync-platform-seed")
    out_of_sync: list[str] = []

    for relative in required_relative_files:
        source_path = source_root / relative
        if not source_path.is_file():
            raise ValueError(
                "missing required platform docs source file for template sync: "
                f"{display_repo_path(repo_root, source_path)}"
            )
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

    extra_template = sorted(set(template_files) - required_set)
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


def _sync_generated_consumer(
    *,
    repo_root: Path,
    source_root: Path,
    template_root: Path,
    required_relative_files: tuple[str, ...],
    check: bool,
) -> int:
    if not source_root.is_dir():
        raise ValueError(f"missing source platform docs root: {source_root}")
    if not template_root.is_dir():
        raise ValueError(f"missing template platform docs root: {template_root}")

    summary = ChangeSummary("quality-docs-clean-generated-consumer-platform-template")
    template_files = _list_files(template_root)
    required_set = set(required_relative_files)
    orphan_relatives = sorted(set(template_files) - required_set)

    if check:
        if orphan_relatives:
            for relative in orphan_relatives:
                template_path = template_root / relative
                source_path = source_root / relative
                if source_path.is_file():
                    print(
                        "generated-consumer template orphan (remove template copy): "
                        f"{display_repo_path(repo_root, template_path)}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "generated-consumer template orphan (move to source and remove template): "
                        f"{display_repo_path(repo_root, template_path)} -> "
                        f"{display_repo_path(repo_root, source_path)}",
                        file=sys.stderr,
                    )
            print(
                "Run: python3 scripts/lib/docs/sync_platform_seed_docs.py",
                file=sys.stderr,
            )
            return 1
        return 0

    for relative in orphan_relatives:
        template_path = template_root / relative
        source_path = source_root / relative
        if source_path.is_file():
            template_path.unlink()
            summary.removed_path(template_path)
            continue

        source_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.replace(source_path)
        summary.created_path(source_path)
        summary.removed_path(template_path)

    summary.emit(dry_run=False)
    return 0


def _sync(repo_root: Path, check: bool) -> int:
    repo_mode, source_root_rel, template_root_rel, required_relative_files = _resolve_platform_docs_contract(repo_root)
    source_root = repo_root / source_root_rel
    template_root = repo_root / template_root_rel

    if repo_mode == REPO_MODE_TEMPLATE_SOURCE:
        return _sync_template_source(
            repo_root=repo_root,
            source_root=source_root,
            template_root=template_root,
            required_relative_files=required_relative_files,
            check=check,
        )

    if repo_mode == REPO_MODE_GENERATED_CONSUMER:
        return _sync_generated_consumer(
            repo_root=repo_root,
            source_root=source_root,
            template_root=template_root,
            required_relative_files=required_relative_files,
            check=check,
        )

    raise ValueError(f"unsupported repository repo_mode for platform docs sync: {repo_mode}")


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
