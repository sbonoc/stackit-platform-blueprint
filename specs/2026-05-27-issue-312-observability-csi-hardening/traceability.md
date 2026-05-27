# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-013 | N/A | CSI driver ArgoCD Applications in `infra/gitops/argocd/core/` | `infra/gitops/argocd/core/secrets-store-csi-driver.yaml`, `secrets-store-csi-driver-vault-provider.yaml` | `test_csi_driver_manifest_exists`, `test_chart_version_pinned` | `docs/platform/prerequisites.md` | ArgoCD sync status |
| FR-002 | SDD-C-005 | N/A | Vault provider sidecar config in CSI driver ArgoCD Application | `infra/gitops/argocd/core/secrets-store-csi-driver-vault-provider.yaml` | `test_vault_provider_manifest_exists` | `docs/platform/prerequisites.md` | — |
| FR-003 | SDD-C-005, SDD-C-009 | N/A | `SecretProviderClass` in observability namespace | `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` | `test_secret_provider_class_referenced` | `docs/platform/modules/observability/README.md` | `kubectl get secretproviderclass -n observability` |
| FR-004 | SDD-C-005, SDD-C-009 | N/A | `extraVolumes.csi` in STACKIT OTC values | `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` | `test_stackit_values_uses_csi_volume`, `test_stackit_values_no_secret_volume` | — | OTC pod `/etc/otel/secrets` mount |
| FR-005 | SDD-C-005 | N/A | Deprecation guard in `observability.sh`; removed call in apply script STACKIT branch | `scripts/bin/infra/observability_apply.sh`, `scripts/lib/infra/observability.sh` | `test_stackit_apply_does_not_call_reconcile` | — | — |
| FR-006 | SDD-C-005 | N/A | Removed call in destroy script STACKIT branch | `scripts/bin/infra/observability_destroy.sh` | `test_stackit_destroy_does_not_call_delete_secret` | — | — |
| FR-007 | SDD-C-005, SDD-C-009 | N/A | Vault TF provider + `vault_kv_secret_v2` resources in observability TF module | `infra/cloud/stackit/terraform/modules/observability/main.tf`, `versions.tf`, `variables.tf` | `test_observability_tf_writes_vault_kv_secret`, `test_observability_tf_declares_vault_provider` | — | Secrets Manager secret path `observability/otel-credentials` |
| FR-008 | SDD-C-005 | N/A | `required_core_capabilities` updated in contract | `blueprint/modules/observability/module.contract.yaml` | `test_module_contract_declares_csi_prerequisite` | — | — |
| FR-009 | SDD-C-007 | N/A | Updated/removed test assertions for K8s Secret lifecycle | `tests/infra/modules/observability/test_contract.py` | All 83+ assertions pass after update | — | — |
| FR-010 | SDD-C-007 | N/A | New CSI volume assertions | `tests/infra/modules/observability/test_contract.py` | `test_stackit_values_uses_csi_volume`, `test_stackit_values_no_secret_volume`, `test_secret_provider_class_referenced` | — | — |
| NFR-SEC-001 | SDD-C-009 | N/A | CSI volume replaces K8s Secret; no etcd write | STACKIT OTC values + TF module | `test_stackit_values_no_secret_volume`; AC-001 | `docs/platform/modules/observability/README.md` Security section | `kubectl get secret blueprint-observability-auth -n observability` → NotFound |
| NFR-SEC-002 | SDD-C-009 | N/A | Credentials not written to state files | `observability_apply.sh`, `observability_destroy.sh` | `test_runtime_state_does_not_contain_password` (existing) | — | — |
| NFR-SEC-003 | SDD-C-009 | N/A | `SecretProviderClass` scoped to `observability` namespace | `SecretProviderClass` manifest | `test_secret_provider_class_namespace_is_observability` | — | — |
| NFR-OBS-001 | SDD-C-010 | N/A | STACKIT Secrets Manager access logs | STACKIT Secrets Manager (external) | AC-003 (smoke) | `docs/platform/modules/observability/README.md` | Secrets Manager audit logs |
| NFR-REL-001 | SDD-C-011 | N/A | CSI mount failure = pod stays in ContainerCreating | Kubernetes default behaviour | AC-003 | `docs/platform/modules/observability/README.md` | Pod events |
| NFR-OPS-001 | SDD-C-011 | N/A | Rotation via Secrets Manager value update + CSI poll | Secrets Manager + CSI driver config | AC-003 | `docs/platform/modules/observability/README.md` Rotation section | — |
| NFR-A11Y-001 | — | N/A | N/A — no UI surfaces | — | T-A01 confirmed | — | — |
| AC-001 | SDD-C-007 | N/A | No K8s Secret object post-deploy | STACKIT OTC values, apply script | `test_stackit_values_no_secret_volume` | — | `kubectl get secret ... → NotFound` |
| AC-002 | SDD-C-007 | N/A | OTC pod starts; tmpfs mount populated | CSI driver + SecretProviderClass + TF | `test_stackit_values_uses_csi_volume` | — | OTC pod Running; smoke passes |
| AC-003 | SDD-C-007 | N/A | Smoke passes on STACKIT profile | All slices | `make infra-observability-smoke` | — | Smoke state `status=passed` |
| AC-004 | SDD-C-007 | N/A | All unit assertions pass | `test_contract.py` updated | pytest exit 0 | — | — |
| AC-005 | SDD-C-007 | N/A | Local lane unchanged | `observability_apply.sh` local branch | `test_reconcile_runtime_secret_function_exists`, `test_reconcile_targets_blueprint_observability_auth` (existing) | — | Local smoke passes |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001 through FR-010, NFR-SEC-001 through NFR-SEC-003, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-005

## Validation Summary
- Required bundles executed: `make quality-hooks-fast` (all 11 checks pass, includes `infra-validate`); `make blueprint-test-unit` (1064 passed, 38 subtests passed); `make infra-observability-smoke` deferred — STACKIT live cluster only (AC-003, manual acceptance criterion, documented in `pr_context.md`)
- Result summary: All automated gates green. STACKIT smoke (AC-003) is post-merge manual validation; no automated equivalent exists for a live STACKIT cluster.
- Documentation validation: `make quality-docs-check-changed` — PASS (included in `quality-hooks-fast`)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: automated credential rotation trigger — parked; trigger: on-scope: observability security hardening.
- Follow-up: local lane CSI driver support — parked; trigger: when Docker Desktop supports Secrets Store CSI Driver natively.
