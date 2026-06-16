"""AGENTS.md operator-default scoping + Persona-precedence paragraph
(issue #364, FR-012 / AC-015).

ADR-issue-364 § 5 requires AGENTS.md § Role and Philosophy to declare its
operator-default scope so that dispatched experts read their *worldview* from
their loaded PERSONA.md § Worldview rather than from this section. Procedural
governance (SDD lifecycle, sign-off policy, etc.) continues to apply to every
expert without exception.

Ported from /tmp/verify_slice4.sh into pytest.
"""

from __future__ import annotations

from tests.blueprint.factory_expert_personas._roster import REPO_ROOT

AGENTS_MD = REPO_ROOT / "AGENTS.md"


def _body() -> str:
    return AGENTS_MD.read_text()


def test_role_and_philosophy_heading_carries_operator_default_qualifier() -> None:
    body = _body()
    assert "## Role and Philosophy (operator-default" in body, (
        "AGENTS.md '## Role and Philosophy' heading must carry the "
        "'operator-default' scope qualifier per FR-012"
    )


def test_persona_precedence_paragraph_is_present() -> None:
    body = _body()
    assert "**Persona precedence.**" in body, (
        "AGENTS.md must carry a '**Persona precedence.**' paragraph that "
        "defers identity to the loaded PERSONA.md § Worldview during expert dispatch"
    )


def test_no_unscoped_role_and_philosophy_heading() -> None:
    lines = _body().splitlines()
    unscoped = [ln for ln in lines if ln.rstrip() == "## Role and Philosophy"]
    assert not unscoped, (
        "AGENTS.md must not carry an unscoped '## Role and Philosophy' heading; "
        "the only acceptable form is the operator-default-qualified heading"
    )
