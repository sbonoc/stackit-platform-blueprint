# Work Item Context Pack

## Context Snapshot
- Work item: issue-189 — prune-glob enforcement in upgrade validate and postcheck
- Track: blueprint
- SPEC_READY: false
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-189-prune-glob-enforcement.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-011, SDD-C-014

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `python3 -m pytest tests/blueprint/test_upgrade_consumer_validate.py -v -k prune_glob`
- `python3 -m pytest tests/blueprint/ -v`
- `make quality-hooks-fast`
- `make quality-docs-check-changed`

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
- `docs/blueprint/architecture/decisions/ADR-issue-189-prune-glob-enforcement.md`
