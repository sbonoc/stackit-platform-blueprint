# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Delivery Approach
Red → green TDD order. Each slice writes failing tests first, then implements the minimum code to pass them. Quality gate (`make infra-contract-test-fast`) runs after every slice.

## Prerequisite: Resolve Q-1 before Slice 3
Slices 1, 2, 4, 5, 6 are independent of Q-1. Slice 3 (TF module) MUST NOT be started until the STACKIT Redis TF resource name is confirmed (verify via `terraform providers schema -json` or provider changelog for version `= 0.88.0`).

## Slices

### Slice 1: Module contract + shell lib skeleton
**Goal:** Establish the module contract file, register in blueprint/contract.yaml, and create the shell lib with all required functions present (implementations: `echo "not implemented"`). Tests go red first.

**Test file:** `tests/infra/modules/managed-cache/test_managed_cache_module.py`

Red assertions:
- `test_module_contract_file_exists`
- `test_managed_cache_enabled_flag_declared`
- `test_contract_outputs_declared` (MANAGED_CACHE_HOST, MANAGED_CACHE_PORT, MANAGED_CACHE_PASSWORD, MANAGED_CACHE_URI)
- `test_managed_cache_host_function_exists`
- `test_managed_cache_port_function_exists`
- `test_managed_cache_password_function_exists`
- `test_managed_cache_uri_function_exists`

Implementation:
- Create `blueprint/modules/managed-cache/module.contract.yaml`
- Add entry under `optional_modules` in `blueprint/contract.yaml`
- Create `scripts/lib/infra/managed_cache.sh` with all functions stubbed

Gate: `make infra-contract-test-fast`

### Slice 2: Make targets
**Goal:** All four make targets exist in Makefile and template. Bin scripts exist (stubs). Tests go red first.

Red assertions:
- `test_make_target_plan_exists`
- `test_make_target_apply_exists`
- `test_make_target_smoke_exists`
- `test_make_target_destroy_exists`
- `test_apply_bin_script_exists`

Implementation:
- Add `infra-managed-cache-plan/apply/smoke/destroy` targets to `make/blueprint.generated.mk` and `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`
- Create stub `scripts/bin/infra/managed_cache_{plan,apply,smoke,destroy}.sh`

Gate: `make infra-contract-test-fast`

### Slice 3: TF module
**Goal:** TF module files exist, declare the correct STACKIT Redis resources, and are wired into the foundation workspace. Tests go red first.

Red assertions:
- `test_tf_module_main_exists`
- `test_tf_module_declares_redis_instance`
- `test_tf_module_declares_redis_credential`
- `test_tf_foundation_wires_managed_cache_module`
- `test_tf_foundation_outputs_managed_cache_host`

Implementation:
- Create `infra/cloud/stackit/terraform/modules/managed-cache/main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
- Add `var.managed_cache_enabled` to `infra/cloud/stackit/terraform/foundation/variables.tf`
- Add `managed_cache_*` outputs to `infra/cloud/stackit/terraform/foundation/outputs.tf`
- Wire module call in foundation `main.tf` guarded by `var.managed_cache_enabled`

Gate: `make infra-validate` + `make infra-contract-test-fast`

### Slice 4: Local lane Helm values
**Goal:** Local Helm values file exists and configures bitnami/redis. Tests go red first.

Red assertions:
- `test_local_helm_values_exists`
- `test_local_helm_values_uses_bitnami_redis`

Implementation:
- Create `infra/local/helm/managed-cache/values.yaml`

Gate: `make infra-contract-test-fast`

### Slice 5: Shell lib + apply script — full implementation
**Goal:** Shell lib functions have real implementations with correct lane branching. Apply script writes state file without password. Tests go red first.

Red assertions:
- `test_managed_cache_uri_uses_redis_scheme`
- `test_managed_cache_host_local_lane_uses_in_cluster_dns`
- `test_managed_cache_host_stackit_reads_foundation_output`
- `test_runtime_state_does_not_contain_password`
- `test_apply_script_calls_init_env`

Implementation:
- Implement all functions in `managed_cache.sh` with `is_stackit_profile` branching
- Implement `managed_cache_apply.sh` with `write_state_file` (host, port, uri — no password)
- Implement `managed_cache_plan.sh` and `managed_cache_destroy.sh`

Gate: `make infra-contract-test-fast`

### Slice 6: Smoke script + bootstrap templates + docs
**Goal:** Smoke validates URI scheme. Bootstrap templates mirror live files. Docs written.

Implementation:
- Implement `managed_cache_smoke.sh` — validate `MANAGED_CACHE_URI` non-empty and `redis://`-prefixed on both lanes
- Create bootstrap template: `scripts/templates/infra/bootstrap/infra/local/helm/managed-cache/values.yaml`
- Create `docs/platform/modules/managed-cache/README.md`
- Add `ensure_infra_template_file` call for `infra/local/helm/managed-cache/values.yaml` in `bootstrap.sh`

Gate: `make quality-hooks-fast`

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- All N/A for this work item — infra-only change; no app code modifications.
