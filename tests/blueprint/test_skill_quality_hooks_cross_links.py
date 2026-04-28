"""Tests for cross-links in skill files.

Slice 10 — AC-017: each of the five skill files contains the canonical cross-link.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The five skill files that must have the cross-link
SKILL_FILES = [
    REPO_ROOT / ".agents/skills/blueprint-sdd-step04-plan-slicer/SKILL.md",
    REPO_ROOT / ".agents/skills/blueprint-sdd-step05-implement/SKILL.md",
    REPO_ROOT / ".agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md",
    REPO_ROOT / ".agents/skills/blueprint-consumer-upgrade/SKILL.md",
    REPO_ROOT / ".agents/skills/blueprint-consumer-ops/SKILL.md",
]

CROSS_LINK_FRAGMENT = "AGENTS.md § Quality Hooks"


class TestSkillCrossLinks:
    """Each skill file has the canonical FR-016 cross-link (AC-017)."""

    def test_step04_plan_slicer_has_cross_link(self) -> None:
        content = SKILL_FILES[0].read_text(encoding="utf-8")
        assert CROSS_LINK_FRAGMENT in content, (
            f"blueprint-sdd-step04-plan-slicer/SKILL.md must contain the cross-link: {CROSS_LINK_FRAGMENT!r}"
        )

    def test_step05_implement_has_cross_link(self) -> None:
        content = SKILL_FILES[1].read_text(encoding="utf-8")
        assert CROSS_LINK_FRAGMENT in content, (
            f"blueprint-sdd-step05-implement/SKILL.md must contain the cross-link: {CROSS_LINK_FRAGMENT!r}"
        )

    def test_step07_pr_packager_has_cross_link(self) -> None:
        content = SKILL_FILES[2].read_text(encoding="utf-8")
        assert CROSS_LINK_FRAGMENT in content, (
            f"blueprint-sdd-step07-pr-packager/SKILL.md must contain the cross-link: {CROSS_LINK_FRAGMENT!r}"
        )

    def test_consumer_upgrade_has_cross_link(self) -> None:
        content = SKILL_FILES[3].read_text(encoding="utf-8")
        assert CROSS_LINK_FRAGMENT in content, (
            f"blueprint-consumer-upgrade/SKILL.md must contain the cross-link: {CROSS_LINK_FRAGMENT!r}"
        )

    def test_consumer_ops_has_cross_link(self) -> None:
        content = SKILL_FILES[4].read_text(encoding="utf-8")
        assert CROSS_LINK_FRAGMENT in content, (
            f"blueprint-consumer-ops/SKILL.md must contain the cross-link: {CROSS_LINK_FRAGMENT!r}"
        )

    def test_no_skill_has_restated_env_var_table(self) -> None:
        """Skills must not restate the full env var table from AGENTS.md."""
        env_var_table_marker = "| `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES`"
        for skill_file in SKILL_FILES:
            content = skill_file.read_text(encoding="utf-8")
            assert env_var_table_marker not in content, (
                f"{skill_file.name} must not restate the full QUALITY_HOOKS_KEEP_GOING_TAIL_LINES "
                "env var table (use the cross-link to AGENTS.md instead)"
            )
