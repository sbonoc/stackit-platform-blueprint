# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-27-issue-214-215-source-only-glob-and-validate
- Track: blueprint
- SPEC_READY: false
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-214-215-source-only-glob-and-validate.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024

## Summary
Fix two complementary v1.8.0 bugs in source_only contract enforcement, both discovered by dhe-marketplace during their v1.8.0 upgrade:
- #214: audit_source_tree_coverage does not count prune-glob-matched files as covered → false uncovered_source_files_count errors block upgrade-plan
- #215: _validate_absent_files uses exists() not is_file() → directory entries in source_only trigger false absent-file errors, blocking the natural workaround for #214

Both bugs are fixed in one PR: extend audit coverage with prune-glob matches; add is_file() and glob support to the validator.

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`
- `make blueprint-template-smoke`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
- `docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-214-215-source-only-glob-and-validate.md`

## Key Implementation Files
- `scripts/lib/blueprint/upgrade_consumer.py` — `audit_source_tree_coverage` (FR-001)
- `scripts/bin/blueprint/validate_contract.py` — `_validate_absent_files` (FR-002, FR-003)
- `tests/` — regression test fixtures (FR-004)
