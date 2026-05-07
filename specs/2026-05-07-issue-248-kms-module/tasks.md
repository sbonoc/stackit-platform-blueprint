# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation (ordered by slice)

### Slice 1 — Tests RED
- [x] T-001 Write `tests/infra/modules/kms/test_kms_module.py` with all unit assertions RED (AC-001–AC-003, AC-005–AC-014 excluding AC-004, AC-011)
- [x] T-002 Write `tests/infra/modules/kms/test_contract.py` with contract assertions RED (AC-004, AC-011)
- [x] T-003 Confirm `pytest tests/infra/modules/kms/ -v` is all RED

### Slice 2 — STACKIT Terraform Module
- [x] T-004 Implement `infra/cloud/stackit/terraform/modules/kms/main.tf` (complete with `stackit_kms_keyring` + `lifecycle { create_before_destroy = true }` + `stackit_kms_key`)
- [x] T-005 Implement `infra/cloud/stackit/terraform/modules/kms/variables.tf` (all contract inputs)
- [x] T-006 Implement `infra/cloud/stackit/terraform/modules/kms/outputs.tf` (`kms_keyring_id`, `kms_keyring_display_name`, `kms_key_id`, `kms_key_display_name`)
- [x] T-007 Implement `infra/cloud/stackit/terraform/modules/kms/versions.tf` (provider version pin matching foundation)

### Slice 3 — Contract + Shell Layer + Local Helm Chart
- [x] T-008 Update `blueprint/modules/kms/module.contract.yaml`: add `KMS_ENDPOINT` to `outputs.produced`
- [x] T-009 Create `infra/local/helm/kms/values.yaml` (Vault dev mode: `fullnameOverride: "blueprint-vault"`, `server.dev.enabled: true`, resource limits ≤ 512 Mi)
- [x] T-010 Update `scripts/lib/infra/module_execution.sh`: change kms local-profile driver from `noop` to `helm` for plan/apply/destroy
- [x] T-011 Add `kms_endpoint()`, `kms_render_values_file()`, `kms_reconcile_runtime_secret()`, `kms_enable_vault_transit()` to `scripts/lib/infra/kms.sh`
- [x] T-012 Update `scripts/bin/infra/kms_apply.sh`: add `helm` case + `endpoint=$(kms_endpoint)` to `write_state_file`
- [x] T-013 Update `scripts/bin/infra/kms_plan.sh`: add `helm` case that writes plan state on local profile
- [x] T-014 Update `scripts/bin/infra/kms_destroy.sh`: add `helm` case calling `run_helm_uninstall`
- [x] T-015 Harden `scripts/bin/infra/kms_smoke.sh`: add `key_ring_id`, `key_id`, `endpoint` non-empty checks; add `endpoint` to smoke state write

### Slice 4 — Docs
- [x] T-016 Write `docs/platform/modules/kms/README.md` (both-lanes usage, Vault Transit section, STACKIT KMS section, endpoint reference, destroy semantics, env-var reference table)

## Test Automation
- [x] T-101 Tests in `test_kms_module.py`: Terraform module structure (AC-001, AC-002, AC-003); `kms_endpoint()` local lane (AC-005); apply state file `endpoint` key (AC-006); smoke pass/fail scenarios (AC-007, AC-008, AC-009, AC-010); Helm values assertions (AC-012); plan state artifact (AC-013); module_execution.sh helm driver (AC-014)
- [x] T-102 Tests in `test_contract.py`: `module.contract.yaml` outputs includes `KMS_ENDPOINT` (AC-004); runtime state has all five keys (AC-011)
- [x] T-103 Not applicable — no filter/payload-transform logic in scope
- [x] T-104 Not applicable — no reproducible pre-PR findings to translate
- [x] T-105 Confirm total assertion count ≥ 18 across both test files — 23 assertions

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 N/A — NFR-A11Y-001 declared in spec.md: no UI component; kms is an infrastructure module with no browser-facing surface
- [x] T-A02 N/A — no UI surface
- [x] T-A03 N/A — no UI surface
- [x] T-A04 N/A — no UI surface
- [x] T-A05 N/A — no UI surface

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
