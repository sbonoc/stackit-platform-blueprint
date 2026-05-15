#!/usr/bin/env python3
"""Verify AGENTS.md contains required structural elements for the north_star.md contract."""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]

_MANDATORY_WORKFLOW_RE = re.compile(r'^## Mandatory Workflow\s*$', re.MULTILINE)


def _check_structure(content: str) -> list[str]:
    violations: list[str] = []

    if '## Architecture Invariants — Pointers' not in content:
        violations.append('missing required section: ## Architecture Invariants — Pointers')

    mw_match = _MANDATORY_WORKFLOW_RE.search(content)
    if mw_match:
        after = content[mw_match.end():]
        next_section = re.search(r'^##\s', after, re.MULTILINE)
        mw_body = after[: next_section.start()] if next_section else after
        if 'north_star.md' not in mw_body:
            violations.append(
                'missing north_star.md reference within ## Mandatory Workflow section'
            )
    else:
        violations.append('missing required section: ## Mandatory Workflow')

    return violations


def main() -> int:
    agents_md = REPO_ROOT / 'AGENTS.md'
    if not agents_md.exists():
        return 0

    content = agents_md.read_text(encoding='utf-8')
    violations = _check_structure(content)

    if not violations:
        print(
            '[quality-docs-agents-md-structure-check] AGENTS.md structural contract satisfied',
        )
        return 0

    for v in violations:
        print(f'[quality-docs-agents-md-structure-check] {v}', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
