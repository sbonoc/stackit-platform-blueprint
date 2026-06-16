"""design-contracts.md alignment with the ADR-issue-364 expert-persona model
(issue #364, FR-005 / FR-007 / FR-009 / FR-010 / AC-002 / AC-008 / AC-009 / AC-010).

Verifies:
- Contract C3 carries the 8-row SDD-step × expert dispatch matrix and
  cross-references ADR-issue-364 (single source of truth);
- Contract C7 'persona' field carries the draft-producing skill basename
  semantics and the additive expert_verdicts[] extension is documented;
- Contract C8 § Category (c) lists exactly the 8 expert PERSONA.md rows
  under #364 ownership and does NOT carry any of the 10 deleted stage-persona
  rows;
- the bootstrap template mirror is in sync.

Ported from /tmp/verify_slice4.sh into pytest.
"""

from __future__ import annotations

import re

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    REPO_ROOT,
)

DC = REPO_ROOT / "docs" / "blueprint" / "autonomous-factory" / "design-contracts.md"
TEMPLATE = (
    REPO_ROOT
    / "scripts"
    / "templates"
    / "blueprint"
    / "bootstrap"
    / "docs"
    / "blueprint"
    / "autonomous-factory"
    / "design-contracts.md"
)


def _section(body: str, start_pattern: str, end_pattern: str) -> str:
    start = re.search(start_pattern, body, flags=re.MULTILINE)
    assert start, f"section start {start_pattern!r} not found"
    end = re.search(end_pattern, body[start.end():], flags=re.MULTILINE)
    assert end, f"section end {end_pattern!r} not found"
    return body[start.start() : start.end() + end.start()]


def _c3() -> str:
    return _section(DC.read_text(), r"^## Contract C3 ", r"^## Contract C4 ")


def _c7() -> str:
    return _section(DC.read_text(), r"^## Contract C7 ", r"^## Contract C8 ")


def _c8_category_c() -> str:
    return _section(DC.read_text(), r"^### Category \(c\) ", r"^### Category \(d\) ")


def test_c3_mentions_every_expert_slug() -> None:
    block = _c3()
    missing = [slug for slug in EXPERT_SLUGS if slug not in block]
    assert not missing, (
        f"design-contracts § C3 dispatch matrix missing expert slugs: {missing!r}"
    )


def test_c3_cross_references_adr_issue_364() -> None:
    assert "ADR-issue-364-expert-persona-model" in _c3(), (
        "design-contracts § C3 must cross-reference ADR-issue-364 (single source rule)"
    )


def test_c3_header_text_matches_spec() -> None:
    expected_header = (
        "| SDD step | Skill | Experts consulted | Lead voice | Convergence mode |"
    )
    assert expected_header in _c3(), (
        "design-contracts § C3 dispatch matrix header must match the exact 5-column "
        "shape required by AC-003 / ADR-issue-364 § 4: "
        f"{expected_header!r}"
    )


def test_c7_persona_field_carries_skill_basename_semantics() -> None:
    assert "draft-producing skill basename" in _c7(), (
        "design-contracts § C7 'persona' field description must carry the "
        "skill-basename semantics introduced by ADR-issue-364 § 2"
    )


def test_c7_documents_expert_verdicts_extension() -> None:
    assert "outcome_details.expert_verdicts" in _c7(), (
        "design-contracts § C7 must document the additive "
        "outcome_details.expert_verdicts[] sibling extension field "
        "(FR-007; sibling of the sealed-string `outcome` per the C7 "
        "extension-field naming convention)"
    )


def test_c8_category_c_lists_every_expert_persona_md() -> None:
    block = _c8_category_c()
    for slug in EXPERT_SLUGS:
        path = f".agents/personas/{slug}/PERSONA.md"
        assert path in block, (
            f"design-contracts § C8 (c) missing row for expert PERSONA.md: {path}"
        )


def test_c8_category_c_does_not_carry_obsolete_stage_persona_rows() -> None:
    block = _c8_category_c()
    for old in (
        "po-analyst.md",
        "architect.md",
        "tech-lead.md",
        "implementer.md",
        "devsecops-qa.md",
        "doc-keeper.md",
        "security-reviewer.md",
        "architecture-reviewer.md",
        "contract-reviewer.md",
        "test-coverage-reviewer.md",
    ):
        assert f".agents/personas/{old}" not in block, (
            f"design-contracts § C8 (c) still lists obsolete stage-persona row: {old}"
        )


def test_bootstrap_template_mirror_is_in_sync() -> None:
    assert DC.read_text() == TEMPLATE.read_text(), (
        "bootstrap template mirror is out of sync with the canonical "
        "design-contracts.md; run "
        "`uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py`"
    )
