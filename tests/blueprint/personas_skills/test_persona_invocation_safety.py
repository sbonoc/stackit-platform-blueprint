"""T-105 — persona invocation-safety checks.

AC-009 (skill-path resolution) is added in Slice 2 after the new skill
directories exist. This module covers AC-010 (sign-off role absence) in
Slice 1 and is extended to AC-009 in Slice 2.

AC-010: No persona file MUST contain the four canonical sign-off phrases
        from FR-012 nor any plain-language equivalent ("grants Product
        sign-off", "approves architecture sign-off", "approves security
        sign-off", "approves operations sign-off").
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.personas_skills._roster import PERSONA_NAMES, persona_path

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
