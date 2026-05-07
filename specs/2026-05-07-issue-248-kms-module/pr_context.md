# PR Context

## Summary
- Work item: 2026-05-07-issue-248-kms-module
- Objective: Elevate the `kms` module from a partial scaffold (STACKIT foundation-only, local lane is a silent no-op) to a production-grade optional module with full dual-lane support. Delivers: a complete STACKIT standalone Terraform module (`stackit_kms_keyring` + `stackit_kms_key` with `lifecycle { create_before_destroy = true }`); a first-class local lane via HashiCorp Vault Transit Secrets Engine (Vault Helm chart, dev mode, K8s Secret token delivery); a new `KMS_ENDPOINT` contract output in `module.contract.yaml`; `kms_endpoint()` dual-lane function and four supporting functions in `kms.sh`; hardened smoke validations for `key_ring_id`, `key_id`, and `endpoint`; a full five-key runtime state file; and complete module documentation.
- Scope boundaries: `scripts/lib/infra/kms.sh`, `scripts/bin/infra/kms_{plan,apply,smoke,destroy}.sh`, `scripts/lib/infra/module_execution.sh`, `scripts/lib/infra/versions.sh`, `blueprint/modules/kms/module.contract.yaml`, `infra/cloud/stackit/terraform/modules/kms/`, `infra/local/helm/kms/values.yaml`, `docs/platform/modules/kms/README.md`, `tests/infra/modules/kms/`. No consumer repository changes; no langfuse/neo4j modules; no make target renames.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-014 (all 14)
- Contract surfaces changed: `KMS_ENDPOINT` added to `outputs.produced` in `module.contract.yaml` (total: 5 outputs). Runtime state file (`artifacts/infra/kms_runtime.env`) gains `endpoint` key and renames `key_ring` → `key_ring_name` for consistency; existing consumers reading `key_ring_id` and `key_id` are unaffected (additive + rename of internal key only). Local lane make targets (`infra-kms-plan`, `infra-kms-apply`, `infra-kms-destroy`) are now backed by Vault Helm driver instead of `noop`.

