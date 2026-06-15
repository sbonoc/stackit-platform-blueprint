"""Reciprocal `Amended-by` / `Superseded-by` lines on the four target ADRs
(issue #364, FR-005).

FR-005 mandates that:
- `ADR-issue-360-factory-personas-skills-roster.md` carries
  `Status: superseded` and links to the superseding ADR in its first
  body paragraph;
- `ADR-issue-337-persona-skill-contract.md`,
  `ADR-issue-337-c7-emission-mechanism.md`, and
  `ADR-issue-337-reviewer-model-heterogeneity.md` each receive an
  "Amended by ADR-issue-364-expert-persona-model.md" line.

This module enforces those reciprocal references so a future ADR edit
cannot silently strip them.
"""

from __future__ import annotations

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    AMENDED_ADRS_WITH_BACKREF,
    REPO_ROOT,
    SUPERSEDED_ADR,
)

ADR_DIR = REPO_ROOT / "docs" / "blueprint" / "architecture" / "decisions"
SUPERSEDING_ADR = "ADR-issue-364-expert-persona-model.md"


@pytest.mark.parametrize("adr_basename", AMENDED_ADRS_WITH_BACKREF)
def test_amended_adr_carries_backref_to_issue_364(adr_basename: str) -> None:
    path = ADR_DIR / adr_basename
    assert path.is_file(), f"target ADR missing on disk: {path}"
    body = path.read_text()
    head = "\n".join(body.splitlines()[:60])
    assert "Amended-by" in head or "Amended by" in head, (
        f"{adr_basename} missing an `Amended-by` line in its header block; "
        f"FR-005 requires the reciprocal back-reference."
    )
    assert SUPERSEDING_ADR in head, (
        f"{adr_basename} amendment header does not name {SUPERSEDING_ADR}; "
        f"FR-005 requires the back-reference to identify ADR-issue-364 by file name."
    )


def test_superseded_adr_carries_status_and_backref() -> None:
    path = ADR_DIR / SUPERSEDED_ADR
    assert path.is_file(), f"superseded ADR missing on disk: {path}"
    body = path.read_text()
    head = "\n".join(body.splitlines()[:60])

    assert "Status:" in head and "superseded" in head.lower(), (
        f"{SUPERSEDED_ADR} must declare `Status: superseded` in its header "
        f"block; FR-005."
    )
    assert SUPERSEDING_ADR in head, (
        f"{SUPERSEDED_ADR} must reference {SUPERSEDING_ADR} as the "
        f"superseding ADR in its header / first body paragraph; FR-005."
    )
