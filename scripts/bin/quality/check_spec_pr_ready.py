#!/usr/bin/env python3
"""Validate SDD publish-gate files before opening a PR.

Checks plan.md, tasks.md, hardening_review.md, and pr_context.md for
unfilled scaffold placeholders. Resolves the active spec directory from
SPEC_SLUG env var or the current git branch name (pattern:
codex/YYYY-MM-DD-<slug>).

Usage:
    make quality-spec-pr-ready
    SPEC_SLUG=2026-04-22-my-work-item python3 scripts/bin/quality/check_spec_pr_ready.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PREFIX = "[quality-spec-pr-ready]"

_SDD_BRANCH_PATTERN = re.compile(r"^codex/(\d{4}-\d{2}-\d{2}-.+)$")

# Verbatim scaffold task subjects from the tasks.md template (T-001 through T-004).
# These must be replaced with actual work descriptions before opening a PR.
_SCAFFOLD_TASK_SUBJECTS: tuple[str, ...] = (
    "Update contract/governance surfaces",
    "Implement runtime/code changes",
    "Update blueprint docs/diagrams",
    "Update consumer-facing docs/diagrams when contracts/behavior change",
)

# plan.md fields that must have non-empty inline content after "- <field>:"
_PLAN_INLINE_FIELDS: tuple[str, ...] = (
    "Simplicity gate:",
    "Anti-abstraction gate:",
    "Integration-first testing gate:",
    "Positive-path filter/transform test gate:",
    "Finding-to-test translation gate:",
    "Migration/rollout sequence:",
    "Backward compatibility policy:",
    "Rollback plan:",
    "Unit checks:",
    "Contract checks:",
    "Integration checks:",
    "E2E checks:",
    "Blueprint docs updates:",
    "Consumer docs updates:",
    "Mermaid diagrams updated:",
    "Logging/metrics/traces:",
    "Alerts/ownership:",
    "Runbook updates:",
)

# pr_context.md required inline fields
_PR_CONTEXT_INLINE_FIELDS: tuple[str, ...] = (
    "Work item:",
    "Objective:",
    "Scope boundaries:",
    "Requirement IDs covered:",
    "Acceptance criteria covered:",
    "Required commands executed:",
    "Result summary:",
    "Main risks:",
    "Rollback strategy:",
)

# hardening_review.md observability sub-fields
_HARDENING_OBSERVABILITY_FIELDS: tuple[str, ...] = (
    "Metrics/logging/tracing updates:",
    "Operational diagnostics updates:",
)

# hardening_review.md architecture/quality sub-fields
_HARDENING_ARCHITECTURE_FIELDS: tuple[str, ...] = (
    "SOLID / Clean Architecture / Clean Code / DDD checks:",
    "Test-automation and pyramid checks:",
    "Documentation/diagram/CI/skill consistency checks:",
)


def _resolve_spec_dir(repo_root: Path) -> Path:
    """Resolve spec directory from SPEC_SLUG env var or git branch."""
    spec_slug = os.environ.get("SPEC_SLUG", "").strip()
    if spec_slug:
        return repo_root / "specs" / spec_slug

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        branch = ""

    match = _SDD_BRANCH_PATTERN.match(branch)
    if not match:
        print(
            f"{PREFIX} cannot resolve spec directory: branch '{branch}' does not match "
            f"pattern codex/YYYY-MM-DD-<slug>; set SPEC_SLUG env var to override",
            file=sys.stderr,
        )
        sys.exit(1)

    return repo_root / "specs" / match.group(1)


def _check_tasks(content: str, file_name: str) -> list[str]:
    """Check tasks.md for unchecked boxes and verbatim scaffold placeholders."""
    violations: list[str] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Unchecked task boxes
        if re.match(r"^-\s+\[\s+\]", stripped):
            violations.append(
                f"{PREFIX} {file_name}:{i}: unchecked task box — mark [x] before opening a PR: {stripped[:80]}"
            )
        # Verbatim scaffold task subjects (T-001 through T-004)
        for subject in _SCAFFOLD_TASK_SUBJECTS:
            if subject in line:
                violations.append(
                    f"{PREFIX} {file_name}:{i}: verbatim scaffold task text found — "
                    f"replace with actual work description: {stripped[:80]}"
                )
                break

    # P-001, P-002, P-003 must each appear as [x]
    for publish_task in ("P-001", "P-002", "P-003"):
        found_checked = any(
            re.search(r"\[x\]", ln, re.IGNORECASE) and publish_task in ln
            for ln in lines
        )
        if not found_checked:
            violations.append(
                f"{PREFIX} {file_name}: publish task {publish_task} must be present and marked [x]"
            )

    return violations


def _check_plan(content: str, file_name: str) -> list[str]:
    """Check plan.md for empty required fields and scaffold placeholders."""
    violations: list[str] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Required inline fields: "- FieldName:" with nothing after the colon
        for field in _PLAN_INLINE_FIELDS:
            if stripped == f"- {field}":
                violations.append(
                    f"{PREFIX} {file_name}:{i}: `{field}` must have non-empty content after the colon"
                )
                break

        # Delivery slice placeholders: "1. Slice 1:" or "2. Slice 2:" with nothing after colon
        if re.match(r"^\d+\.\s+Slice\s+\d+:\s*$", stripped):
            violations.append(
                f"{PREFIX} {file_name}:{i}: delivery slice placeholder — "
                f"replace with concrete slice description: {stripped}"
            )

        # App onboarding impact not resolved (scaffold has "no-impact | impacted (select one)")
        if "no-impact | impacted (select one)" in line:
            violations.append(
                f"{PREFIX} {file_name}:{i}: app onboarding impact must be resolved to "
                "`no-impact` or `impacted` (remove the `| impacted (select one)` suffix)"
            )

        # Risk -> mitigation placeholder: "- Risk N -> mitigation:" with nothing after colon
        if re.match(r"^-\s+Risk\s+\d+\s+->\s+mitigation:\s*$", stripped):
            violations.append(
                f"{PREFIX} {file_name}:{i}: risk mitigation placeholder — "
                f"add mitigation content after `-> mitigation:`: {stripped}"
            )

    return violations


def _check_hardening_review(content: str, file_name: str) -> list[str]:
    """Check hardening_review.md for empty required sections and scaffold placeholders."""
    violations: list[str] = []
    lines = content.splitlines()

    in_findings = False
    in_observability = False
    in_architecture = False
    in_proposals = False

    findings_has_content = False
    proposals_has_content = False
    proposals_has_none_or_na = False
    has_empty_proposal = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Section detection
        if stripped.startswith("## "):
            in_findings = "Repository-Wide Findings Fixed" in stripped
            in_observability = "Observability and Diagnostics Changes" in stripped
            in_architecture = "Architecture and Code Quality Compliance" in stripped
            in_proposals = "Proposals Only" in stripped
            continue

        if in_findings:
            if re.match(r"^-\s+Finding\b", stripped):
                colon_pos = stripped.find(":")
                if colon_pos != -1 and not stripped[colon_pos + 1:].strip():
                    violations.append(
                        f"{PREFIX} {file_name}:{i}: scaffold finding placeholder — "
                        f"add finding description after the colon: {stripped}"
                    )
                elif colon_pos != -1 and stripped[colon_pos + 1:].strip():
                    findings_has_content = True

        if in_observability:
            for field in _HARDENING_OBSERVABILITY_FIELDS:
                if stripped == f"- {field}":
                    violations.append(
                        f"{PREFIX} {file_name}:{i}: `{field}` must have non-empty content after the colon"
                    )
                    break

        if in_architecture:
            for field in _HARDENING_ARCHITECTURE_FIELDS:
                if stripped == f"- {field}":
                    violations.append(
                        f"{PREFIX} {file_name}:{i}: `{field}` must have non-empty content after the colon"
                    )
                    break

        if in_proposals:
            if re.match(r"^-\s+Proposal\b", stripped):
                colon_pos = stripped.find(":")
                if colon_pos != -1 and not stripped[colon_pos + 1:].strip():
                    has_empty_proposal = True
                elif colon_pos != -1 and stripped[colon_pos + 1:].strip():
                    proposals_has_content = True
            if re.match(r"^-\s+(none|n/a)$", stripped, re.IGNORECASE):
                proposals_has_none_or_na = True

    if not findings_has_content:
        violations.append(
            f"{PREFIX} {file_name}: `Repository-Wide Findings Fixed` section must contain "
            "at least one non-empty finding entry"
        )

    if has_empty_proposal and not proposals_has_content and not proposals_has_none_or_na:
        violations.append(
            f"{PREFIX} {file_name}: `Proposals Only` section contains scaffold placeholder "
            "`Proposal 1:` — add proposal content, or write `- none` if there are no proposals"
        )

    return violations


def _check_pr_context(content: str, file_name: str) -> list[str]:
    """Check pr_context.md for empty required fields and scaffold placeholders."""
    violations: list[str] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Required inline fields: "- FieldName:" with nothing after the colon
        for field in _PR_CONTEXT_INLINE_FIELDS:
            if stripped == f"- {field}":
                violations.append(
                    f"{PREFIX} {file_name}:{i}: `{field}` must have non-empty content after the colon"
                )
                break

        # Scaffold deferred proposal placeholder: "- Proposal N (not implemented):" with nothing after colon
        if re.match(r"^-\s+Proposal\s+\d+\s+\(not implemented\):\s*$", stripped):
            violations.append(
                f"{PREFIX} {file_name}:{i}: scaffold deferred proposal placeholder — "
                f"add proposal content or remove the line if there are no deferred proposals: {stripped}"
            )

    # Check "Primary files to review first:" has at least one sub-bullet
    in_primary = False
    has_sub_bullet = False
    primary_field_present = False

    for line in lines:
        stripped = line.strip()
        if stripped == "- Primary files to review first:":
            in_primary = True
            primary_field_present = True
            continue
        if in_primary:
            # Stop at next top-level bullet or section heading
            if stripped.startswith("## ") or (
                stripped.startswith("- ") and not line[0:1].isspace()
            ):
                break
            # Sub-bullet: indented line starting with "- " and has content beyond the dash
            if line[0:1].isspace() and stripped.startswith("- ") and len(stripped) > 2:
                has_sub_bullet = True
                break

    if primary_field_present and not has_sub_bullet:
        violations.append(
            f"{PREFIX} {file_name}: `Primary files to review first:` section must contain "
            "at least one non-empty bullet item"
        )

    return violations


def main(repo_root: Path | None = None) -> int:
    if repo_root is None:
        repo_root = REPO_ROOT
    spec_dir = _resolve_spec_dir(repo_root)

    if not spec_dir.is_dir():
        print(
            f"{PREFIX} spec directory not found: {spec_dir}; "
            "create it with `make spec-scaffold SPEC_SLUG=<slug>` or set SPEC_SLUG env var",
            file=sys.stderr,
        )
        return 1

    all_violations: list[str] = []

    for file_name, check_fn in (
        ("tasks.md", _check_tasks),
        ("plan.md", _check_plan),
        ("hardening_review.md", _check_hardening_review),
        ("pr_context.md", _check_pr_context),
    ):
        path = spec_dir / file_name
        if not path.is_file():
            all_violations.append(f"{PREFIX} {file_name}: file not found in spec directory {spec_dir.name}")
            continue
        content = path.read_text(encoding="utf-8", errors="surrogateescape")
        all_violations.extend(check_fn(content, file_name))

    for v in all_violations:
        print(v)

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