| Requirement | Implementation path | Test evidence |
|---|---|---|
| FR-001 | `infra/cloud/stackit/terraform/modules/kms/main.tf` | `test_kms_module.py::test_terraform_module_declares_keyring_and_key` |
| FR-002 | `blueprint/modules/kms/module.contract.yaml` | `test_contract.py::test_contract_yaml_outputs_include_kms_endpoint` |
| FR-003 | `scripts/lib/infra/kms.sh::kms_endpoint()` | `test_kms_module.py::test_kms_endpoint_local_lane_returns_vault_transit_url` |
| FR-004 | `scripts/lib/infra/kms.sh` (3 functions) | `test_kms_module.py::test_kms_shell_functions_exist` |
| FR-005 | `scripts/bin/infra/kms_apply.sh` | `test_kms_module.py::test_kms_apply_state_file_includes_endpoint_key` |
| FR-006 | `scripts/bin/infra/kms_plan.sh` | `test_kms_module.py::test_kms_plan_helm_case_writes_plan_state` |
| FR-007 | `scripts/bin/infra/kms_destroy.sh` | `test_kms_module.py::test_module_execution_kms_local_destroy_driver_is_helm` |
| FR-008 | `scripts/bin/infra/kms_smoke.sh` | `test_kms_module.py::TestKmsSmokeHardening` (AC-007–AC-010) |
| FR-009 | `infra/cloud/stackit/terraform/modules/kms/variables.tf`, `outputs.tf` | `test_kms_module.py::test_terraform_module_variables_tf_*` |
| FR-010 | `infra/local/helm/kms/values.yaml` | `test_kms_module.py::test_vault_helm_values_fullname_and_dev_mode` |
| FR-011 | `scripts/lib/infra/module_execution.sh` | `test_kms_module.py::test_module_execution_kms_local_driver_is_helm` |
| NFR-SEC-001 | `infra/local/helm/kms/values.yaml` (`{{KMS_VAULT_ROOT_TOKEN}}`), `kms.sh::kms_reconcile_runtime_secret()` | `test_kms_module.py::test_vault_helm_values_no_plaintext_token` |
| NFR-OBS-001 | Pre-existing `start_script_metric_trap` in all 4 scripts | verified by grep |
| NFR-REL-001 | `main.tf::lifecycle { create_before_destroy = true }` | `test_kms_module.py::test_terraform_module_keyring_has_create_before_destroy` |
| NFR-OPS-001 | `kms_apply.sh`, `kms_smoke.sh` | `test_contract.py::test_runtime_state_has_all_five_contract_output_keys` |
| NFR-A11Y-001 | N/A — infrastructure module | N/A |

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/kms.sh` — five new functions: `kms_endpoint()` (dual-lane), `kms_render_values_file()`, `kms_reconcile_runtime_secret()`, `kms_enable_vault_transit()`, `kms_delete_runtime_secret()`; also `kms_init_env()` extended with Vault env vars
  - `infra/cloud/stackit/terraform/modules/kms/main.tf` — full `stackit_kms_keyring` + `stackit_kms_key` Terraform implementation (was a 7-line stub)
  - `infra/local/helm/kms/values.yaml` — Vault dev mode values; note `devRootToken: "{{KMS_VAULT_ROOT_TOKEN}}"` (template placeholder, never plaintext) satisfying NFR-SEC-001
  - `scripts/lib/infra/module_execution.sh` — kms local driver changed from `noop` to `helm`; high-signal dispatch change
  - `blueprint/modules/kms/module.contract.yaml` — `KMS_ENDPOINT` added to `outputs.produced`
- High-risk files:
  - `scripts/bin/infra/kms_apply.sh` — `key_ring=` renamed to `key_ring_name=`, `endpoint=$(kms_endpoint)` added; consumers reading old state files will need re-apply
  - `scripts/bin/infra/kms_smoke.sh` — smoke now fails on missing/empty `key_ring_id` and `endpoint` in addition to `key_id`

## Validation Evidence
- Required commands executed: `pytest tests/infra/modules/kms/ -v` (23/23 PASSED); `make infra-validate` (PASS); `make infra-audit-version` (PASS); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (PASS — shellcheck, quality-sdd-check-all, quality-docs-check-changed, infra-contract-test-fast); `make quality-docs-check-changed` (PASS); `make docs-build` (PASS); `make docs-smoke` (PASS); `make quality-hardening-review` (PASS)
- Result summary: 23 new tests, all green. All quality gates pass. Pyramid ratios within thresholds.
- Artifact references: `specs/2026-05-07-issue-248-kms-module/traceability.md` (Validation Summary section)

## Risk and Rollback
- Main risks: (1) `endpoint` key is new in the state file and `key_ring=` renamed to `key_ring_name=` — consumers re-reading `artifacts/infra/kms_runtime.env` before re-running `infra-kms-apply` will see the updated key name; additive `endpoint` key is safe. (2) Smoke now fails when `key_ring_id`, `key_id`, or `endpoint` is empty — any environment with a pre-existing state file will fail smoke until `infra-kms-apply` is re-run. (3) Local lane Vault requires the `hashicorp` Helm repo added and `kubectl` context pointing at `docker-desktop`; missing prerequisites produce a clear Helm error. (4) `KMS_VAULT_HELM_CHART_VERSION_PIN="0.28.1"` pinned in `versions.sh` — future Vault Helm chart releases will surface as a version audit warning.
- Rollback strategy: Revert the PR branch. No persistent infrastructure is deployed by this PR — all changes are code, configuration, and documentation. The STACKIT Terraform module changes are additive; the foundation layer continues to manage its own resources unchanged. `KMS_ENDPOINT` addition to `module.contract.yaml` is backward-compatible (consumers not reading this output are unaffected). Re-running `infra-kms-destroy` then reverting clears any state artifacts.

## Deferred Proposals
- Proposal 1: `KMS_KEY_ROTATION_PERIOD` — add to `module.contract.yaml` and `variables.tf` when `stackit_kms_key` exposes a `rotation_period` attribute in a future provider version. Parked — trigger: on-scope: infra — AGENTS.backlog.md entry: `proposal(issue-248-kms-module): KMS_KEY_ROTATION_PERIOD input`.
- Proposal 2: Vault HA / persistent storage for the local lane — Vault standalone mode with raft storage and a PVC, so key material survives pod restarts in local dev. Parked — trigger: on-scope: infra — AGENTS.backlog.md entry: `proposal(issue-248-kms-module): Vault HA/persistent storage for local lane`.
