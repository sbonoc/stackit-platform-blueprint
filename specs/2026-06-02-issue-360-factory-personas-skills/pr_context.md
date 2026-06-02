# PR Context

## Summary
- Work item: 2026-06-02-issue-360-factory-personas-skills (Child A of #333)
- Objective: Author the 10 AI persona files (6 implementer + 4 reviewer) and the 10 new SDD/factory skill `SKILL.md` runbooks that power the autonomous software factory's SDD execution, plus enumerate the 20 new paths under Contract C8 § Category (c) and add the persona-roster ADR.
- Scope boundaries: governance-doc and skill-runbook authoring only. No runtime code, no orchestrator service, no OpenHands client, no RabbitMQ/C7 emission machinery (all owned by Child B `#361`).

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-013
- Contract surfaces changed: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) gains 20 new rows (10 personas + 10 skills) with stability tier `stable` and extensibility tier `extensible`. No change to C7 schema, C3 convention, or C8 sealed list.

## Key Reviewer Files
- Primary files to review first:
  - `specs/2026-06-02-issue-360-factory-personas-skills/spec.md` — full requirement set
  - `docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md` — persona roster decision
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) — 20 new enumeration rows
- High-risk files: the 4 reviewer persona files (`.agents/personas/security-reviewer.md`, `.agents/personas/architecture-reviewer.md`, `.agents/personas/contract-reviewer.md`, `.agents/personas/test-coverage-reviewer.md`) — non-overlapping `## Review Dimensions` (FR-013) is brittle to wording drift; the architecture-reviewer's `## Cross-Context Impact Reporting` template (FR-014) drops directly into the PR body for the human merge gate.

## Validation Evidence
- Required commands executed: pending — to be filled at implementation time (T-201)
- Result summary: pending
- Artifact references:
  - traceability matrix: `specs/2026-06-02-issue-360-factory-personas-skills/traceability.md`
  - hardening review: `specs/2026-06-02-issue-360-factory-personas-skills/hardening_review.md`

## Risk and Rollback
- Main risks:
  - persona content drifts from FR phrases over time → grep-based tests anchored on exact phrases (T-104, T-105, T-106) catch this in PR diff
  - Child B's jsonschema validator needs additional fields beyond what the schemas declare today → OQ-2 leaves the door open for a uniform retrofit pass when Child B lands
- Rollback strategy: pure content commit; `git revert <commit>` is sufficient. No data migration, no schema change, no consumer-instance state.

## Deferred Proposals
- Proposal 1 (not implemented): Add a slash-command row for `blueprint-sdd-step08-agent-pr-review` to `CLAUDE.md`'s Skills table. Reason for deferral: step08 is orchestrator-invoked on PR open (Child B), not human-invoked; no slash-command access is required until Child B is operational and human invocation paths are defined. Trigger: Child B (`#361`) merges.
- Proposal 2 (not implemented): Retroactively add `## Required Output Schema` sections to the existing 7 SDD step skills (`step01`–`step07`) + `blueprint-sdd-traceability-keeper`. Reason for deferral: the orchestrator-side validator (Child B) is not yet implemented; adding schemas today produces unused content. Trigger: Child B (`#361`) merges; retrofit in one uniform pass at that time.
