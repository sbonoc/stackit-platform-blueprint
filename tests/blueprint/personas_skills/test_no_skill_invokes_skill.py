"""T-107 — no new SKILL.md directive-invokes another skill (FR-016, AC-013).

AC-013: No new SKILL.md contains any of:
  - a `Skill(` token,
  - a `/blueprint-` token on a line that starts with `Invoke`, `Run`, `Call`,
    or `Execute`,
  - an `Invoke skill:` directive.

Prose mentions of skill names elsewhere remain permitted (skill composition is
a persona-layer responsibility per `ADR-issue-337-persona-skill-contract.md`).
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import NEW_SKILL_NAMES, new_skill_path

INVOKE_VERB_RE = re.compile(
    r"^\s*(?:Invoke|Run|Call|Execute)\b[^\n]*?/blueprint-",
    re.MULTILINE | re.IGNORECASE,
)
INVOKE_SKILL_DIRECTIVE_RE = re.compile(r"\bInvoke\s+skill\s*:", re.IGNORECASE)


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_no_skill_function_call_token(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    assert "Skill(" not in text, (
        f"{name}: SKILL.md MUST NOT contain a `Skill(` invocation token; "
        "skill composition is a persona-layer responsibility."
    )


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_no_slash_command_invocation_directive(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    hits = INVOKE_VERB_RE.findall(text)
    assert not hits, (
        f"{name}: SKILL.md MUST NOT contain a directive-invoke line "
        f"(Invoke|Run|Call|Execute … /blueprint-…); offending matches: {hits!r}"
    )


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_no_invoke_skill_directive(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    assert not INVOKE_SKILL_DIRECTIVE_RE.search(text), (
        f"{name}: SKILL.md MUST NOT contain an `Invoke skill:` directive."
    )
