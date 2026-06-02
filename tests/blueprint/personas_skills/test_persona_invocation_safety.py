"""T-105 — persona invocation-safety checks.

AC-009: Every `.agents/skills/<name>` path token under any `## Skills Invoked`
        section of any persona file resolves to a directory that exists in
        the repo. (Closed in slice 2.)
AC-010: No persona file MUST contain the four canonical sign-off phrases
        from FR-012 nor any plain-language equivalent ("grants Product
        sign-off", "approves architecture sign-off", "approves security
        sign-off", "approves operations sign-off"). (Slice 1.)
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import (
    PERSONA_NAMES,
    REPO_ROOT,
    persona_path,
)

# FR-012: canonical sign-off phrases (sealed under design-contracts.md
# FR-017(b) item 2).
CANONICAL_SIGNOFF_PHRASES: tuple[str, ...] = (
    "SPEC_PRODUCT_READY: approved",
    "ARCHITECTURE_SIGNOFF: approved",
    "SECURITY_SIGNOFF: approved",
    "OPERATIONS_SIGNOFF: approved",
)

# FR-012 plain-language equivalents.
PLAIN_LANGUAGE_SIGNOFF_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bgrants?\s+product\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bapproves?\s+architecture\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bapproves?\s+security\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bapproves?\s+operations\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bgrants?\s+architecture\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bgrants?\s+security\s+sign[- ]?off\b", re.IGNORECASE),
    re.compile(r"\bgrants?\s+operations\s+sign[- ]?off\b", re.IGNORECASE),
)


@pytest.mark.parametrize("name", PERSONA_NAMES)
@pytest.mark.parametrize("phrase", CANONICAL_SIGNOFF_PHRASES)
def test_persona_does_not_contain_canonical_signoff_phrase(name: str, phrase: str) -> None:
    text = persona_path(name).read_text(encoding="utf-8")
    assert phrase not in text, (
        f"{name}: persona file contains canonical sign-off phrase {phrase!r}; "
        f"FR-012 forbids personas from claiming canonical sign-off authority"
    )


@pytest.mark.parametrize("name", PERSONA_NAMES)
@pytest.mark.parametrize(
    "pattern", PLAIN_LANGUAGE_SIGNOFF_PATTERNS, ids=lambda p: p.pattern
)
def test_persona_does_not_contain_plain_language_signoff(
    name: str, pattern: re.Pattern[str]
) -> None:
    text = persona_path(name).read_text(encoding="utf-8")
    match = pattern.search(text)
    assert match is None, (
        f"{name}: persona file contains plain-language sign-off equivalent "
        f"matching {pattern.pattern!r} at {match.group(0)!r}; FR-012 forbids "
        f"plain-language sign-off equivalents"
    )


# AC-009 — skill-path resolution under ## Skills Invoked.

SKILLS_INVOKED_HEADING_RE = re.compile(r"^## Skills Invoked\s*$", re.MULTILINE)
NEXT_H2_RE = re.compile(r"^## \S", re.MULTILINE)
# Match either backticked or bare `.agents/skills/<name>/` paths.
SKILL_PATH_TOKEN_RE = re.compile(r"\.agents/skills/([A-Za-z0-9._-]+)/?")


def _skills_invoked_section(text: str) -> str | None:
    heading_match = SKILLS_INVOKED_HEADING_RE.search(text)
    if heading_match is None:
        return None
    start = heading_match.end()
    # Find the next H2 heading after this one.
    next_match = NEXT_H2_RE.search(text, start)
    end = next_match.start() if next_match else len(text)
    return text[start:end]


@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_skills_invoked_references_resolve(name: str) -> None:
    text = persona_path(name).read_text(encoding="utf-8")
    section = _skills_invoked_section(text)
    assert section is not None, f"{name}: missing ## Skills Invoked section"

    skill_names_referenced = SKILL_PATH_TOKEN_RE.findall(section)
    assert skill_names_referenced, (
        f"{name}: ## Skills Invoked section has no `.agents/skills/<name>/` "
        f"path tokens; persona MUST list at least one invoked skill"
    )

    unresolved: list[str] = []
    for skill_name in skill_names_referenced:
        target = REPO_ROOT / ".agents" / "skills" / skill_name
        if not target.is_dir():
            unresolved.append(skill_name)
    assert not unresolved, (
        f"{name}: ## Skills Invoked references unresolved skill paths: "
        f"{unresolved}"
    )
