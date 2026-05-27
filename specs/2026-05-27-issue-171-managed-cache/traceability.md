# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | N/A | STACKIT TF module: `stackit_redis_instance` + `stackit_redis_credential`, guarded by `var.managed_cache_enabled` | `infra/cloud/stackit/terraform/modules/managed-cache/main.tf`, `variables.tf`, `outputs.tf`, `versions.tf` | `test_tf_module_main_exists`, `test_tf_module_declares_redis_instance`, `test_tf_module_declares_redis_credential` | `docs/platform/modules/managed-cache/README.md` | `terraform state list` shows `module.managed_cache.*` after apply |
| FR-002 | SDD-C-005 | N/A | Foundation TF workspace wires managed-cache module; `managed_cache_enabled` variable (default `false`); `managed_cache_*` outputs | `infra/cloud/stackit/terraform/foundation/variables.tf`, `outputs.tf`, `main.tf` | `test_tf_foundation_wires_managed_cache_module`, `test_tf_foundation_outputs_managed_cache_host` | `docs/platform/modules/managed-cache/README.md` | `terraform output managed_cache_host` returns non-empty string |
| FR-003 | SDD-C-005 | N/A | bitnami/redis Helm values; Helm release `blueprint-managed-cache` in `managed-cache` namespace | `infra/local/helm/managed-cache/values.yaml` | `test_local_helm_values_exists`, `test_local_helm_values_uses_bitnami_redis` | `docs/platform/modules/managed-cache/README.md` | `helm list -n managed-cache` shows `blueprint-managed-cache` |
| FR-004 | SDD-C-005 | N/A | Shell lib: `managed_cache_seed_env_defaults`, `managed_cache_init_env`, `managed_cache_host`, `managed_cache_port`, `managed_cache_password`, `managed_cache_uri` with lane-branching via `is_stackit_profile` | `scripts/lib/infra/managed_cache.sh` | `test_managed_cache_host_function_exists`, `test_managed_cache_port_function_exists`, `test_managed_cache_password_function_exists`, `test_managed_cache_uri_function_exists`, `test_managed_cache_uri_uses_redis_scheme`, `test_managed_cache_host_local_lane_uses_in_cluster_dns`, `test_managed_cache_host_stackit_reads_foundation_output` | — | — |
| FR-005 | SDD-C-005, SDD-C-009 | N/A | Bin scripts: plan/apply/smoke/destroy; apply writes `managed_cache_runtime.env` (host, port, uri — no password) | `scripts/bin/infra/managed_cache_{plan,apply,smoke,destroy}.sh` | `test_apply_bin_script_exists`, `test_apply_script_calls_init_env`, `test_runtime_state_does_not_contain_password` | `docs/platform/modules/managed-cache/README.md` | `managed_cache_runtime.env` exists; `grep -i password managed_cache_runtime.env` → empty |
| FR-006 | SDD-C-005, SDD-C-014 | N/A | `OptionalModuleContract` schema: `MANAGED_CACHE_ENABLED` flag; outputs `MANAGED_CACHE_HOST/PORT/PASSWORD/URI`; make targets; paths | `blueprint/modules/managed-cache/module.contract.yaml` | `test_module_contract_file_exists`, `test_managed_cache_enabled_flag_declared`, `test_contract_outputs_declared` | — | `make infra-contract-test-fast` passes |
| FR-007 | SDD-C-005, SDD-C-014 | N/A | `optional_modules` entry in top-level contract | `blueprint/contract.yaml` | `test_module_contract_file_exists` (indirectly via contract registration check) | — | — |
| FR-008 | SDD-C-005 | N/A | Four make targets in generated Makefile and template; all in `.PHONY` | `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_make_target_plan_exists`, `test_make_target_apply_exists`, `test_make_target_smoke_exists`, `test_make_target_destroy_exists` | — | `make infra-managed-cache-plan --dry-run` exits 0 |
| FR-009 | SDD-C-007 | N/A | pytest module with ≥ 10 assertions | `tests/infra/modules/managed-cache/test_managed_cache_module.py` | All ≥ 10 assertions pass (AC-005) | — | — |
| FR-010 | SDD-C-013 | N/A | README documenting activation, inputs, outputs, URI format, make targets, rollback, relationship to issue #172 | `docs/platform/modules/managed-cache/README.md` | — | `docs/platform/modules/managed-cache/README.md` present | — |
| FR-011 | SDD-C-005 | N/A | Bootstrap templates mirror live files; `ensure_infra_template_file` call in `bootstrap.sh` | `scripts/templates/infra/bootstrap/infra/local/helm/managed-cache/values.yaml`, `scripts/bin/infra/bootstrap.sh` | — | — | `make blueprint-init-repo` seeds template without overwriting live files |
| NFR-SEC-001 | SDD-C-009 | N/A | `write_state_file` call in apply script excludes `MANAGED_CACHE_PASSWORD`; password retrieved at runtime from `managed_cache_password()` only | `scripts/bin/infra/managed_cache_apply.sh` | `test_runtime_state_does_not_contain_password` | `docs/platform/modules/managed-cache/README.md` Security section | `grep -i password managed_cache_runtime.env` → empty |
| NFR-SEC-002 | SDD-C-009 | N/A | `stackit_redis_instance` declares network ACL aligned with SKE egress CIDR ranges (same pattern as postgres); no open-world `0.0.0.0/0` sole entry | `infra/cloud/stackit/terraform/modules/managed-cache/main.tf` | `test_tf_module_declares_redis_instance` (verifies resource block exists; network ACL reviewed manually) | — | STACKIT portal: Redis instance ACL shows SKE egress CIDRs |
| NFR-OPS-001 | SDD-C-011 | N/A | `MANAGED_CACHE_ENABLED` defaults to `false` in `managed_cache_seed_env_defaults`; module absent from default foundation workspace | `scripts/lib/infra/managed_cache.sh`, `infra/cloud/stackit/terraform/foundation/variables.tf` | `test_managed_cache_enabled_flag_declared` (contract declares flag); AC-004 | `docs/platform/modules/managed-cache/README.md` — Activation section | Existing consumers unaffected (AC-004) |
| NFR-OPS-002 | SDD-C-011 | N/A | `managed_cache_smoke.sh` validates `MANAGED_CACHE_URI` non-empty and `redis://`-prefixed | `scripts/bin/infra/managed_cache_smoke.sh` | `test_managed_cache_uri_uses_redis_scheme`; AC-003 | `docs/platform/modules/managed-cache/README.md` — Smoke section | `make infra-managed-cache-smoke` passes on both lanes |
| NFR-A11Y-001 | — | N/A | N/A — no UI surfaces introduced or modified | — | Confirmed at intake | — | — |
| AC-001 | SDD-C-012 | N/A | `make infra-managed-cache-apply` on STACKIT + `MANAGED_CACHE_ENABLED=true` provisions Redis + writes `managed_cache_runtime.env` with host/port/uri, no password | All slices (FR-001, FR-002, FR-004, FR-005) | `test_runtime_state_does_not_contain_password`, `test_apply_bin_script_exists` | — | `managed_cache_runtime.env` present; no password key; `managed_cache_host` output non-empty |
| AC-002 | SDD-C-012 | N/A | `MANAGED_CACHE_URI` matches `redis://:.+@.+:[0-9]+/0` on both lanes | FR-004 | `test_managed_cache_uri_uses_redis_scheme` | `docs/platform/modules/managed-cache/README.md` | `managed_cache_uri()` output matches regex on both lanes |
| AC-003 | SDD-C-012 | N/A | `make infra-managed-cache-smoke` passes on both lanes | FR-005, NFR-OPS-002 | smoke script exits 0 | — | Smoke state `status=passed` |
| AC-004 | SDD-C-012 | N/A | Existing consumer with `MANAGED_CACHE_ENABLED=false` (default) completely unaffected | FR-006, FR-007, NFR-OPS-001 | — | — | No change to existing make targets or shell lib functions in other modules |
| AC-005 | SDD-C-012 | N/A | `python3 -m pytest tests/infra/modules/managed-cache/ -x -q` passes with ≥ 10 assertions | FR-009 | All ≥ 10 test assertions pass | — | pytest exit 0; assertion count ≥ 10 |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001 through FR-011, NFR-SEC-001, NFR-SEC-002, NFR-OPS-001, NFR-OPS-002, NFR-A11Y-001, AC-001 through AC-005

## Validation Summary
- Required bundles executed: pending implementation
- Result summary: pending implementation
- Documentation validation: pending (`make docs-build`, `make docs-smoke`)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Q-1 (open): STACKIT Redis TF resource name (`stackit_redis_instance` + `stackit_redis_credential`) must be verified before Slice 3. Slice 3 (TF module) is blocked until resolved.
- Follow-up: bitnami/redis local lane deprecation — tracked under issue #324 scope; this module follows the same migration pattern as postgres when #324 lands.
