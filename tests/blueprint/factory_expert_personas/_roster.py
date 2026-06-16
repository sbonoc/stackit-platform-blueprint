"""Shared constants for the factory expert-persona panel tests (issue #364).

Ported from the slice 2/3/4 verification scripts under /tmp/verify_slice*.sh
into proper in-repo pytest assertions. Single source of truth for the
ADR-issue-364 § 3 expert roster and the Contract C3 dispatch matrix so the
test modules stay aligned with the spec without each module re-listing them.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PERSONAS_DIR = REPO_ROOT / ".agents" / "personas"
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

EXPERT_SLUGS: tuple[str, ...] = (
    "product-pragmatist",
    "boundary-hawk",
    "security-paranoid",
    "data-privacy",
    "test-quality-sceptic",
    "operability-sre",
    "documentation-discipline",
    "performance-cost-aware",
)

PERSONA_REQUIRED_SECTIONS: tuple[str, ...] = (
    "## Worldview",
    "## Default Heuristics",
    "## Push-back Triggers",
    "## What I Notice That Others Miss",
    "## Quality Bar",
    "## Communication Style",
)

PERSONA_FORBIDDEN_SECTIONS: tuple[str, ...] = (
    "## Activation Triggers",
    "## Skills Invoked",
    "## Definition of Done",
    "## Collaboration & Handoffs",
    "## Strict Guardrails",
    "## SDD Cycle Stakes",
    "## Required Inputs",
    "## Role Objective",
)

OLD_FLAT_PERSONA_FILES: tuple[str, ...] = (
    "po-analyst.md",
    "architect.md",
    "tech-lead.md",
    "implementer.md",
    "devsecops-qa.md",
    "doc-keeper.md",
    "security-reviewer.md",
    "architecture-reviewer.md",
    "contract-reviewer.md",
    "test-coverage-reviewer.md",
)

MIN_PUSH_BACK_TRIGGER_PHRASES: int = 6
MAX_PAIRWISE_TRIGGER_OVERLAP: int = 1

AMENDED_ADRS_WITH_BACKREF: tuple[str, ...] = (
    "ADR-issue-337-persona-skill-contract.md",
    "ADR-issue-337-c7-emission-mechanism.md",
    "ADR-issue-337-reviewer-model-heterogeneity.md",
)
SUPERSEDED_ADR: str = "ADR-issue-360-factory-personas-skills-roster.md"

CROSS_TICKET_AMENDMENT_TICKETS: tuple[str, ...] = (
    "#333",
    "#361",
    "#335",
    "#336",
    "#342",
    "#343",
    "#332",
    "#360",
    "#362",
)

STAGE_PERSONA_SLUGS: tuple[str, ...] = (
    "po-analyst",
    "architect",
    "tech-lead",
    "qa-engineer",
    "implementer",
    "implementer-backend",
    "implementer-frontend",
    "implementer-infra",
    "security-reviewer",
    "architecture-reviewer",
    "contract-reviewer",
    "test-coverage-reviewer",
    "reviewer-security",
    "reviewer-architecture",
    "reviewer-contracts",
    "reviewer-tests",
    "doc-keeper",
    "documentation-keeper",
    "devsecops-qa",
)

SDD_STEP_SKILL_NAMES: tuple[str, ...] = (
    "blueprint-sdd-step01-intake",
    "blueprint-sdd-step02-resolve-questions",
    "blueprint-sdd-step03-spec-complete",
    "blueprint-sdd-step04-plan-slicer",
    "blueprint-sdd-step05-implement",
    "blueprint-sdd-step06-document-sync",
    "blueprint-sdd-step07-pr-packager",
    "blueprint-sdd-step08-agent-pr-review",
)

EXPERT_VERDICTS_EXEMPT_STEPS: tuple[str, ...] = (
    "blueprint-sdd-step03-spec-complete",
)


def persona_path(slug: str) -> Path:
    return PERSONAS_DIR / slug / "PERSONA.md"


def skill_path(name: str) -> Path:
    return SKILLS_DIR / name / "SKILL.md"
