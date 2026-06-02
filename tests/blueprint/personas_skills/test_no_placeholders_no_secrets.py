"""T-103 — no placeholder tokens + no secret patterns in any new file.

AC-006: No occurrence of the SDD unresolved-work-marker strings from
        `blueprint/contract.yaml` § normative_language.unresolved_marker_tokens,
        the SDD clarification marker token defined in
        `AGENTS.md § Clarification Marker Policy`, or unquoted `<...>`-style
        angle-bracket placeholders in any of the 20 new files; AND zero
        baseline secret-pattern matches.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.blueprint.personas_skills._roster import (
    NEW_SKILL_NAMES,
    PERSONA_NAMES,
    REPO_ROOT,
    new_skill_path,
    persona_path,
)


def _load_unresolved_marker_tokens() -> list[str]:
    text = (REPO_ROOT / "blueprint" / "contract.yaml").read_text(encoding="utf-8")
    contract = yaml.safe_load(text)
    tokens = (
        contract["spec"]["spec_driven_development_contract"]["normative_language"][
            "unresolved_marker_tokens"
        ]
    )
    assert isinstance(tokens, list) and tokens, "unresolved_marker_tokens must be populated"
    return [str(t) for t in tokens]


UNRESOLVED_MARKER_TOKENS = _load_unresolved_marker_tokens()
CLARIFICATION_MARKER = "[NEEDS CLARIFICATION:"

# FR-008: angle-bracket-style placeholder; alphanumeric or kebab-case identifier
# inside `<...>`. Permissive enough to catch `<slug>`, `<n>`, `<work-item-slug>`,
# `<list of ...>`. Excluded: tokens with whitespace at the immediate boundary
# (those are part of HTML-like comments or arrow markers).
ANGLE_PLACEHOLDER_RE = re.compile(r"<[A-Za-z][\w.\- ]*>")

# Baseline secret patterns — conservative, covering AWS access keys, private-key
# armor blocks, GitHub bearer tokens. Documentation references are excluded by
# anchoring on the canonical literal forms.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("PEM private key header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub bearer token", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("GitHub server token", re.compile(r"\bghs_[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
)


def _new_files() -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    for name in PERSONA_NAMES:
        files.append((f"persona/{name}", persona_path(name)))
    for name in NEW_SKILL_NAMES:
        files.append((f"skill/{name}", new_skill_path(name)))
    return files


@pytest.mark.parametrize("label,path", _new_files(), ids=lambda v: v if isinstance(v, str) else v.name)
@pytest.mark.parametrize("token", UNRESOLVED_MARKER_TOKENS)
def test_no_unresolved_marker_tokens(label: str, path: Path, token: str) -> None:
    text = path.read_text(encoding="utf-8")
    # Word-boundary scan for alphanumeric tokens; literal scan for `???`.
    if token.isalnum():
        pattern = re.compile(rf"\b{re.escape(token)}\b")
        match = pattern.search(text)
        assert match is None, (
            f"{label}: unresolved-marker token {token!r} present at "
            f"line {text[:match.start()].count(chr(10)) + 1}"
        )
    else:
        assert token not in text, (
            f"{label}: unresolved-marker token {token!r} present"
        )


@pytest.mark.parametrize("label,path", _new_files(), ids=lambda v: v if isinstance(v, str) else v.name)
def test_no_clarification_marker(label: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert CLARIFICATION_MARKER not in text, (
        f"{label}: SDD clarification marker {CLARIFICATION_MARKER!r} present"
    )


@pytest.mark.parametrize("label,path", _new_files(), ids=lambda v: v if isinstance(v, str) else v.name)
def test_no_angle_bracket_placeholders(label: str, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = ANGLE_PLACEHOLDER_RE.search(text)
    assert match is None, (
        f"{label}: angle-bracket placeholder {match.group(0)!r} present at "
        f"line {text[:match.start()].count(chr(10)) + 1}"
    )


@pytest.mark.parametrize("label,path", _new_files(), ids=lambda v: v if isinstance(v, str) else v.name)
@pytest.mark.parametrize(
    "secret_label,pattern",
    SECRET_PATTERNS,
    ids=[label for label, _ in SECRET_PATTERNS],
)
def test_no_secret_pattern_match(
    label: str, path: Path, secret_label: str, pattern: re.Pattern[str]
) -> None:
    text = path.read_text(encoding="utf-8")
    match = pattern.search(text)
    assert match is None, (
        f"{label}: {secret_label} pattern matched {match.group(0)!r}"
    )
