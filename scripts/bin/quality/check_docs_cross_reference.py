#!/usr/bin/env python3
"""Detect heading duplication between AGENTS.md and north_star.md."""

from __future__ import annotations

from pathlib import Path
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[3]

_HEADING_RE = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
_TABLE_ROW_RE = re.compile(r'^\|(.+)\|$')


def _normalize_heading(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip().lower())


def _extract_headings(content: str) -> set[str]:
    return {_normalize_heading(m.group(1)) for m in _HEADING_RE.finditer(content)}


def _extract_pointer_headings(content: str) -> set[str]:
    section_re = re.compile(r'^## Architecture Invariants — Pointers\s*$', re.MULTILINE)
    match = section_re.search(content)
    if not match:
        return set()

    after = content[match.end():]
    next_section = re.search(r'^##\s', after, re.MULTILINE)
    if next_section:
        after = after[: next_section.start()]

    result: set[str] = set()
    header_seen = False
    for line in after.splitlines():
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        cells = [c.strip() for c in stripped.split('|')[1:-1]]
        if not cells:
            continue
        if not header_seen:
            header_seen = True
            continue
        if re.match(r'^[-:\s|]+$', stripped):
            continue
        domain = re.sub(r'<!--.*?-->', '', cells[0]).strip()
        if domain:
            result.add(_normalize_heading(domain))
    return result


def _load_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    content = path.read_text(encoding='utf-8')
    if yaml is None:
        print(
            '[quality-docs-cross-reference-check] WARNING: PyYAML not available; allowlist skipped',
            file=sys.stderr,
        )
        return set()
    data = yaml.safe_load(content) or {}
    entries = data.get('entries', [])
    result: set[str] = set()
    for entry in entries:
        heading = entry.get('heading', '')
        justification = entry.get('justification', '').strip()
        if not justification:
            print(
                f'[quality-docs-cross-reference-check] allowlist entry missing justification: {heading!r}',
                file=sys.stderr,
            )
            continue
        if heading:
            result.add(_normalize_heading(heading))
    return result


def _resolve_north_star(repo_root: Path) -> Path | None:
    consumer = repo_root / 'docs' / 'platform' / 'architecture' / 'north_star.md'
    if consumer.exists():
        return consumer
    blueprint = repo_root / 'docs' / 'blueprint' / 'architecture' / 'north_star.md'
    if blueprint.exists():
        return blueprint
    return None


def main() -> int:
    agents_md = REPO_ROOT / 'AGENTS.md'
    if not agents_md.exists():
        return 0

    north_star = _resolve_north_star(REPO_ROOT)
    if north_star is None:
        return 0

    agents_content = agents_md.read_text(encoding='utf-8')
    north_star_content = north_star.read_text(encoding='utf-8')
    allowlist_path = REPO_ROOT / '.quality-docs-cross-reference-allowlist.yml'

    agents_headings = _extract_headings(agents_content)
    north_star_headings = _extract_headings(north_star_content)
    pointer_headings = _extract_pointer_headings(agents_content)
    allowlist = _load_allowlist(allowlist_path)

    exempted = pointer_headings | allowlist
    violations = sorted(agents_headings & north_star_headings - exempted)

    if not violations:
        print(
            '[quality-docs-cross-reference-check] no heading duplication detected between AGENTS.md and north_star.md',
        )
        return 0

    for heading in violations:
        print(
            f'[quality-docs-cross-reference-check] AGENTS.md heading duplicates north_star.md: {heading!r}',
            file=sys.stderr,
        )
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
