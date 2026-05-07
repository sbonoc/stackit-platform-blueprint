# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-30-issue-238-239-240-a11y-compliance
- Track: blueprint
- SPEC_READY: false (blocked — Q-1 layer conditionality and Q-2 ACR integration path open)
- ADR path: docs/blueprint/architecture/decisions/ADR-20260430-issue-238-239-240-a11y-compliance.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024

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
