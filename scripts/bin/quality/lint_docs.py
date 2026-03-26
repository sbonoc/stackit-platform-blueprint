#!/usr/bin/env python3
"""Lint Markdown docs for local links, Make targets, and governance links."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_module_contract  # noqa: E402

DEFAULT_DOC_GLOBS = (
    "README.md",
    "AGENTS.md",
    "AGENTS.backlog.md",
    "AGENTS.decisions.md",
    "docs/**/*.md",
)
# Only lint repository-owned Markdown. Built docs and vendored package READMEs
# are useful locally, but they are not part of the blueprint contract surface.
EXCLUDED_DOC_PREFIXES = (
    Path("docs/node_modules"),
    Path("docs/.docusaurus"),
    Path("docs/build"),
)
MAKE_REFERENCE_PATTERN = re.compile(r"(?<![\w./-])make\s+([A-Za-z0-9][A-Za-z0-9._-]*)")
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
FENCED_CODE_PATTERN = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
VALID_GOVERNANCE_LINK_BASENAMES = {"AGENTS.md", "AGENTS.backlog.md", "AGENTS.decisions.md"}


@dataclass(frozen=True, slots=True)
class LintIssue:
    file_path: Path
    line: int
    message: str


def iter_markdown_files(repo_root: Path, patterns: tuple[str, ...]) -> list[Path]:
    files: set[Path] = set()
    for pattern in patterns:
        for path in repo_root.glob(pattern):
            if path.is_file():
                relative = path.relative_to(repo_root)
                if any(relative.is_relative_to(prefix) for prefix in EXCLUDED_DOC_PREFIXES):
                    continue
                files.add(path)
    return sorted(files)


def load_make_targets(repo_root: Path) -> set[str]:
    targets: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    for makefile in [repo_root / "Makefile", *(repo_root / "make").rglob("*.mk")]:
        if not makefile.is_file():
            continue
        for line in makefile.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match is None:
                continue
            target = match.group(1)
            if target != ".PHONY":
                targets.add(target)
    modules_dir = repo_root / "blueprint" / "modules"
    if modules_dir.is_dir():
        # Module contracts declare conditional targets that may be intentionally
        # absent from the currently materialized Make surface.
        for module_contract in modules_dir.glob("*/module.contract.yaml"):
            contract = load_module_contract(module_contract, repo_root)
            targets.update(contract.make_targets.values())
    return targets


def iter_fenced_code_blocks(content: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    for match in FENCED_CODE_PATTERN.finditer(content):
        start_line = content.count("\n", 0, match.start()) + 1
        blocks.append((start_line, match.group(1)))
    return blocks


def _resolve_link_target(repo_root: Path, doc_path: Path, raw_target: str) -> Path | None:
    if raw_target.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    target = raw_target.split("#", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        return (repo_root / target.lstrip("/")).resolve()
    return (doc_path.parent / target).resolve()


def lint_markdown_file(repo_root: Path, file_path: Path, make_targets: set[str]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    for line_no, line in enumerate(lines, start=1):
        for match in MARKDOWN_LINK_PATTERN.finditer(line):
            raw_target = match.group(1).strip()
            if not raw_target:
                continue
            resolved = _resolve_link_target(repo_root, file_path, raw_target)
            if resolved is not None and not resolved.exists():
                issues.append(LintIssue(file_path, line_no, f"broken local markdown link: {raw_target}"))

            basename = Path(raw_target.split("#", 1)[0]).name
            if basename.startswith("AGENTS") and basename not in VALID_GOVERNANCE_LINK_BASENAMES:
                issues.append(
                    LintIssue(file_path, line_no, f"non-canonical governance file reference: {raw_target}")
                )

        for code_match in INLINE_CODE_PATTERN.finditer(line):
            snippet = code_match.group(1).strip()
            make_match = MAKE_REFERENCE_PATTERN.search(snippet)
            if make_match is None:
                continue
            target = make_match.group(1)
            if target not in make_targets:
                issues.append(LintIssue(file_path, line_no, f"unknown make target reference: {target}"))

    for block_start_line, block_content in iter_fenced_code_blocks(content):
        for line_offset, block_line in enumerate(block_content.splitlines()):
            make_match = MAKE_REFERENCE_PATTERN.search(block_line.strip())
            if make_match is None:
                continue
            target = make_match.group(1)
            if target not in make_targets:
                issues.append(
                    LintIssue(file_path, block_start_line + line_offset, f"unknown make target reference: {target}")
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint repository markdown docs.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root containing Makefiles and markdown files.",
    )
    parser.add_argument(
        "--doc-glob",
        action="append",
        default=list(DEFAULT_DOC_GLOBS),
        help="Markdown glob to lint relative to repo root.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    doc_globs = tuple(args.doc_glob)
    make_targets = load_make_targets(repo_root)
    markdown_files = iter_markdown_files(repo_root, doc_globs)

    issues: list[LintIssue] = []
    for file_path in markdown_files:
        issues.extend(lint_markdown_file(repo_root, file_path, make_targets))

    if issues:
        for issue in issues:
            relative = issue.file_path.relative_to(repo_root)
            print(f"{relative}:{issue.line}: {issue.message}", file=sys.stderr)
        return 1

    print(f"docs lint passed for {len(markdown_files)} markdown files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
