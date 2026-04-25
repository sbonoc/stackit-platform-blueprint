# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-25-scripted-upgrade-pipeline
- Track: blueprint
- SPEC_READY: false (open questions Q-1 and Q-2 pending)
- ADR path: docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md
- ADR status: proposed

## Summary
Phase 4 of the consumer upgrade flow improvement programme. Replaces the `blueprint-consumer-upgrade` skill's ~30 open-interpretation runbook steps with a single deterministic make target (`make blueprint-upgrade-consumer`). The pipeline chains 10 scripted stages — pre-flight, apply-with-delete, contract resolution, coverage-gap-fetch, mirror-sync, doc-target-check, docs-regen, gate-chain, residual report — and produces a structured Markdown report covering only items that genuinely require human decision.

The root motivation is 10 observed failure modes (F-001–F-010) from a real v1.0.0→v1.6.0 upgrade of a consumer repo (sbonoc/dhe-marketplace#40). Each failure mode required unguided agent judgment that must instead be scripted and verified by automated tests.

## Key Design Decisions
- Contract resolver (`resolve_contract_upgrade.py`) — deterministic merge rules for `blueprint/contract.yaml` conflicts: preserve consumer identity fields, merge `required_files` additively, drop prune globs that match existing consumer paths. Addresses F-001, F-007, F-008.
- Coverage gap detection + local-git file fetch — no HTTP fetches; uses already-cloned source repo. Addresses F-002.
- Stage 10 residual report always emitted — even on partial pipeline failure. Addresses F-010.
- ALLOW_DELETE default (Q-2 open) — agent recommends delete ON by default for deterministic outcomes; non-destructive mode available via override.
- Stage 5 fetch scope (Q-1 open) — agent recommends narrow scope (plan-covered action=create files only); the #185 planner audit already blocks plan production for uncovered source files.

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-018

## Open Questions (2)
- Q-1: Stage 5 fetch scope — narrow (plan-covered action=create only) vs. broad (all contract-referenced absent files). Agent recommendation: Option A (narrow).
- Q-2: BLUEPRINT_UPGRADE_ALLOW_DELETE default for the pipeline entry point — delete ON by default vs. delete OFF by default. Agent recommendation: Option A (delete ON).

## Key Files for Reviewers
- `specs/2026-04-25-scripted-upgrade-pipeline/spec.md` — normative requirements (FR-001–019, NFR-SEC/REL/OPS/OBS-001, AC-001–006)
- `specs/2026-04-25-scripted-upgrade-pipeline/architecture.md` — bounded context design and pipeline flowchart
- `specs/2026-04-25-scripted-upgrade-pipeline/plan.md` — 8 delivery slices in red→green TDD order
- `docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md` — architectural decision record

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

## Phase Programme Context
- Phase 1 (Foundation): Issues #160, #166, #169 — done
- Phase 2 (Correctness gates): Issues #162, #163 — done
- Phase 2 (Bug-fix layer): Issues #179, #180, #181, #182, #185, #186, #187 — done
- Phase 3 (Reporting): Issue #165 — done
- **Phase 4 (this work item)**: single-command UX built on stable correctness foundation
- Pending Phase 2 item: Issue #189 (prune glob enforcement in planner/validate/postcheck) — complementary but not a blocker for this work item
