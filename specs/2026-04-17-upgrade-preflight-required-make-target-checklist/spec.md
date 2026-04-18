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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260417-upgrade-preflight-required-make-target-checklist.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-014, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
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
- Business outcome: convert missing consumer-owned required Make targets from a late validate failure into an explicit preflight checklist with deterministic remediation guidance.
- Success metric: upgrade preflight reports contract-required consumer Make target gaps before apply/validate, with exact target identifiers and expected definition surfaces.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001: Upgrade planning MUST emit a required manual action for every source-defined consumer-owned Make target that is listed in `spec.make_contract.required_targets` and missing from target consumer-owned Make surfaces.
- FR-002: Missing-target manual actions MUST be emitted even when no known blueprint invoker path references the target yet.
- FR-003: Each missing-target manual action reason MUST include both the exact target name and deterministic expected definition surfaces (`make/platform.mk` or linked includes under `make/platform/*.mk`).
- FR-004: If a known invoker reference path exists, manual action `dependency_of` MUST point to that invoker; otherwise it MUST fall back to `blueprint/contract.yaml: spec.make_contract.required_targets -> <target>`.
- FR-005: Existing placeholder/manual-action checks for `apps-ci-bootstrap-consumer` and `infra-post-deploy-consumer` MUST remain active and include deterministic target-location guidance.

### Non-Functional Requirements (Normative)
- NFR-SEC-001: The feature MUST remain contract/read-only for detection logic and MUST NOT introduce new privileged operations or secret reads beyond existing upgrade planning behavior.
- NFR-OBS-001: Manual action messages MUST remain structured and deterministic so `upgrade_preflight.json` and `upgrade_summary.md` stay machine- and operator-readable.
- NFR-REL-001: Existing upgrade manual-action regressions MUST remain green while adding new missing-target coverage.
- NFR-OPS-001: Operator remediation text MUST remain command-compatible with existing follow-up flow (`make blueprint-upgrade-consumer-validate`).

## Normative Option Decision
- Option A: keep missing-target reporting gated by known invoker references only.
- Option B: report all contract-required missing consumer-owned targets from source-defined platform make surfaces, using contract fallback dependency context when no invoker exists.
- Selected option: OPTION_B
- Rationale: Option B satisfies preflight ergonomics by surfacing actionable gaps before late validation failures, including newly introduced required targets.

## Contract Changes (Normative)
- Config/Env contract: no new variables.
- API contract: no external API changes.
- Event contract: no event changes.
- Make/CLI contract: no new targets; enhanced manual-action diagnostics in existing upgrade/preflight flow.
- Docs contract: consumer upgrade docs MUST describe missing required target checklist behavior and expected definition locations.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001: A regression test fails red->green when a source contract introduces a new required consumer-owned Make target defined in source platform make surfaces but missing in the target repo.
- AC-002: The resulting manual action includes the exact target name and expected location guidance (`make/platform.mk` or `make/platform/*.mk`).
- AC-003: `dependency_of` uses invoker-path reference when available and contract-fallback reference when invoker-path reference is unavailable.
- AC-004: Existing CI/bootstrap and local-post-deploy placeholder manual-action behaviors remain green.
- AC-005: Consumer upgrade docs state that preflight includes required-target checklist findings and where to define missing targets.

## Informative Notes (Non-Normative)
- Context: Issue #102 reported that generated-consumer upgrades hit late validation failures due to missing consumer-owned required Make targets.
- Tradeoffs: broader preflight checklist output can include multiple actionable missing targets in legacy consumer makefiles.
- Clarifications:
  - user explicitly requested strict SDD lifecycle execution for this work item.

## Explicit Exclusions
- Excluded item 1: no schema version changes in `blueprint/contract.yaml`.
- Excluded item 2: no changes to upgrade apply merge/conflict resolution behavior.
