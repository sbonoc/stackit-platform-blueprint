"""Old flat stage-persona files are deleted (issue #364, FR-011 / AC-013).

The repository MUST NOT carry both the stage-persona and expert-persona
roster shapes simultaneously. The 10 pre-existing flat `.md` files at the
root of `.agents/personas/` (from #360 / PR #362) MUST be deleted in the
same commit that introduces the 8 `.agents/personas/<slug>/PERSONA.md`
files. The `.agents/personas/consumer/` subdirectory (consumer shadow
space) MUST be preserved.
"""

from __future__ import annotations

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    OLD_FLAT_PERSONA_FILES,
    PERSONAS_DIR,
)


@pytest.mark.parametrize("filename", OLD_FLAT_PERSONA_FILES)
def test_old_flat_persona_file_is_absent(filename: str) -> None:
    p = PERSONAS_DIR / filename
    assert not p.exists(), (
        f"Old flat stage-persona file still present: {p}. FR-011 requires "
        f"deletion in the same commit that introduces the expert-persona "
        f"directory shape so the repository never carries both rosters."
    )


def test_consumer_overlay_directory_is_preserved() -> None:
    consumer = PERSONAS_DIR / "consumer"
    # Either absent (no consumer overlay yet) or present as a directory —
    # never a regular file or a leftover from the old shape.
    if consumer.exists():
        assert consumer.is_dir(), (
            f"{consumer} exists but is not a directory; FR-011 reserves the "
            f"consumer/ name as the consumer shadow-space subdirectory."
        )
