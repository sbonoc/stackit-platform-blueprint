"""Shared constants for the factory persona + skill roster tests (issue #360).

Single source of truth for the FR-001 / FR-002 / FR-020 file paths so the
test modules stay aligned with the spec text without each module re-listing
the same paths.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PERSONAS_DIR = REPO_ROOT / ".agents" / "personas"
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

IMPLEMENTER_PERSONA_NAMES: tuple[str, ...] = (
    "po-analyst",
    "architect",
    "tech-lead",
    "implementer",
    "devsecops-qa",
    "doc-keeper",
)

REVIEWER_PERSONA_NAMES: tuple[str, ...] = (
    "security-reviewer",
    "architecture-reviewer",
    "contract-reviewer",
    "test-coverage-reviewer",
)

PERSONA_NAMES: tuple[str, ...] = IMPLEMENTER_PERSONA_NAMES + REVIEWER_PERSONA_NAMES

NEW_SKILL_NAMES: tuple[str, ...] = (
    "blueprint-ticket-triage-size",
    "blueprint-ticket-decompose-light",
    "blueprint-agent-secret-scan",
    "blueprint-agent-handoff",
    "blueprint-spec-revision-handoff",
    "blueprint-spec-review-prep",
    "blueprint-human-review-prep",
    "blueprint-sdd-step08-agent-pr-review",
    "blueprint-pr-review-respond",
    "blueprint-agent-stop-cleanup",
)

EXISTING_SDD_SKILL_NAMES: tuple[str, ...] = (
    "blueprint-sdd-step01-intake",
    "blueprint-sdd-step02-resolve-questions",
    "blueprint-sdd-step03-spec-complete",
    "blueprint-sdd-step04-plan-slicer",
    "blueprint-sdd-step05-implement",
    "blueprint-sdd-step06-document-sync",
    "blueprint-sdd-step07-pr-packager",
    "blueprint-sdd-traceability-keeper",
)


def persona_path(name: str) -> Path:
    return PERSONAS_DIR / f"{name}.md"


def new_skill_path(name: str) -> Path:
    return SKILLS_DIR / name / "SKILL.md"


def existing_skill_path(name: str) -> Path:
    return SKILLS_DIR / name / "SKILL.md"
