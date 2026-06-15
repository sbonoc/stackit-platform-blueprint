"""Compositional-independence assertions (issue #364, FR-001 / AC-012).

FR-001: each PERSONA.md MUST NOT reference another expert's slug in its body
prose (forbidden example: "defer to `security-paranoid` for threat modelling").
The orchestrator dispatch table is the sole binding mechanism between experts.

The H1 title line and any markdown frontmatter MUST be excluded from the
search range (those are permitted to contain a slug-like word).
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    persona_path,
)


def _body_excluding_title_and_frontmatter(slug: str) -> str:
    raw = persona_path(slug).read_text()
    lines = raw.splitlines()

    # Strip YAML frontmatter if present (--- ... ---).
    if lines and lines[0].strip() == "---":
        try:
            close_idx = next(
                i for i, ln in enumerate(lines[1:], start=1) if ln.strip() == "---"
            )
            lines = lines[close_idx + 1 :]
        except StopIteration:
            pass

    # Strip leading blank lines, then the first H1 line.
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]

    return "\n".join(lines)


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
def test_persona_body_does_not_reference_other_expert_slugs(slug: str) -> None:
    body = _body_excluding_title_and_frontmatter(slug)
    other_slugs = [s for s in EXPERT_SLUGS if s != slug]
    offenders: list[str] = []
    for other in other_slugs:
        pattern = re.compile(r"\b" + re.escape(other) + r"\b", re.IGNORECASE)
        if pattern.search(body):
            offenders.append(other)
    assert not offenders, (
        f"{slug}/PERSONA.md body prose references other expert slug(s) "
        f"{offenders!r} — FR-001 compositional independence forbids cross-slug "
        f"citation; the orchestrator dispatch table is the sole binding mechanism."
    )
