"""T-108 — persona template skeleton structure (AC-014, FR-017).

Each of the 10 persona files MUST contain the 9 common section headings in
EXACTLY this order, and each required section MUST have at least one
non-blank line of content between its heading and the next heading.

The 4 reviewer persona files MUST additionally contain `## Review Dimensions`.
`architecture-reviewer.md` MUST additionally contain
`## Cross-Context Impact Reporting`.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import (
    IMPLEMENTER_PERSONA_NAMES,
    PERSONA_NAMES,
    REVIEWER_PERSONA_NAMES,
    persona_path,
)

# FR-017: exact order, 9 common section headings.
REQUIRED_SECTIONS_IN_ORDER: tuple[str, ...] = (
    "# Persona:",
    "## Role Objective",
    "## Required Inputs",
    "## SDD Cycle Stakes",
    "## Skills Invoked",
    "## Activation Triggers",
    "## Collaboration & Handoffs",
    "## Strict Guardrails",
    "## Definition of Done (DoD)",
)

REVIEWER_EXTRA_SECTION = "## Review Dimensions"
ARCHITECTURE_REVIEWER_EXTRA_SECTION = "## Cross-Context Impact Reporting"

# Strip YAML front-matter for body parsing.
FRONT_MATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def _strip_front_matter(text: str) -> str:
    return FRONT_MATTER_RE.sub("", text, count=1)


def _heading_indices(body: str, heading: str) -> list[int]:
    indices: list[int] = []
    for i, line in enumerate(body.splitlines()):
        stripped = line.rstrip()
        # Match exact-prefix headings (allow trailing content on `# Persona:` H1).
        if heading == "# Persona:":
            if stripped.startswith("# Persona:"):
                indices.append(i)
        elif stripped == heading or stripped.startswith(heading + " "):
            indices.append(i)
    return indices


def _section_content(body: str, start_heading: str, next_heading: str | None) -> str:
    lines = body.splitlines()
    start_indices = _heading_indices(body, start_heading)
    assert start_indices, f"missing heading: {start_heading!r}"
    start = start_indices[0] + 1
    if next_heading is None:
        end = len(lines)
    else:
        next_indices = [i for i in _heading_indices(body, next_heading) if i > start]
        end = next_indices[0] if next_indices else len(lines)
    return "\n".join(lines[start:end])


@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_has_all_required_headings(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    for heading in REQUIRED_SECTIONS_IN_ORDER:
        assert _heading_indices(body, heading), (
            f"{name}: missing required heading {heading!r}"
        )


@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_headings_appear_in_required_order(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    line_positions: list[tuple[int, str]] = []
    for heading in REQUIRED_SECTIONS_IN_ORDER:
        indices = _heading_indices(body, heading)
        assert indices, f"{name}: missing heading {heading!r}"
        line_positions.append((indices[0], heading))
    actual_order = [h for _, h in sorted(line_positions, key=lambda p: p[0])]
    assert actual_order == list(REQUIRED_SECTIONS_IN_ORDER), (
        f"{name}: required headings appear out of order: got {actual_order}"
    )


@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_each_required_section_has_non_empty_content(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    headings = list(REQUIRED_SECTIONS_IN_ORDER)
    for i, heading in enumerate(headings):
        next_heading = headings[i + 1] if i + 1 < len(headings) else None
        content = _section_content(body, heading, next_heading)
        non_blank = [ln for ln in content.splitlines() if ln.strip()]
        assert non_blank, (
            f"{name}: section {heading!r} has no non-blank content"
        )


@pytest.mark.parametrize("name", REVIEWER_PERSONA_NAMES)
def test_reviewer_persona_has_review_dimensions(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    assert _heading_indices(body, REVIEWER_EXTRA_SECTION), (
        f"{name}: reviewer persona missing {REVIEWER_EXTRA_SECTION!r}"
    )


@pytest.mark.parametrize("name", IMPLEMENTER_PERSONA_NAMES)
def test_implementer_persona_does_not_have_review_dimensions(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    assert not _heading_indices(body, REVIEWER_EXTRA_SECTION), (
        f"{name}: implementer persona must not contain {REVIEWER_EXTRA_SECTION!r}"
    )


def test_architecture_reviewer_has_cross_context_impact_reporting() -> None:
    body = _strip_front_matter(persona_path("architecture-reviewer").read_text(encoding="utf-8"))
    assert _heading_indices(body, ARCHITECTURE_REVIEWER_EXTRA_SECTION), (
        f"architecture-reviewer: missing {ARCHITECTURE_REVIEWER_EXTRA_SECTION!r}"
    )


@pytest.mark.parametrize("name", tuple(n for n in PERSONA_NAMES if n != "architecture-reviewer"))
def test_non_architecture_reviewer_does_not_have_cross_context_section(name: str) -> None:
    body = _strip_front_matter(persona_path(name).read_text(encoding="utf-8"))
    assert not _heading_indices(body, ARCHITECTURE_REVIEWER_EXTRA_SECTION), (
        f"{name}: must not contain {ARCHITECTURE_REVIEWER_EXTRA_SECTION!r} "
        f"(reserved for architecture-reviewer per FR-014)"
    )
