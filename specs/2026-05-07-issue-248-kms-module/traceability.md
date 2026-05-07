# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | — | STACKIT Terraform module (keyring + key resources) | `infra/cloud/stackit/terraform/modules/kms/main.tf`, `versions.tf` | `tests/infra/modules/kms/test_kms_module.py` | `docs/platform/modules/kms/README.md` | — |
| FR-002 | SDD-C-005 | — | `module.contract.yaml` outputs.produced + KMS_ENDPOINT | `blueprint/modules/kms/module.contract.yaml` | `tests/infra/modules/kms/test_contract.py` | `docs/platform/modules/kms/README.md` | — |
| FR-003 | SDD-C-005 | — | `kms_endpoint()` dual-lane | `scripts/lib/infra/kms.sh` | `tests/infra/modules/kms/test_kms_module.py` | `docs/platform/modules/kms/README.md` | — |
| FR-004 | SDD-C-005 | — | `kms_render_values_file()`, `kms_reconcile_runtime_secret()`, `kms_enable_vault_transit()` | `scripts/lib/infra/kms.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| FR-005 | SDD-C-005, SDD-C-006 | — | State file write extended with endpoint key; helm driver case | `scripts/bin/infra/kms_apply.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | `artifacts/infra/kms_runtime.env` |
| FR-006 | SDD-C-005 | — | `kms_plan.sh` helm driver case | `scripts/bin/infra/kms_plan.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| FR-007 | SDD-C-005 | — | `kms_destroy.sh` helm driver case | `scripts/bin/infra/kms_destroy.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| FR-008 | SDD-C-005, SDD-C-006 | — | Smoke hardening for key_ring_id, key_id, endpoint | `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| FR-009 | SDD-C-005 | — | Terraform variables.tf + outputs.tf | `infra/cloud/stackit/terraform/modules/kms/variables.tf`, `outputs.tf` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| FR-010 | SDD-C-005 | — | Local Vault Helm chart values | `infra/local/helm/kms/values.yaml` | `tests/infra/modules/kms/test_kms_module.py` | `docs/platform/modules/kms/README.md` | — |
| FR-011 | SDD-C-005 | — | module_execution.sh kms local driver → helm | `scripts/lib/infra/module_execution.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| NFR-SEC-001 | SDD-C-009 | — | No plaintext Vault token in values.yaml; delivered via K8s Secret | `scripts/lib/infra/kms.sh` (`kms_reconcile_runtime_secret`) | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| NFR-OBS-001 | SDD-C-010 | — | `start_script_metric_trap` in all four scripts (pre-existing, no changes) | `scripts/bin/infra/kms_{plan,apply,smoke,destroy}.sh` | verified by grep | — | metric events |
| NFR-REL-001 | SDD-C-011 | — | `lifecycle { create_before_destroy = true }` on keyring | `infra/cloud/stackit/terraform/modules/kms/main.tf` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| NFR-OPS-001 | SDD-C-012 | — | State file has 5 keys; smoke validates key_ring_id, key_id, endpoint | `scripts/bin/infra/kms_apply.sh`, `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_contract.py`, `tests/infra/modules/kms/test_kms_module.py` | — | `artifacts/infra/kms_runtime.env` |
| NFR-A11Y-001 | — | — | N/A — infrastructure module | — | — | — | — |
| AC-001 | SDD-C-012 | — | Terraform resources declared | `infra/cloud/stackit/terraform/modules/kms/main.tf` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-002 | SDD-C-012 | — | variables.tf inputs | `infra/cloud/stackit/terraform/modules/kms/variables.tf` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-003 | SDD-C-012 | — | outputs.tf keys | `infra/cloud/stackit/terraform/modules/kms/outputs.tf` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-004 | SDD-C-012 | — | contract YAML outputs includes KMS_ENDPOINT | `blueprint/modules/kms/module.contract.yaml` | `tests/infra/modules/kms/test_contract.py` | — | — |
| AC-005 | SDD-C-012 | — | kms_endpoint() local lane returns Vault Transit URL | `scripts/lib/infra/kms.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-006 | SDD-C-012 | — | apply state file includes endpoint key | `scripts/bin/infra/kms_apply.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-007 | SDD-C-012 | — | smoke passes with 5-key state | `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-008 | SDD-C-012 | — | smoke fails empty key_id | `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-009 | SDD-C-012 | — | smoke fails empty key_ring_id | `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-010 | SDD-C-012 | — | smoke fails empty endpoint | `scripts/bin/infra/kms_smoke.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-011 | SDD-C-012 | — | runtime state fixture has all 5 contract keys | `tests/infra/modules/kms/test_contract.py` | `tests/infra/modules/kms/test_contract.py` | — | — |
| AC-012 | SDD-C-012 | — | Vault Helm values fullnameOverride + dev mode | `infra/local/helm/kms/values.yaml` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-013 | SDD-C-012 | — | kms_plan.sh helm case writes plan state | `scripts/bin/infra/kms_plan.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |
| AC-014 | SDD-C-012 | — | module_execution.sh kms local driver = helm | `scripts/lib/infra/module_execution.sh` | `tests/infra/modules/kms/test_kms_module.py` | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014

## Validation Summary
- Required bundles executed: (to be filled at implementation completion)
- Result summary: (to be filled at implementation completion)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: `KMS_KEY_ROTATION_PERIOD` input — add to contract when `stackit_kms_key` exposes `rotation_period` attribute in a future provider version.
- Follow-up 2: Vault HA/persistent storage for local lane — surfaces if a consumer requires key persistence across pod restarts in a local dev environment.
