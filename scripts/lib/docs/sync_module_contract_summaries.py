#!/usr/bin/env python3
"""Sync generated module contract summaries with repo-mode-aware template behavior."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import (  # noqa: E402
    ChangeSummary,
    display_repo_path,
    resolve_repo_root,
)
from scripts.lib.blueprint.contract_schema import load_module_contract  # noqa: E402
from scripts.lib.docs.repo_mode import resolve_docs_repo_context  # noqa: E402


BEGIN_MARKER = "<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->"
END_MARKER = "<!-- END GENERATED MODULE CONTRACT SUMMARY -->"


def _replace_marked_block(content: str, replacement_block: str, path: Path) -> str:
    start = content.find(BEGIN_MARKER)
    end = content.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"missing generated module summary markers in {path}")
    end += len(END_MARKER)
    return content[:start] + replacement_block + content[end:]


def _render_summary(module_id: str, purpose: str, enable_flag: str, required_env: list[str], make_targets: list[str], outputs: list[str]) -> str:
    lines: list[str] = []
    lines.append(BEGIN_MARKER)
    lines.append("## Contract Summary")
    lines.append(f"- Purpose: {purpose}")
    lines.append(f"- Enable flag: `{enable_flag}` (default: `false`)")
    lines.append("- Required inputs:")
    for item in required_env:
        lines.append(f"  - `{item}`")
    lines.append("- Make targets:")
    for item in make_targets:
        lines.append(f"  - `{item}`")
    lines.append("- Outputs:")
    for item in outputs:
        lines.append(f"  - `{item}`")
    lines.append(END_MARKER)
    return "\n".join(lines)


def _apply(path: Path, updated: str, dry_run: bool, summary: ChangeSummary) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else None
    if original == updated:
        summary.skipped_path(path, "already synchronized")
        return
    if dry_run:
        if original is None:
            summary.created_path(path)
        else:
            summary.updated_path(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    if original is None:
        summary.created_path(path)
    else:
        summary.updated_path(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve module docs and template paths.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when source/template module docs are out of sync with module contracts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    summary = ChangeSummary("quality-docs-sync-module-contract-summaries")
    repo_context = resolve_docs_repo_context(repo_root)
    template_sync_enabled = repo_context.template_sync_enabled
    modules_dir = repo_root / "blueprint/modules"
    module_contracts = sorted(modules_dir.glob("*/module.contract.yaml"))
    if not module_contracts:
        raise ValueError(f"no module contracts found under {modules_dir}")

    out_of_date: list[str] = []
    for module_contract_path in module_contracts:
        module_contract = load_module_contract(module_contract_path, repo_root)
        source_doc = repo_root / f"docs/platform/modules/{module_contract.module_id}/README.md"
        template_doc = (
            repo_root / f"scripts/templates/blueprint/bootstrap/docs/platform/modules/{module_contract.module_id}/README.md"
        )
        rendered_block = _render_summary(
            module_id=module_contract.module_id,
            purpose=module_contract.purpose,
            enable_flag=module_contract.enable_flag,
            required_env=module_contract.required_env,
            make_targets=list(module_contract.make_targets.values()),
            outputs=module_contract.outputs,
        )
        rendered_source = _replace_marked_block(source_doc.read_text(encoding="utf-8"), rendered_block, source_doc)

        if args.check:
            if source_doc.read_text(encoding="utf-8") != rendered_source:
                out_of_date.append(display_repo_path(repo_root, source_doc))
            if template_sync_enabled and template_doc.read_text(encoding="utf-8") != rendered_source:
                out_of_date.append(display_repo_path(repo_root, template_doc))
            continue

        _apply(source_doc, rendered_source, dry_run=False, summary=summary)
        if template_sync_enabled:
            _apply(template_doc, rendered_source, dry_run=False, summary=summary)

    if args.check:
        if out_of_date:
            for path in out_of_date:
                print(f"module contract summary doc out of date: {path}", file=sys.stderr)
            print(
                "Run: python3 scripts/lib/docs/sync_module_contract_summaries.py",
                file=sys.stderr,
            )
            return 1
        return 0

    summary.emit(dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
