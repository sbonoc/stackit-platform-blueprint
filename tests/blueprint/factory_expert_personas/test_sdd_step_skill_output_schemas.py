"""SDD-step skill output schemas carry expert_verdicts where dispatched
(issue #364, FR-007 / AC-014).

ADR-issue-364 § 4 dispatches an expert panel at every SDD step except step03
(spec-complete; single lead voice, no panel). Each panel-dispatched SDD-step
SKILL.md MUST carry an output-schema fragment exposing the per-expert
verdicts array so the orchestrator can pack the merged array onto the C7
outcome.details.expert_verdicts[] extension field.

Ported from /tmp/verify_slice3.sh into pytest.
"""

from __future__ import annotations

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_VERDICTS_EXEMPT_STEPS,
    SDD_STEP_SKILL_NAMES,
    skill_path,
)


@pytest.mark.parametrize("skill", SDD_STEP_SKILL_NAMES)
def test_sdd_step_skill_has_required_output_schema_section(skill: str) -> None:
    body = skill_path(skill).read_text()
    assert "## Required Output Schema" in body, (
        f"{skill}/SKILL.md missing '## Required Output Schema' heading"
    )


@pytest.mark.parametrize(
    "skill",
    [s for s in SDD_STEP_SKILL_NAMES if s not in EXPERT_VERDICTS_EXEMPT_STEPS],
)
def test_panel_dispatched_step_schema_carries_expert_verdicts(skill: str) -> None:
    body = skill_path(skill).read_text()
    assert "expert_verdicts" in body, (
        f"{skill}/SKILL.md output schema missing expert_verdicts[] — the "
        f"orchestrator merges per-expert verdicts at this step per ADR-issue-364 § 4"
    )


@pytest.mark.parametrize(
    "skill",
    [s for s in SDD_STEP_SKILL_NAMES if s not in EXPERT_VERDICTS_EXEMPT_STEPS],
)
def test_panel_dispatched_step_schema_carries_expert_slug(skill: str) -> None:
    body = skill_path(skill).read_text()
    assert "expert_slug" in body, (
        f"{skill}/SKILL.md output schema missing expert_slug — per-expert "
        f"attribution is required per ADR-issue-364 § 6"
    )
