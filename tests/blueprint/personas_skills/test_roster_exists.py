"""T-101 — file-existence + roster cardinality checks.

AC-001: exactly 10 persona files under `.agents/personas/<name>.md` matching
        the FR-001 split (6 implementer + 4 reviewer); no more, no fewer.
AC-002: each of the 10 new skill directories from FR-002 contains a SKILL.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.blueprint.personas_skills._roster import (
    NEW_SKILL_NAMES,
    PERSONA_NAMES,
    PERSONAS_DIR,
    new_skill_path,
    persona_path,
)


@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_file_exists(name: str) -> None:
    path = persona_path(name)
    assert path.is_file(), f"persona file missing: {path.relative_to(PERSONAS_DIR.parent.parent)}"


def test_persona_roster_is_exactly_ten_named_files() -> None:
    actual = {p.stem for p in PERSONAS_DIR.glob("*.md") if p.is_file()}
    expected = set(PERSONA_NAMES)
    extra = actual - expected
    missing = expected - actual
    assert not extra, f"unexpected persona files: {sorted(extra)}"
    assert not missing, f"missing persona files: {sorted(missing)}"
    assert len(actual) == 10, f"expected exactly 10 personas, got {len(actual)}"


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_skill_md(name: str) -> None:
    path = new_skill_path(name)
    assert path.is_file(), f"new skill SKILL.md missing: {path}"
