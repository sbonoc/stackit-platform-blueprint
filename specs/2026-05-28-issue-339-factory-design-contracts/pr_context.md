# PR Context

## Summary
- Work item: 2026-05-28-issue-339-factory-design-contracts
- Objective: pin the cross-ticket interface conventions (C1–C7) that Phase 1 factory tickets (#333, #334, #335, #336) and Phase 0 sibling #337 depend on, AND enumerate the consumer-shipped surface (C8) the blueprint publishes so each consumer repo can instantiate its own per-consumer factory. One signed-off document plus one summary ADR. C1–C4 are identical conventions; C5–C7 are parameterized (identical rule + blueprint instance + consumer overlay schema); C8 enumerates docs/ADRs, Terraform/Helm module wrappers, Make targets + skill runbooks, and GitHub App / Actions workflows (LiteLLM is external; consumers configure access). C8 additionally carries an orthogonal extensibility-tier dimension (sealed/parameterized/extensible, default extensible, sealed list pinned to a compliance subset), a namespaced consumer-extension discovery convention, semver-style factory contract versioning, and an `upstream-candidate: true` front-matter convention for consumer extensions.
- Scope boundaries: produces `docs/blueprint/autonomous-factory/design-contracts.md` and `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`. Excludes implementation of any contract (owned by the dependent tickets) and concrete per-consumer values for C5/C6/C7 overlays (owned by each consumer repo's onboarding).

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-020; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002; AC-001 through AC-012.
- Acceptance criteria covered: AC-001 (C1–C8 populated, no stray TBD), AC-002 (Referenced by lines cover downstream set), AC-003 (four sign-offs recorded), AC-004 (open decisions name deferring ticket + deadline), AC-005 (ADR exists + linked), AC-006 (`make quality-sdd-check` passes), AC-007 (`make docs-build` + `make docs-smoke` pass), AC-008 (C5/C6/C7 carry the three required subsections; consumer overlay is schema-only), AC-009 (C8 enumerates four surface categories, LiteLLM external, every surface item tier-tagged), AC-010 (every C8 surface item carries extensibility tier; sealed list matches FR-017(b) exactly; default = extensible), AC-011 (discovery convention documented with one worked example per artifact kind), AC-012 (semver posture and upstream-candidate convention documented; Referenced by cites new Phase 1 ticket).
- Contract surfaces changed: Docs contract — new files under `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/`; both directories are part of the C8-enumerated consumer-shipped surface. Event contract — Contract C7 introduces the lifecycle event schema definition (consumers ship emission separately, replicated per consumer instance via C8-inherited module wrappers). Config/Env contract — `### Consumer overlay` schemas under C5/C6/C7 plus the LiteLLM access configuration shape under C8 define where consumer repos declare per-instance values in their own `contract.yaml`. Make/CLI contract — Contract C8 enumerates the consumer-inheritable Make targets and skill runbooks (enumeration only; implementations owned by #334/#335/#336).

## Key Reviewer Files
- Primary files to review first:
  - `docs/blueprint/autonomous-factory/design-contracts.md` (the deliverable — sections C1–C8)
  - `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` (the summary ADR)
  - `specs/2026-05-28-issue-339-factory-design-contracts/spec.md` (the governing spec)
- High-risk files:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C5 (factory bot identity + SoD detection — security-relevant; exact-string equality rule per NFR-SEC-001; `### Consumer overlay` schema is the per-tenant boundary)
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (event schema — pinning emitter behavior across every factory instance per NFR-OBS-001)
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 (consumer-shipped surface — pins what the blueprint exposes to consumers; stability tiers determine breaking-change discipline; LiteLLM external configuration shape touches secret-handling via ESO)

## Validation Evidence
- Required commands executed: (to be filled at Step 7) `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`.
- Result summary: (to be filled at Step 7)
- Artifact references: `specs/2026-05-28-issue-339-factory-design-contracts/traceability.md`, `specs/2026-05-28-issue-339-factory-design-contracts/evidence_manifest.json`.

## Risk and Rollback
- Main risks:
  - Open Decisions backlog (Q-1, Q-2, Q-3 for blueprint-instance values; Q-4 for LiteLLM `contract.yaml` location; Q-5 for the new Phase 1 factory-upgrade-process ticket number) creates a tail of follow-up edits during #334 / #337 / deliverable authoring / new-ticket filing; mitigated by `### Open Decisions` subsections and per-section `Referenced by:` lines. Q-4 and Q-5 are enforced as pre-SPEC_READY gates.
  - First SDD application on factory governance sets the bar that #333–#337 inherit; mitigated by choosing full SDD ceremony (not the chore bypass track).
  - Per-tenant value bleed risk: a consumer repo might inadvertently inherit the blueprint's literal C5/C6/C7 values; mitigated by FR-016 (consumer overlay subsections specify schema only, never concrete values) and AC-008 enforcement.
  - C8 surface stability: breaking changes to `stable`-tagged module wrappers, Make targets, skill runbooks, or App manifest cascade across all consumer repos; mitigated by FR-015 stability tier + FR-019 semver posture; supported-major window owned by the new Phase 1 factory-upgrade-process ticket.
  - Audit-consistency erosion: FR-017 defaults the C8 surface to `extensible` so consumers may shadow blueprint personas/skills/steps. Cross-consumer review-output uniformity is not a goal; audit consistency is scoped only to the FR-017(b) sealed list (bot-identity rule, sign-off phrases, multi-author SoD, sovereignty/ZDR, reject-rerun cap, C7 minimum event fields). Sealed-shadow rejection rule (FR-018) prevents accidental compliance erosion.
- Rollback strategy: revert the PR. No runtime side effects; no migrations to undo. Phase 1 tickets that begin work after this PR merges treat a rollback as "design contracts not yet decided" and pause dependent work. Consumer repos that have already inherited Contract C8 surface pause new factory-onboarding work until restored.

## Deferred Proposals
- (none at intake — to be re-evaluated at Step 6 document-sync and Step 7 hardening review)
