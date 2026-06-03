"""No stage-persona slug residue in PERSONA.md or SKILL.md files
(issue #364, FR-006 / AC-004).

ADR-issue-364 supersedes the stage-persona roster from #360 / PR #362.
The expert-persona panel files MUST NOT carry stage-persona slugs in body
text (Worldview, Push-back Triggers, etc.), AND skill runbooks MUST be
stripped of persona-coupling language so the orchestrator owns dispatch.

Ported from /tmp/verify_slice3.sh into pytest.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    SDD_STEP_SKILL_NAMES,
    SKILLS_DIR,
    STAGE_PERSONA_SLUGS,
    persona_path,
    skill_path,
)

STAGE_SLUG_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STAGE_PERSONA_SLUGS) + r")\b"
)


def _all_blueprint_skill_paths() -> list[str]:
    return sorted(
        p.parent.name
        for p in SKILLS_DIR.glob("blueprint-*/SKILL.md")
    )


ALL_BLUEPRINT_SKILL_NAMES: tuple[str, ...] = tuple(_all_blueprint_skill_paths())


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
def test_expert_persona_carries_no_stage_persona_slug(slug: str) -> None:
    body = persona_path(slug).read_text()
    matches = STAGE_SLUG_REGEX.findall(body)
    assert not matches, (
        f"{slug}/PERSONA.md references obsolete stage-persona slug(s) "
        f"{sorted(set(matches))!r} — ADR-issue-364 supersedes the stage-persona model"
    )


@pytest.mark.parametrize("skill", SDD_STEP_SKILL_NAMES)
def test_sdd_step_skill_carries_no_stage_persona_slug(skill: str) -> None:
    body = skill_path(skill).read_text()
    matches = STAGE_SLUG_REGEX.findall(body)
    assert not matches, (
        f"{skill}/SKILL.md references obsolete stage-persona slug(s) "
        f"{sorted(set(matches))!r} — strip per FR-006 (skill runbooks "
        f"MUST NOT couple to a stage-persona identity; orchestrator dispatches "
        f"the panel via the Contract C3 matrix)"
    )


@pytest.mark.parametrize("skill", ALL_BLUEPRINT_SKILL_NAMES)
def test_all_blueprint_skills_carry_no_stage_persona_slug(skill: str) -> None:
    body = skill_path(skill).read_text()
    matches = STAGE_SLUG_REGEX.findall(body)
    assert not matches, (
        f"{skill}/SKILL.md references obsolete stage-persona slug(s) "
        f"{sorted(set(matches))!r} — strip per FR-006 (all blueprint-* skill "
        f"runbooks MUST be free of stage-persona coupling; orchestrator dispatches "
        f"the panel via the Contract C3 matrix)"
    )
