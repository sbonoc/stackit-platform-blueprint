# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md` — done 2026-05-06
- [x] G-002 Confirm open questions and unresolved alternatives are `0` — done 2026-05-06 (Q-1: Option A; Q-2: Option A)
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations) — all approved 2026-05-06
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs — SDD-C-001..SDD-C-021 listed
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated — confirmed
- [x] G-006 Confirm Q-1 (make target naming axis) resolved and commented on issue #248 — Option A, comment posted
- [x] G-007 Confirm Q-2 (admin credential level for `stackit_opensearch_credential`) resolved — Option A; stop condition applies if assumption fails

## Implementation

### Slice 1 — STACKIT Terraform module
- [ ] T-001 Write failing test `test_terraform_module_has_opensearch_resources` (asserts resource blocks in `main.tf`)
- [ ] T-002 Implement `infra/cloud/stackit/terraform/modules/opensearch/main.tf` with `stackit_opensearch_instance` + `lifecycle { create_before_destroy = true }` and `stackit_opensearch_credential`
- [ ] T-003 Implement `infra/cloud/stackit/terraform/modules/opensearch/variables.tf` binding contract inputs
- [ ] T-004 Implement `infra/cloud/stackit/terraform/modules/opensearch/outputs.tf` exposing all 8 contract outputs
- [ ] T-005 Implement `infra/cloud/stackit/terraform/modules/opensearch/versions.tf` with required provider version constraint
- [ ] T-006 Run `make test-unit-all` — green

### Slice 2 — versions.sh pins
- [ ] T-011 Write failing test `test_opensearch_version_pins_declared`
- [ ] T-012 Add `OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_REGISTRY`, `OPENSEARCH_LOCAL_IMAGE_REPOSITORY`, `OPENSEARCH_LOCAL_IMAGE_TAG` to `scripts/lib/infra/versions.sh`
- [ ] T-013 Run `make test-unit-all` — green

### Slice 3 — opensearch.sh local lane functions
- [ ] T-021 Write failing tests for local host/port/scheme resolution functions
- [ ] T-022 Update `opensearch_init_env()` to set local Helm defaults
- [ ] T-023 Add `opensearch_local_service_host()`, `opensearch_local_port()`, `opensearch_local_scheme()` functions
- [ ] T-024 Update `opensearch_host()`, `opensearch_port()`, `opensearch_scheme()`, `opensearch_uri()`, `opensearch_username()`, `opensearch_password()` to branch on `is_local_profile`
- [ ] T-025 Add `opensearch_render_values_file()` function
- [ ] T-026 Source `scripts/lib/infra/versions.sh` and `scripts/lib/infra/fallback_runtime.sh` in opensearch.sh
- [ ] T-027 Run `make test-unit-all` — green

### Slice 4 — Local Helm chart
- [ ] T-031 Write failing test `test_opensearch_local_helm_values_file_exists_and_parses`
- [ ] T-032 Add `infra/local/helm/opensearch/values.yaml` (fullnameOverride: blueprint-opensearch, dev-sized resources ≤1 GB RAM, persistence disabled, admin credentials)
- [ ] T-033 Run `make test-unit-all` — green

### Slice 5 — module_execution.sh routing
- [ ] T-041 Write failing test `test_opensearch_local_profile_routes_to_helm_driver`
- [ ] T-042 Update `resolve_optional_module_execution "opensearch"` cases in `module_execution.sh` to use `helm` driver for local profile
- [ ] T-043 Run `make test-unit-all` — green

### Slice 6 — opensearch_apply.sh update
- [ ] T-051 Write failing test `test_opensearch_apply_local_calls_helm_upgrade`
- [ ] T-052 Add `helm` case to `scripts/bin/infra/opensearch_apply.sh`; source versions.sh and fallback_runtime.sh
- [ ] T-053 Run `make test-unit-all` — green

### Slice 7 — opensearch_smoke.sh implementation
- [ ] T-061 Write failing tests `test_opensearch_smoke_fails_when_uri_empty` and `test_opensearch_smoke_passes_with_valid_uri`
- [ ] T-062 Implement `scripts/bin/infra/opensearch_smoke.sh`: read `opensearch_runtime` state, assert uri and dashboard_url non-empty
- [ ] T-063 Run `make test-unit-all` — green

### Slice 8 — Contract tests
- [ ] T-071 Write failing test `test_opensearch_runtime_state_has_all_contract_outputs` in `tests/infra/modules/opensearch/test_contract.py`
- [ ] T-072 Wire test to mock state fixture or real state file from local apply
- [ ] T-073 Run `make test-unit-all` — green

### Slice 9 — Documentation
- [ ] T-081 Update `docs/platform/modules/opensearch/README.md` with dual-lane usage examples, env-var reference table, prerequisite notes, and rollback instructions
- [ ] T-082 Run `make quality-docs-check-changed` — green

### Slice 10 — Pre-PR quality sweep
- [ ] T-091 Run `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` — fix all violations
- [ ] T-092 Run `make infra-validate` — green
- [ ] T-093 Run `make quality-sdd-check` — green

## Test Automation
- [ ] T-101 Unit tests added for local lane resolution functions (Slices 3, 4, 5, 6, 7)
- [ ] T-102 Contract test added for state file output key presence (Slice 8)
- [ ] T-103 No filter/payload-transform routes in scope — N/A
- [ ] T-104 Translate any reproducible pre-PR smoke findings to failing tests before fix
- [ ] T-105 No new boundary/integration tests required beyond the contract test

## Accessibility Testing (Normative)
- [ ] T-A01 N/A — infrastructure-only work item; no UI components (declared in NFR-A11Y-001)

## Validation and Release Readiness
- [ ] T-201 Run `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` and `make infra-validate` — both green
- [ ] T-202 Attach evidence to `traceability.md` and `pr_context.md`
- [ ] T-203 Confirm no stale TODOs, dead code, or drift in touched scope
- [ ] T-204 Run `make quality-docs-check-changed` and `make quality-docs-check-module-contract-summaries-sync`
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings; cite issue #248; list satisfied cross-cutting requirements; link per-module integration contract section; list verification evidence
- [ ] P-004 Post comment on issue #248 with PR link after Draft PR is opened
- [ ] P-005 Post comment on issue #248 explaining naming convention deviation (Q-1 resolution)

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [ ] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [ ] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [ ] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [ ] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [ ] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
