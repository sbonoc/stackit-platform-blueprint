#!/usr/bin/env python3
"""Enforce canonical shell prelude root-resolution contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]

INLINE_ROOT_RESOLVER_RE = re.compile(r'^ROOT_DIR="\$\(cd "\$SCRIPT_DIR/', re.MULTILINE)
ROOT_BOOTSTRAP_SOURCE_RE = re.compile(r'^source "\$ROOT_DIR/scripts/lib/(?:shell/)?bootstrap\.sh"$', re.MULTILINE)
SCRIPT_DIR_BOOTSTRAP_SOURCE_RE = re.compile(
    r'^source "\$SCRIPT_DIR/(?:\.\./)+(?:lib/bootstrap\.sh|lib/shell/bootstrap\.sh)"$',
    re.MULTILINE,
)

SCRIPT_GLOBS = (
    "scripts/bin/blueprint/**/*.sh",
    "scripts/bin/infra/**/*.sh",
    "scripts/bin/docs/**/*.sh",
    "scripts/bin/quality/**/*.sh",
)
TEMPLATE_GLOBS = ("scripts/templates/infra/module_wrappers/**/*.sh.tmpl",)


@dataclass(frozen=True)
class Violation:
    path: str
    message: str


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _validate_prelude(path: Path) -> list[Violation]:
    content = path.read_text(encoding="utf-8")
    violations: list[Violation] = []

    if INLINE_ROOT_RESOLVER_RE.search(content):
        violations.append(Violation(_repo_relative(path), "inline ROOT_DIR resolver detected"))

    if ROOT_BOOTSTRAP_SOURCE_RE.search(content):
        violations.append(
            Violation(
                _repo_relative(path),
                "bootstrap sourced via $ROOT_DIR; use SCRIPT_DIR-relative source path",
            )
        )

    if not SCRIPT_DIR_BOOTSTRAP_SOURCE_RE.search(content):
        violations.append(
            Violation(
                _repo_relative(path),
                "missing canonical bootstrap source prelude using $SCRIPT_DIR relative path",
            )
        )

    return violations


def _iter_paths(globs: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for pattern in globs:
        paths.extend(sorted(REPO_ROOT.glob(pattern)))
    return paths


def main() -> int:
    violations: list[Violation] = []

    for path in _iter_paths(SCRIPT_GLOBS):
        violations.extend(_validate_prelude(path))

    for path in _iter_paths(TEMPLATE_GLOBS):
        violations.extend(_validate_prelude(path))

    if not violations:
        print(
            "[quality-root-dir-prelude-check] all managed shell entrypoints use canonical root-resolution prelude",
            file=sys.stdout,
        )
        return 0

    for violation in violations:
        print(f"[quality-root-dir-prelude-check] {violation.path}: {violation.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
