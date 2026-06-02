"""T-104 — DevSecOps/QA + Tech Lead `## Definition of Done (DoD)` phrase coverage.

AC-007: `.agents/personas/devsecops-qa.md` `## Definition of Done (DoD)` section
        contains separate bullet items for the three FR-009 phrases:
        (a) PII exclusion, (b) non-root container constraint,
        (c) `hardening_review.md` produced via `make quality-hardening-review` and
        clean before handoff to `blueprint-sdd-step07-pr-packager`.

AC-008: `.agents/personas/tech-lead.md` `## Definition of Done (DoD)` section
        contains separate bullet items for the four FR-010 phrases:
        (a) `blueprint-ticket-triage-size` runs first on every ticket,
        (b) `blueprint-ticket-decompose-light` invoked on `large-decomposable`,
        (c) every sub-ticket grounds in the parent spec and cites its boundary type,
        (d) sub-ticket fan-out MUST NOT exceed the maximum defined in
        `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md`.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import persona_path

DOD_HEADING_RE = re.compile(
    r"^## Definition of Done \(DoD\)\s*$", re.MULTILINE
)
NEXT_HEADING_RE = re.compile(r"^## ", re.MULTILINE)


def _dod_section(text: str) -> str:
    match = DOD_HEADING_RE.search(text)
    assert match is not None, "persona is missing the `## Definition of Done (DoD)` heading"
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


# -------- AC-007 — DevSecOps/QA DoD has the three FR-009 bullet items ---------

DEVSECOPS_QA_BULLET_TOKENS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("PII exclusion bullet", ("PII",)),
    ("non-root container bullet", ("non-root container",)),
    (
        "hardening_review.md clean before step07 handoff bullet",
        (
            "hardening_review.md",
            "make quality-hardening-review",
            "blueprint-sdd-step07-pr-packager",
        ),
    ),
)


@pytest.mark.parametrize(
    "label,required_tokens",
    DEVSECOPS_QA_BULLET_TOKENS,
    ids=[label for label, _ in DEVSECOPS_QA_BULLET_TOKENS],
)
def test_devsecops_qa_dod_has_required_bullet(
    label: str, required_tokens: tuple[str, ...]
) -> None:
    text = persona_path("devsecops-qa").read_text(encoding="utf-8")
    section = _dod_section(text)
    bullets = _bullets(section)
    assert any(
        all(token in bullet for token in required_tokens)
        for bullet in bullets
    ), f"devsecops-qa DoD missing {label} (required tokens: {required_tokens!r})"


# -------- AC-008 — Tech Lead DoD has the four FR-010 bullet items -------------

TECH_LEAD_BULLET_TOKENS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "triage-size first bullet",
        ("blueprint-ticket-triage-size",),
    ),
    (
        "decompose-light on large-decomposable bullet",
        ("blueprint-ticket-decompose-light", "large-decomposable"),
    ),
    (
        "sub-ticket grounds in parent spec + cites boundary type bullet",
        ("boundary type",),
    ),
    (
        "fan-out limit per Phase 0 ADR bullet",
        ("ADR-issue-337-light-decomposition-policy.md",),
    ),
)


@pytest.mark.parametrize(
    "label,required_tokens",
    TECH_LEAD_BULLET_TOKENS,
    ids=[label for label, _ in TECH_LEAD_BULLET_TOKENS],
)
def test_tech_lead_dod_has_required_bullet(
    label: str, required_tokens: tuple[str, ...]
) -> None:
    text = persona_path("tech-lead").read_text(encoding="utf-8")
    section = _dod_section(text)
    bullets = _bullets(section)
    assert any(
        all(token in bullet for token in required_tokens)
        for bullet in bullets
    ), f"tech-lead DoD missing {label} (required tokens: {required_tokens!r})"
