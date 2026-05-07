"""Tests for .envrc and .claude/settings.json env kit.

Slice 10 — AC-018: .envrc and .claude/settings.json configuration.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENVRC = REPO_ROOT / ".envrc"
CLAUDE_SETTINGS = REPO_ROOT / ".claude/settings.json"


class TestEnvrc:
    """.envrc exports QUALITY_HOOKS_KEEP_GOING=true (AC-018)."""

    def test_envrc_exists(self) -> None:
        assert ENVRC.exists(), ".envrc must exist at repo root"

    def test_envrc_exports_keep_going(self) -> None:
        content = ENVRC.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_KEEP_GOING" in content, (
            ".envrc must export QUALITY_HOOKS_KEEP_GOING"
        )
        assert "true" in content, (
            ".envrc must set QUALITY_HOOKS_KEEP_GOING to true"
        )

    def test_envrc_does_not_set_force_full(self) -> None:
        content = ENVRC.read_text(encoding="utf-8")
        assert "QUALITY_HOOKS_FORCE_FULL" not in content, (
            ".envrc must NOT set QUALITY_HOOKS_FORCE_FULL (that would override all gating)"
        )


class TestClaudeSettings:
    """.claude/settings.json env block sets QUALITY_HOOKS_KEEP_GOING=true (AC-018)."""

    def test_claude_settings_exists(self) -> None:
        assert CLAUDE_SETTINGS.exists(), ".claude/settings.json must exist at repo root"

    def test_claude_settings_has_env_block(self) -> None:
        data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        assert "env" in data, ".claude/settings.json must contain an 'env' block"

    def test_claude_settings_keep_going_true(self) -> None:
        data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        env = data.get("env", {})
        assert env.get("QUALITY_HOOKS_KEEP_GOING") == "true", (
            ".claude/settings.json env block must set QUALITY_HOOKS_KEEP_GOING=true"
        )

    def test_claude_settings_no_force_full(self) -> None:
        data = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        env = data.get("env", {})
        assert "QUALITY_HOOKS_FORCE_FULL" not in env, (
            ".claude/settings.json must NOT set QUALITY_HOOKS_FORCE_FULL"
        )
