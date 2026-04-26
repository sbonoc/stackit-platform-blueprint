# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-26-issue-198-199-upgrade-coverage-gaps
- Track: blueprint
- SPEC_READY: false (pending Architecture/Security/Operations sign-off)
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-198-199-upgrade-coverage-gaps.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`

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
- `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-198-199-upgrade-coverage-gaps.md`

## Key Implementation Files
- `scripts/lib/blueprint/upgrade_consumer_validate.py` — VALIDATION_TARGETS tuple (line 28)
- `scripts/lib/blueprint/contract_schema.py` — RepositoryOwnershipPathClasses (line 44)
- `scripts/lib/blueprint/upgrade_consumer.py` — audit_source_tree_coverage (line 336), call site (line 1851)
- `scripts/bin/blueprint/validate_contract.py` — conditional_scaffold validation (line 1771)
- `blueprint/contract.yaml` — ownership_path_classes (line 529)
- `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — bootstrap mirror
- `tests/blueprint/test_upgrade_consumer.py` — unit tests for new behavior
