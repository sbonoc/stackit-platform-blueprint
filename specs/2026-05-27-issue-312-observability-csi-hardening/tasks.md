# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: CSI Driver bootstrap ArgoCD Applications
- [ ] T-101 Create `infra/gitops/argocd/core/secrets-store-csi-driver.yaml` — ArgoCD Application (pinned chart version)
- [ ] T-102 Create `infra/gitops/argocd/core/secrets-store-csi-driver-vault-provider.yaml` — ArgoCD Application for Vault provider
- [ ] T-103 Document CSI driver as STACKIT bootstrap prerequisite in `docs/platform/prerequisites.md`
- [ ] T-104 Write unit assertions: manifests exist, chart versions pinned, sync-wave annotation present

## Implementation — Slice 2: Terraform credential write to Secrets Manager
- [ ] T-201 Write failing assertions: `test_observability_tf_writes_vault_kv_secret`, `test_observability_tf_declares_vault_provider`
- [ ] T-202 Add Vault Terraform provider to `infra/cloud/stackit/terraform/modules/observability/versions.tf`
- [ ] T-203 Add `vault_kv_secret_v2` resources writing five credential keys to `observability/otel-credentials`
- [ ] T-204 Add Vault provider variables to `variables.tf`
- [ ] T-205 Turn T-201 assertions green

## Implementation — Slice 3: SecretProviderClass + CSI volume in STACKIT OTC values
- [ ] T-301 Write failing assertions: `test_stackit_values_uses_csi_volume`, `test_stackit_values_no_secret_volume`, `test_secret_provider_class_referenced`
- [ ] T-302 Update `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` — replace `extraVolumes.secret` with `extraVolumes.csi`
- [ ] T-303 Add `SecretProviderClass` manifest to STACKIT ArgoCD observability Applications (dev/stage/prod)
- [ ] T-304 Mirror changes to `scripts/templates/blueprint/bootstrap/` counterparts
- [ ] T-305 Turn T-301 assertions green

## Implementation — Slice 4: Shell layer — remove K8s Secret calls from STACKIT path
- [ ] T-401 Rewrite failing assertions for STACKIT path: reconcile/delete MUST NOT be called; deprecation log MUST exist in function body
- [ ] T-402 Update `scripts/bin/infra/observability_apply.sh` — remove reconcile call in STACKIT case
- [ ] T-403 Update `scripts/bin/infra/observability_destroy.sh` — remove delete call in STACKIT case
- [ ] T-404 Add deprecation guard in `observability.sh` — emit `log_warn` when reconcile/delete called on STACKIT profile
- [ ] T-405 Turn T-401 assertions green

## Implementation — Slice 5: Contract, docs, publish artifacts
- [ ] T-501 Update `blueprint/modules/observability/module.contract.yaml` — add CSI prerequisites
- [ ] T-502 Update `docs/platform/modules/observability/README.md` — CSI prerequisite, rotation procedure
- [ ] T-503 Mirror README to `scripts/templates/blueprint/bootstrap/docs/platform/modules/observability/README.md`
- [ ] T-504 Populate `hardening_review.md`, `traceability.md`, `evidence_manifest.json`, `pr_context.md`
- [ ] T-505 Run `make quality-hooks-fast` — exits 0
- [ ] T-506 Run `make quality-docs-check-changed` — exits 0

## Accessibility Testing
- [x] T-A01 NFR-A11Y-001: N/A — no UI surfaces introduced or modified

## Validation and Release Readiness
- [ ] T-601 Run `make quality-sdd-check` — exits 0
- [ ] T-602 Run `python3 -m pytest tests/infra/modules/observability/ -x -q` — all assertions pass
- [ ] T-603 Confirm no `secretName: blueprint-observability-auth` remains in `infra/cloud/stackit/` paths
- [ ] T-604 Confirm `blueprint-observability-auth` K8s Secret lifecycle is intact in local-lane scripts

## Publish
- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md`
- [ ] P-003 PR description references `pr_context.md` and Open Questions table

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — no-impact; targets unchanged by this work item
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact; targets unchanged
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact; targets unchanged
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact; targets unchanged
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact; targets unchanged
