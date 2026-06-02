"""T-106 — reviewer persona structural assertions (FR-013, FR-014, FR-018).

AC-011: union of bulleted items under `## Review Dimensions` across the four
        reviewer personas contains zero duplicates after case-folding and
        whitespace-normalization.
AC-012: `.agents/personas/architecture-reviewer.md` contains a
        `## Cross-Context Impact Reporting` section with bullets covering:
        bounded contexts touched, downstream consumers impacted,
        contract-surface deltas, rollback risk.
AC-015: each of the 4 reviewer persona files contains a statement that the
        reviewer MUST run on a different model family than the implementer
        that produced the change under review AND cites
        `ADR-issue-337-reviewer-model-heterogeneity.md` by path.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import (
    REVIEWER_PERSONA_NAMES,
    persona_path,
)

REVIEW_DIMENSIONS_HEADING_RE = re.compile(
    r"^## Review Dimensions\s*$", re.MULTILINE
)
CROSS_CONTEXT_HEADING_RE = re.compile(
    r"^## Cross-Context Impact Reporting\s*$", re.MULTILINE
)
NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)

HETEROGENEITY_ADR_PATH = (
    "ADR-issue-337-reviewer-model-heterogeneity.md"
)


def _section(text: str, heading_re: re.Pattern[str]) -> str | None:
    match = heading_re.search(text)
    if match is None:
        return None
    start = match.end()
    next_match = NEXT_HEADING_RE.search(text, start)
    end = next_match.start() if next_match else len(text)
    return text[start:end]


def _bullets(section: str) -> list[str]:
    bullets: list[str] = []
    current: list[str] | None = None
    for raw in section.splitlines():
        if raw.lstrip().startswith("- "):
            if current is not None:
                bullets.append(" ".join(current).strip())
            current = [raw.lstrip()[2:].strip()]
        elif current is not None:
            stripped = raw.strip()
            if stripped == "":
                bullets.append(" ".join(current).strip())
                current = None
            else:
                current.append(stripped)
    if current is not None:
        bullets.append(" ".join(current).strip())
    return bullets


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


# -------- AC-011 — Reviewer dimensions non-overlapping ------------------------

def test_reviewer_dimensions_have_zero_duplicates_after_normalization() -> None:
    seen: dict[str, str] = {}
    for name in REVIEWER_PERSONA_NAMES:
        text = persona_path(name).read_text(encoding="utf-8")
        section = _section(text, REVIEW_DIMENSIONS_HEADING_RE)
        assert section is not None, (
            f"{name}: persona is missing the `## Review Dimensions` heading"
        )
        for bullet in _bullets(section):
            key = _normalize(bullet)
            assert key, f"{name}: review-dimension bullet is empty after normalization"
            prior = seen.get(key)
            assert prior is None, (
                f"review-dimension {bullet!r} duplicated across "
                f"{prior!r} and {name!r}"
            )
            seen[key] = name


# -------- AC-012 — Architecture-reviewer Cross-Context Impact Reporting ------

CROSS_CONTEXT_REQUIRED_TOKENS: tuple[tuple[str, str], ...] = (
    ("bounded contexts touched", "bounded contexts touched"),
    ("downstream consumers impacted", "downstream consumers impacted"),
    ("contract-surface deltas", "contract-surface deltas"),
    ("rollback risk", "rollback risk"),
)


@pytest.mark.parametrize(
    "label,token",
    CROSS_CONTEXT_REQUIRED_TOKENS,
    ids=[label for label, _ in CROSS_CONTEXT_REQUIRED_TOKENS],
)
def test_architecture_reviewer_cross_context_template_field(
    label: str, token: str
) -> None:
    text = persona_path("architecture-reviewer").read_text(encoding="utf-8")
    section = _section(text, CROSS_CONTEXT_HEADING_RE)
    assert section is not None, (
        "architecture-reviewer is missing the "
        "`## Cross-Context Impact Reporting` heading"
    )
    assert token in section.casefold(), (
        f"architecture-reviewer Cross-Context Impact Reporting section "
        f"missing required field {label!r} (token {token!r})"
    )


# -------- AC-015 — Reviewer model heterogeneity convention --------------------

@pytest.mark.parametrize("name", REVIEWER_PERSONA_NAMES)
def test_reviewer_persona_documents_model_heterogeneity(name: str) -> None:
    text = persona_path(name).read_text(encoding="utf-8")
    folded = text.casefold()
    assert "different model family" in folded, (
        f"{name}: persona missing reviewer-model-heterogeneity statement "
        f"(expected substring 'different model family')"
    )
    assert "implementer" in folded, (
        f"{name}: heterogeneity statement does not name the implementer"
    )
    assert HETEROGENEITY_ADR_PATH in text, (
        f"{name}: persona does not cite "
        f"{HETEROGENEITY_ADR_PATH!r} by path"
    )
