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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260417-blueprint-consumer-template-boundaries.md
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
- Business outcome: generated-consumer repositories receive only consumer-relevant scaffolded assets while blueprint-maintainer history remains in the source blueprint repository.
- Success metric: initial `make blueprint-init-repo` transitions remove source-only SDD/ADR artifacts, docs template sync excludes source-only blueprint docs, and contract tests validate both behaviors.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001: consumer-init contract MUST declare `source_artifact_prune_globs_on_init` with deterministic patterns for blueprint-source-only artifacts.
- FR-002: init-repo runtime MUST remove paths matched by `source_artifact_prune_globs_on_init` ONLY when `repository.repo_mode == consumer_init.mode_from`.
- FR-003: blueprint docs template sync MUST mirror ONLY an explicit consumer-facing allowlist and MUST remove non-allowlisted files from `scripts/templates/blueprint/bootstrap/docs/blueprint/**`.

### Non-Functional Requirements (Normative)
- NFR-SEC-001: prune behavior MUST stay constrained to contract-declared glob patterns and MUST NOT introduce non-contract deletion paths.
- NFR-OBS-001: init/doc-sync flows MUST emit deterministic diagnostics through existing summary/check command output.
- NFR-REL-001: re-runs in `generated-consumer` mode MUST NOT prune consumer-owned SDD work-item folders or blueprint ADR records.
- NFR-OPS-001: governance docs and tests MUST record and enforce source-only ownership boundaries through contract-validation lanes.

## Normative Option Decision
- Option A: contract-driven initial prune globs plus explicit docs-sync allowlist.
- Option B: full `docs/blueprint/**` mirror and no source-artifact prune contract.
- Selected option: OPTION_A
- Rationale: Option A preserves blueprint-maintainer history in source mode and keeps generated-consumer scaffold scope minimal.

## Contract Changes (Normative)
- Config/Env contract: `spec.repository.consumer_init.source_artifact_prune_globs_on_init` is added to source and bootstrap contract files.
- API contract: no change.
- Event contract: no change.
- Make/CLI contract: existing targets remain; behavior change is exercised through existing init and quality commands.
- Docs contract: blueprint docs template mirror uses an explicit allowlist for consumer-facing blueprint docs.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001: when prune helper runs with `repo_mode=template-source`, matching paths under `specs/<YYYY-MM-DD>-*` and `docs/blueprint/architecture/decisions/ADR-*.md` are removed.
- AC-002: when prune helper runs with `repo_mode=generated-consumer`, matching source-artifact paths remain unchanged.
- AC-003: blueprint docs sync keeps every allowlisted path in template mirror in byte-for-byte sync and removes non-allowlisted source-only blueprint docs from the template mirror.

## Informative Notes (Non-Normative)
- Context: this work item packages PR2 for template-boundary separation between blueprint-maintainer history and generated-consumer scaffolding.
- Tradeoffs: docs allowlist maintenance is explicit overhead exchanged for lower consumer template noise.
- Clarifications:
  - User approved continuation of PR2 work in single-author mode via chat on 2026-04-17.

## Explicit Exclusions
- Excluded item 1: no changes to consumer-owned `docs/platform/**` seed/edit behavior.
- Excluded item 2: no changes to runtime module provisioning or app runtime contracts.
