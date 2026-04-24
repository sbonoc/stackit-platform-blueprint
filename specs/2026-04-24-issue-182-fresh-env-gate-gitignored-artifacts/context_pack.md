# Work Item Context Pack

## Context Snapshot
- Work item: issue-182 — upgrade_fresh_env_gate: seed gitignored artifacts into clean worktree
- Track: blueprint
- SPEC_READY: true
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-182-fresh-env-gate-artifact-seeding.md
- ADR status: approved

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-011, SDD-C-014

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `python3 -m pytest tests/blueprint/test_upgrade_fresh_env_gate.py -v`
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
- `docs/blueprint/architecture/decisions/ADR-issue-182-fresh-env-gate-artifact-seeding.md`
