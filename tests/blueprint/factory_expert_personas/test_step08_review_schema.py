"""step08-agent-pr-review schema reshape assertions (issue #364, FR-007 / AC-011).

The step08 SKILL.md MUST carry the expert-panel shape:
- expert_slug enum spanning the 8-expert roster (NOT a reviewer_persona enum
  scoped to 4 stage-persona slugs);
- verdict enum (pass | revise | block) per ADR-issue-364 § 6;
- expert_verdicts[] array carried on outcome.details for orchestrator-merged
  per-expert attribution.

Ported from /tmp/verify_slice3.sh into pytest.
"""

from __future__ import annotations

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    skill_path,
)

STEP08 = "blueprint-sdd-step08-agent-pr-review"


def _body() -> str:
    return skill_path(STEP08).read_text()


def test_step08_schema_does_not_define_reviewer_persona_enum() -> None:
    body = _body()
    assert "reviewer_persona" not in body, (
        f"{STEP08}/SKILL.md still references reviewer_persona — the four "
        f"stage-persona reviewer slugs are replaced by the 8-expert roster "
        f"per ADR-issue-364 § 6"
    )


def test_step08_schema_defines_expert_slug_field() -> None:
    body = _body()
    assert "expert_slug" in body, (
        f"{STEP08}/SKILL.md missing expert_slug field — FR-007 / AC-011 require "
        f"per-expert attribution keyed by expert_slug"
    )


def test_step08_schema_defines_expert_verdicts_array() -> None:
    body = _body()
    assert "expert_verdicts" in body, (
        f"{STEP08}/SKILL.md missing expert_verdicts[] array — the orchestrator "
        f"merges per-expert verdicts into outcome.details.expert_verdicts[] "
        f"per ADR-issue-364 § 6"
    )


def test_step08_schema_defines_verdict_enum_values() -> None:
    body = _body()
    for verdict in ("pass", "revise", "block"):
        assert verdict in body, (
            f"{STEP08}/SKILL.md missing verdict enum value {verdict!r} — "
            f"always-respond verdict contract per ADR-issue-364 § 6"
        )


def test_step08_schema_enumerates_all_eight_expert_slugs() -> None:
    body = _body()
    missing = [slug for slug in EXPERT_SLUGS if slug not in body]
    assert not missing, (
        f"{STEP08}/SKILL.md does not enumerate all 8 expert slugs in its "
        f"expert_slug enum; missing: {missing!r}"
    )
