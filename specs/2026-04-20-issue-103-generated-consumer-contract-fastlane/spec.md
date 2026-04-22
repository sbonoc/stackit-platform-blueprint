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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260420-issue-103-generated-consumer-fast-contract-repo-mode-selection.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: single-agent
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: generated-consumer upgrade validation MUST not fail due to template-source-only fast-contract tests while template-source remains strict for canonical lane coverage.
- Success metric: `infra-contract-test-fast` selects deterministic test sets by repo mode and passes generated-consumer scenarios without requiring source-only files.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `scripts/bin/infra/contract_test_fast.sh` MUST select test files by active repo mode resolved from contract runtime helpers.
- FR-002 when `repo_mode=generated-consumer`, the fast lane MUST execute shared infra contract tests and MUST NOT require template-source-only tests.
- FR-003 when `repo_mode=template-source`, the fast lane MUST include template-source-only tests and MUST fail-fast if any selected required test path is missing.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 mode-aware selection MUST NOT introduce new secret/env requirements.
- NFR-OBS-001 fast lane MUST emit deterministic selection metrics/logs containing `repo_mode` and selected/skipped counts.
- NFR-REL-001 selected test order MUST remain deterministic across runs.
- NFR-OPS-001 remediation path MUST be explicit through lane output (`missing required fast contract test path(s)`) and rerun command `make infra-contract-test-fast`.

## Normative Option Decision
- Option A: execute all existing test paths found on disk regardless of repo mode.
- Option B: define explicit repo-mode test sets with strict required-path checks on selected tests.
- Selected option: OPTION_B
- Rationale: explicit mode-aware sets preserve strict source coverage and remove generated-consumer false failures deterministically.

## Contract Changes (Normative)
- Config/Env contract:
  - no new env keys; consumes existing `repo_mode` contract runtime values.
- API contract:
  - none.
- Event contract:
  - none.
- Make/CLI contract:
  - `scripts/bin/infra/contract_test_fast.sh` SHALL select tests by `repo_mode` and SHALL emit `infra_contract_test_fast_test_selection_total` metrics.
- Docs contract:
  - SDD artifact set, backlog, and decision log SHALL capture Issue #103 delivery scope.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/103
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST be objectively testable: template-source mode includes `tests/blueprint/test_upgrade_fixture_matrix.py` and `tests/infra/test_optional_module_required_env_contract.py` in fast-lane selection.
- AC-002 MUST be objectively testable: generated-consumer mode excludes template-source-only tests while keeping shared infra contract tests selected.
- AC-003 MUST be objectively testable: template-source mode fails fast with deterministic diagnostics when a selected required test path is missing.

## Informative Notes (Non-Normative)
- Context: this is the first item in backlog group `P1 Generated-consumer upgrade regressions`.
- Tradeoffs: this scope fixes fast-lane selection only; it does not address additive-file or helper-distribution regressions.
- Clarifications: none.

## Explicit Exclusions
- Issue #104 additive baseline-absent conflict classification.
- Issues #106 and #107 helper distribution coverage in generated-consumer upgrades.
