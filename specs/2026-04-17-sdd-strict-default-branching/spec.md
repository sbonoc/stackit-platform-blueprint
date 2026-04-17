# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260417-sdd-default-enforcement.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
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
- Business outcome: enforce deterministic SDD execution defaults across assistant workflows and reduce branch/traceability drift during new work-item start.
- Success metric: new work items scaffold with dedicated non-default branches by default and SDD policy checks fail on branch-contract wiring drift.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST enforce Spec-Driven Development as the default assistant execution mode unless the user explicitly opts out for the requested task.
- FR-002 MUST create and check out a dedicated non-default branch when scaffolding a new SDD work item, with explicit override and explicit opt-out support.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST require explicit user/operator intent to bypass branch auto-creation and MUST NOT introduce automatic remote branch mutation.
- NFR-OBS-001 MUST emit deterministic operator-facing diagnostics for scaffold branch decisions and branch-contract validation failures.
- NFR-REL-001 MUST validate contract-to-tooling wiring for branch defaults in quality gates before merge.
- NFR-OPS-001 MUST expose deterministic make/CLI controls for branch override and branch opt-out for runbook usability.

## Normative Option Decision
- Option A: strict default SDD + dedicated branch auto-creation + explicit opt-out controls + enforced quality checks.
- Option B: advisory-only governance text with manual branch discipline.
- Selected option: OPTION_A
- Rationale: OPTION_A preserves deterministic lifecycle behavior and blocks silent drift across assistants and repository templates.

## Contract Changes (Normative)
- Config/Env contract: `spec.spec_driven_development_contract.branch_contract` added in blueprint + bootstrap template contract surfaces.
- API contract: none.
- Event contract: none.
- Make/CLI contract: `spec-scaffold` supports `SPEC_BRANCH=<name>` and `SPEC_NO_BRANCH=true` passthrough.
- Docs contract: governance and interoperability docs now declare strict-default SDD and dedicated-branch startup expectations.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST prove `make spec-scaffold SPEC_SLUG=<slug>` creates/checks out `codex/<YYYY-MM-DD>-<slug>` by default and supports explicit override/opt-out modes.
- AC-002 MUST prove SDD quality checks fail when branch-contract scaffold wiring drifts and pass when contract, tooling, and templates remain synchronized.

## Informative Notes (Non-Normative)
- Context: this work item was executed to harden governance behavior before follow-on upgrade/runtime fixes.
- Tradeoffs: stricter defaults add an explicit step for branch opt-out, but remove ambiguity and rework risk.
- Clarifications: none.

## Explicit Exclusions
- Runtime module bugfix implementation from open issues (`#103`, `#105`, `#106`, `#107`, and related runtime lanes) is excluded from this work item.
