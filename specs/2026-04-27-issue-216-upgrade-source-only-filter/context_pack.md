# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-27-issue-216-upgrade-source-only-filter
- Track: blueprint
- SPEC_READY: false
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-216-upgrade-source-only-filter.md
- ADR status: proposed

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024

## Summary
Fix v1.8.0 regression in Stage 3 contract resolver: `resolve_contract_upgrade.py` takes `source_only` wholesale from source, silently overwriting consumer-owned paths (`specs`, `CLAUDE.md`, `docs/src`, etc.) with the upstream 9-entry list. Restores FR-009 `_filter_source_only` logic (Phase 1: drop source entries existing on disk; Phase 2: carry forward consumer additions). Closes issue #216.

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
- `docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-216-upgrade-source-only-filter.md`

## Key Implementation Files
- `scripts/lib/blueprint/resolve_contract_upgrade.py` — `_filter_source_only` (new), `resolve_contract_conflict` (FR-001), `ContractResolveResult` (FR-003)
- `tests/` — regression test fixtures (FR-005)
