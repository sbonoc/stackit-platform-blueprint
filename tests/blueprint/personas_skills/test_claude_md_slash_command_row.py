"""T-109 — CLAUDE.md Skills slash-command table row for step08 (AC-016, FR-019).

AC-016: CLAUDE.md MUST contain EXACTLY ONE table row whose slash-command cell
is ``/blueprint-sdd-step08-agent-pr-review`` and whose runbook-path cell is
``.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md``; AND no other
row references any of the 9 other new skill names from FR-002.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import NEW_SKILL_NAMES, REPO_ROOT

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

STEP08_SLASH = "/blueprint-sdd-step08-agent-pr-review"
STEP08_RUNBOOK = ".agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md"

OTHER_NEW_SKILL_NAMES: tuple[str, ...] = tuple(
    name for name in NEW_SKILL_NAMES if name != "blueprint-sdd-step08-agent-pr-review"
)


def _table_rows() -> list[str]:
    """Return non-header markdown table rows from CLAUDE.md."""
    rows: list[str] = []
    for raw in CLAUDE_MD.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.startswith("|"):
            continue
        # Skip header separator rows like `|---|---|---|---|`
        if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        rows.append(line)
    return rows


def test_claude_md_contains_exactly_one_step08_slash_command_row() -> None:
    matching = [
        r for r in _table_rows()
        if f"`{STEP08_SLASH}`" in r and f"`{STEP08_RUNBOOK}`" in r
    ]
    assert len(matching) == 1, (
        f"CLAUDE.md MUST contain EXACTLY ONE row with slash-command "
        f"`{STEP08_SLASH}` and runbook `{STEP08_RUNBOOK}`; got {len(matching)} "
        f"matching rows: {matching!r}"
    )


@pytest.mark.parametrize("other_name", OTHER_NEW_SKILL_NAMES)
def test_claude_md_does_not_reference_other_new_skill_names_in_table_rows(
    other_name: str,
) -> None:
    offenders = [
        r for r in _table_rows()
        if re.search(rf"\b{re.escape(other_name)}\b", r)
    ]
    assert not offenders, (
        f"CLAUDE.md table MUST NOT reference new skill `{other_name}` "
        f"(persona-invoked only per FR-019); offending rows: {offenders!r}"
    )
