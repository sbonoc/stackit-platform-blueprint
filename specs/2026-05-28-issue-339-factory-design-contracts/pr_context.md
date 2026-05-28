# PR Context

## Summary
- Work item: 2026-05-28-issue-339-factory-design-contracts
- Objective: pin the seven cross-ticket interface conventions (C1–C7) that Phase 1 factory tickets (#333, #334, #335, #336) and Phase 0 sibling #337 all depend on, in one signed-off document plus one summary ADR, so Phase 1 ships with consistent interfaces.
- Scope boundaries: produces `docs/blueprint/autonomous-factory/design-contracts.md` and `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`. Excludes implementation of any contract (owned by the dependent tickets).

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-012; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001; AC-001 through AC-007.
- Acceptance criteria covered: AC-001 (sections populated, no stray TBD), AC-002 (Referenced by lines cover downstream set), AC-003 (four sign-offs recorded), AC-004 (open decisions name deferring ticket + deadline), AC-005 (ADR exists + linked), AC-006 (`make quality-sdd-check` passes), AC-007 (`make docs-build` + `make docs-smoke` pass).
- Contract surfaces changed: Docs contract — new files under `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/`. Event contract — Contract C7 introduces the lifecycle event schema definition (consumers ship emission separately).

## Key Reviewer Files
- Primary files to review first:
  - `docs/blueprint/autonomous-factory/design-contracts.md` (the deliverable — sections C1–C7)
  - `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` (the summary ADR)
  - `specs/2026-05-28-issue-339-factory-design-contracts/spec.md` (the governing spec)
- High-risk files:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C5 (factory bot identity + SoD detection — security-relevant; exact-string equality rule per NFR-SEC-001)
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (event schema — pinning downstream emitter behavior per NFR-OBS-001)

## Validation Evidence
- Required commands executed: (to be filled at Step 7) `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`.
- Result summary: (to be filled at Step 7)
- Artifact references: `specs/2026-05-28-issue-339-factory-design-contracts/traceability.md`, `specs/2026-05-28-issue-339-factory-design-contracts/evidence_manifest.json`.

## Risk and Rollback
- Main risks:
  - Open Decisions backlog (Q-1, Q-2, Q-3) creates a tail of follow-up edits during #334 and #337; mitigated by `### Open Decisions` subsections and per-section `Referenced by:` lines.
  - First SDD application on factory governance sets the bar that #333–#337 inherit; mitigated by choosing full SDD ceremony (not the chore bypass track).
- Rollback strategy: revert the PR. No runtime side effects; no migrations to undo. Phase 1 tickets that begin work after this PR merges treat a rollback as "design contracts not yet decided" and pause dependent work.

## Deferred Proposals
- (none at intake — to be re-evaluated at Step 6 document-sync and Step 7 hardening review)
