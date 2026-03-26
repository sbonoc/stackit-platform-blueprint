#!/usr/bin/env python3
"""Initialize repository identity after GitHub template instantiation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


def _replace_scalar_once(content: str, pattern: str, replacement: str, label: str) -> str:
    compiled = re.compile(pattern, flags=re.MULTILINE)
    updated, count = compiled.subn(replacement, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _replace_js_string_key(content: str, key: str, value: str, label: str) -> str:
    pattern = re.compile(rf'^(\s*{re.escape(key)}:\s*")[^"]*(".*)$', flags=re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{value}{match.group(2)}'

    updated, count = pattern.subn(repl, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _render_contract(
    content: str,
    repo_name: str,
    default_branch: str,
) -> str:
    content = _replace_scalar_once(
        content,
        r"^(\s*name:\s*).+$",
        rf"\1{repo_name}",
        "blueprint contract metadata.name",
    )
    content = _replace_scalar_once(
        content,
        r"^(\s*default_branch:\s*).+$",
        rf"\1{default_branch}",
        "blueprint contract repository.default_branch",
    )
    return content


def _render_docusaurus_config(
    content: str,
    docs_title: str,
    docs_tagline: str,
    github_org: str,
    github_repo: str,
    default_branch: str,
) -> str:
    edit_url = f"https://github.com/{github_org}/{github_repo}/edit/{default_branch}/docs/"

    content = _replace_js_string_key(content, "title", docs_title, "docs title")
    content = _replace_js_string_key(content, "tagline", docs_tagline, "docs tagline")
    content = _replace_js_string_key(content, "organizationName", github_org, "docs organizationName")
    content = _replace_js_string_key(content, "projectName", github_repo, "docs projectName")
    content = _replace_js_string_key(content, "editUrl", edit_url, "docs editUrl")
    return content


def _apply_file_update(path: Path, original: str, updated: str, dry_run: bool) -> bool:
    changed = updated != original
    if not changed:
        print(f"no change required: {path}")
        return False

    if dry_run:
        print(f"[dry-run] would update: {path}")
        return True

    path.write_text(updated, encoding="utf-8")
    print(f"updated: {path}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Absolute repository root path.")
    parser.add_argument("--repo-name", required=True, help="Repository slug for contract metadata.")
    parser.add_argument("--github-org", required=True, help="GitHub org/user for edit links.")
    parser.add_argument("--github-repo", required=True, help="GitHub repo for edit links.")
    parser.add_argument("--default-branch", required=True, help="Default branch name.")
    parser.add_argument("--docs-title", required=True, help="Docusaurus site title.")
    parser.add_argument("--docs-tagline", required=True, help="Docusaurus site tagline.")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    contract_path = repo_root / "blueprint/contract.yaml"
    docusaurus_path = repo_root / "docs/docusaurus.config.js"

    contract_original = contract_path.read_text(encoding="utf-8")
    contract_updated = _render_contract(
        content=contract_original,
        repo_name=args.repo_name,
        default_branch=args.default_branch,
    )
    docusaurus_original = docusaurus_path.read_text(encoding="utf-8")
    docusaurus_updated = _render_docusaurus_config(
        content=docusaurus_original,
        docs_title=args.docs_title,
        docs_tagline=args.docs_tagline,
        github_org=args.github_org,
        github_repo=args.github_repo,
        default_branch=args.default_branch,
    )
    changed_count = 0
    changed_count += int(
        _apply_file_update(contract_path, contract_original, contract_updated, args.dry_run)
    )
    changed_count += int(
        _apply_file_update(docusaurus_path, docusaurus_original, docusaurus_updated, args.dry_run)
    )

    if args.dry_run:
        print(f"[dry-run] summary: {changed_count} file(s) would be updated")
    else:
        print(f"summary: updated {changed_count} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
