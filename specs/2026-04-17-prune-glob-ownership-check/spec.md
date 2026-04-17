# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260417-prune-glob-ownership-check.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: enforce deterministic contract-to-doc ownership parity for source-artifact prune globs while preserving consumer docs integrity and prune safety guarantees.
- Success metric: `infra-validate` fails when any prune glob is undocumented in source-only ownership rows and passes when contract/doc mapping is complete.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001: `spec.docs_contract.blueprint_docs.template_sync_allowlist` MUST be the single declarative source for blueprint docs template sync scope.
- FR-002: `infra-validate` MUST enforce that every `repository.consumer_init.source_artifact_prune_globs_on_init` pattern is documented in source-only rows in `docs/blueprint/governance/ownership_matrix.md`.
- FR-003: bootstrap template docs mirror MUST include every allowlisted blueprint docs path and MUST prune non-allowlisted template docs.

### Non-Functional Requirements (Normative)
- NFR-SEC-001: prune logic MUST reject unsafe patterns and MUST skip out-of-root resolved candidates and symlink-following deletes.
- NFR-OBS-001: contract validation failures MUST include explicit missing-pattern diagnostics.
- NFR-REL-001: checker behavior MUST be deterministic and independent of external services.
- NFR-OPS-001: governance docs, validators, and tests MUST remain synchronized in the same change.

## Normative Option Decision
- Option A: strict contract-to-ownership-matrix parity check with exact pattern documentation.
- Option B: narrative-only docs guidance with no validation check.
- Selected option: OPTION_A
- Rationale: Option A prevents silent drift and makes ownership governance executable.

## Contract Changes (Normative)
- Config/Env contract: no change.
- API contract: no change.
- Event contract: no change.
- Make/CLI contract: `infra-validate` behavior expands with prune-glob documentation validation.
- Docs contract: ownership matrix source-only row uses exact prune-glob patterns from contract.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001: if ownership matrix source-only rows omit any prune-glob pattern from contract, `infra-validate` returns a deterministic error naming the missing pattern.
- AC-002: if source-only rows document all prune-glob patterns, `infra-validate` passes this check.
- AC-003: docs sync and docs contract tests keep `assistant_compatibility.md` and ownership matrix in template mirror according to contract allowlist.

## Informative Notes (Non-Normative)
- Context: this is the follow-up PR after template-boundary enforcement to close the remaining deferred governance gap.
- Tradeoffs: exact pattern documentation increases maintenance burden but reduces ambiguity.
- Clarifications:
  - user requested proceeding with the next remaining PR item on 2026-04-17.

## Explicit Exclusions
- Excluded item 1: no changes to app runtime or module provisioning logic.
- Excluded item 2: no additional CI lane split/refactor beyond contract validation checks.
