"""Roster cardinality + structural assertions for the 8 expert PERSONA.md files
(issue #364, FR-001 / FR-011, AC-001 / AC-012).

Ported from /tmp/verify_slice2.sh into pytest. ADR-issue-364 § 3 locks the
8-expert ceiling; each PERSONA.md MUST carry the 6 required sections and MUST
NOT carry the 2 forbidden sections (Activation Triggers / Skills Invoked) —
the expert-panel layer MUST NOT directive-invoke skills (the orchestrator
owns dispatch via the Contract C3 matrix).
"""

from __future__ import annotations

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    PERSONAS_DIR,
    PERSONA_FORBIDDEN_SECTIONS,
    PERSONA_REQUIRED_SECTIONS,
    persona_path,
)


def test_persona_directory_contains_exactly_eight_expert_subdirs() -> None:
    subdirs = sorted(
        p.name for p in PERSONAS_DIR.iterdir() if p.is_dir() and p.name != "consumer"
    )
    assert subdirs == sorted(EXPERT_SLUGS), (
        f"expected exactly the 8 expert slugs from ADR-issue-364 § 3 under "
        f".agents/personas/ (plus optional consumer/ overlay); got {subdirs!r}"
    )


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
def test_expert_persona_md_exists(slug: str) -> None:
    p = persona_path(slug)
    assert p.is_file(), f"missing expert persona file: {p}"


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
@pytest.mark.parametrize("heading", PERSONA_REQUIRED_SECTIONS)
def test_expert_persona_contains_required_section(slug: str, heading: str) -> None:
    body = persona_path(slug).read_text()
    assert f"\n{heading}" in body or body.startswith(heading), (
        f"{slug}/PERSONA.md missing required section heading: {heading!r}"
    )


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
@pytest.mark.parametrize("heading", PERSONA_FORBIDDEN_SECTIONS)
def test_expert_persona_does_not_contain_forbidden_section(
    slug: str, heading: str
) -> None:
    body = persona_path(slug).read_text()
    assert heading not in body, (
        f"{slug}/PERSONA.md contains forbidden section {heading!r} — the "
        f"expert-panel layer MUST NOT directive-invoke skills (ADR-issue-364 § 2; "
        f"orchestrator owns dispatch via Contract C3)."
    )


def test_data_privacy_persona_distinguishes_from_security_paranoid() -> None:
    """ADR-issue-364 § 3 admission criterion: each expert MUST have distinct
    push-back triggers from every other expert. data-privacy and security-paranoid
    are the highest-collision pair (both touch sensitive-data flows); verify
    data-privacy's Worldview explicitly carries the data-protection-posture
    framing (data minimization / lawful basis / retention / subject rights)
    that distinguishes posture from threat-actor lens.
    """
    body = persona_path("data-privacy").read_text().lower()
    for needle in (
        "data minimization",
        "lawful basis",
        "retention",
        "subject rights",
    ):
        assert needle in body, (
            f"data-privacy/PERSONA.md missing distinguishing posture term {needle!r} "
            f"(ADR-issue-364 § 3 distinct-push-back-triggers admission criterion)"
        )
