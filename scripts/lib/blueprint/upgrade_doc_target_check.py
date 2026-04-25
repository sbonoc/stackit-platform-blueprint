"""Stage 7: Make target validation for new/changed markdown files.

Scans modified markdown files for fenced code blocks containing `make <target>`
references. Verifies each target appears in a .PHONY declaration across all .mk
files. Emits structured warnings for missing targets.

This stage NEVER aborts the pipeline — it emits warnings only (FR-012).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Match lines of the form: make <target>
# Anchored at start-of-line optionally with whitespace (e.g. inside shell blocks).
_MAKE_TARGET_RE = re.compile(r"^\s*make\s+([A-Za-z0-9_\-]+)\s*$", re.MULTILINE)

# Match .PHONY declarations in makefiles.
_PHONY_RE = re.compile(r"^\.PHONY\s*:\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class DocTargetCheckResult:
    missing_targets: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    exit_code: int = 0  # always 0 — stage never aborts

    def as_dict(self) -> dict:
        return {
            "missing_targets": self.missing_targets,
            "warnings": self.warnings,
            "exit_code": self.exit_code,
        }


def _collect_phony_targets(repo_root: Path) -> set[str]:
    """Return all targets declared in .PHONY lines across all .mk files."""
    targets: set[str] = set()
    for mk_file in repo_root.rglob("*.mk"):
        text = mk_file.read_text(encoding="utf-8", errors="replace")
        for match in _PHONY_RE.finditer(text):
            for target in match.group(1).split():
                targets.add(target.strip())
    return targets


def _extract_make_targets_from_fenced_bash(md_text: str) -> list[str]:
    """Extract make target names from fenced bash/shell code blocks in markdown."""
    targets: list[str] = []
    # Match fenced blocks: ```bash, ```shell, ```sh, or untagged ```.
    # We only scan bash/shell/sh/untagged blocks, not python/other language blocks.
    fence_re = re.compile(
        r"```(?:bash|shell|sh)?\s*\n(.*?)```",
        re.DOTALL,
    )
    for fence_match in fence_re.finditer(md_text):
        block = fence_match.group(1)
        # Only process blocks that look like shell (no obvious language keywords)
        for target_match in _MAKE_TARGET_RE.finditer(block):
            targets.append(target_match.group(1))
    return targets


def check_doc_make_targets(
    repo_root: Path,
    modified_md_paths: list[str],
) -> DocTargetCheckResult:
    """Scan modified markdown files for make target references; warn on missing ones.

    Never raises or returns a non-zero exit_code — warnings only (FR-012).
    """
    if not modified_md_paths:
        return DocTargetCheckResult()

    phony_targets = _collect_phony_targets(repo_root)
    missing: list[str] = []
    warnings: list[str] = []

    for rel_path in modified_md_paths:
        md_file = repo_root / rel_path
        if not md_file.exists():
            continue
        text = md_file.read_text(encoding="utf-8", errors="replace")
        referenced = _extract_make_targets_from_fenced_bash(text)
        for target in referenced:
            if target not in phony_targets and target not in missing:
                missing.append(target)
                warnings.append(
                    f"[WARN] {rel_path}: make target '{target}' not found in any .PHONY declaration"
                )

    return DocTargetCheckResult(
        missing_targets=missing,
        warnings=warnings,
        exit_code=0,
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Stage 7: validate make targets referenced in modified markdown files.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--modified-md-paths-json",
        type=Path,
        default=None,
        help="JSON file containing a list of repo-relative modified .md paths.",
    )
    args = parser.parse_args()

    if args.modified_md_paths_json and args.modified_md_paths_json.exists():
        modified_md_paths = json.loads(
            args.modified_md_paths_json.read_text(encoding="utf-8")
        )
    else:
        modified_md_paths = []

    result = check_doc_make_targets(args.repo_root, modified_md_paths)
    for warning in result.warnings:
        print(warning, file=sys.stderr)
    if result.missing_targets:
        print(
            f"[PIPELINE] Stage 7: {len(result.missing_targets)} missing make target(s) — "
            "see warnings above. Pipeline continues.",
            file=sys.stderr,
        )
    else:
        print("[PIPELINE] Stage 7: all make target references validated.")
    # Always exit 0 (FR-012)
    return 0


if __name__ == "__main__":
    sys.exit(main())
