# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices

### Slice 1: Cluster bootstrap — Secrets Store CSI Driver ArgoCD Applications
1. Add `infra/gitops/argocd/core/secrets-store-csi-driver.yaml` — ArgoCD Application for `secrets-store-csi-driver/secrets-store-csi-driver` Helm chart (cluster-wide, pinned version).
2. Add `infra/gitops/argocd/core/secrets-store-csi-driver-vault-provider.yaml` — ArgoCD Application for the Vault provider side-car.
3. Document CSI driver as a STACKIT bootstrap prerequisite in `docs/platform/prerequisites.md`.
4. Write unit assertions: manifests exist, chart versions are pinned, sync-wave annotation precedes observability wave.

### Slice 2: Terraform — write credentials to STACKIT Secrets Manager (red → green TDD)
1. Write failing assertions: `test_observability_tf_writes_vault_kv_secret`, `test_observability_tf_declares_vault_provider`.
2. Add Vault Terraform provider to `infra/cloud/stackit/terraform/modules/observability/versions.tf`.
3. Add `vault_kv_secret_v2` resources writing all five credential keys to `observability/otel-credentials`.
4. Add Vault provider variables (endpoint, token/auth) to `variables.tf`.
5. Turn assertions green.

### Slice 3: SecretProviderClass + CSI volume in STACKIT OTC values (red → green TDD)
1. Write failing assertions: `test_stackit_values_uses_csi_volume`, `test_stackit_values_no_secret_volume`, `test_secret_provider_class_referenced`.
2. Replace `extraVolumes.secret` with `extraVolumes.csi` block in ALL four files that carry the inline override:
   - `infra/cloud/stackit/helm/observability/otel-collector.values.yaml`
   - `infra/gitops/argocd/optional/dev/observability.yaml`
   - `infra/gitops/argocd/optional/stage/observability.yaml`
   - `infra/gitops/argocd/optional/prod/observability.yaml`
3. Add `SecretProviderClass` manifest as an inline additional resource within each per-env ArgoCD observability Application (`dev/observability.yaml`, `stage/observability.yaml`, `prod/observability.yaml`) or as a standalone manifest in the same ArgoCD Application source directory, namespace-scoped to `observability`.
4. Bootstrap template note: no STACKIT-specific ArgoCD optional bootstrap template exists for the per-env observability manifests — no mirror required. Local-lane template (`scripts/templates/infra/bootstrap/infra/local/helm/observability/otel-collector.values.yaml`) is unchanged (local lane out of scope).
5. Turn assertions green.

### Slice 4: Shell layer — remove K8s Secret lifecycle from STACKIT path (red → green TDD)
1. Rewrite failing assertions for `observability_apply.sh` and `observability_destroy.sh` — STACKIT branch MUST NOT call reconcile/delete functions; deprecation log MUST be present in function body.
2. Update `observability_apply.sh`: remove `observability_reconcile_runtime_secret` call in STACKIT case.
3. Update `observability_destroy.sh`: remove `observability_delete_runtime_secret` call in STACKIT case.
4. Add deprecation guard in `observability.sh` functions.
5. Turn assertions green.

### Slice 5: Contract, docs, traceability, and publish artifacts
1. Update `blueprint/modules/observability/module.contract.yaml` — add CSI prerequisites.
2. Update `docs/platform/modules/observability/README.md` — CSI prerequisite section, rotation procedure, K8s Secret lifecycle removal.
3. Mirror README to bootstrap template.
4. Populate `hardening_review.md`, `traceability.md`, `evidence_manifest.json`, `pr_context.md`.
5. Run `make quality-hooks-fast` and `make quality-docs-check-changed` — both MUST pass.

## Change Strategy
- Migration/rollout sequence: Slice 1 (CSI driver bootstrap) → Slice 2 (TF credential write) → Slice 3 (CSI volume in OTC values) → Slice 4 (shell cleanup) → Slice 5 (docs/contracts).
- Backward compatibility policy: Local lane unchanged; local-lane consumers are unaffected. STACKIT-lane consumers must have the CSI driver running before deploying the observability module post-upgrade — documented as a migration prerequisite.
- Rollback plan: Revert `extraVolumes` block to `secret` type; re-run `make infra-observability-apply` to recreate the `blueprint-observability-auth` K8s Secret. The existing reconcile functions are not removed, only de-called in the STACKIT branch.

## Validation Strategy (Shift-Left)
- Unit checks: pytest assertions on Helm values files (no `secretName: blueprint-observability-auth` in STACKIT values; `csi:` block present), shell scripts (reconcile not called in STACKIT path), TF module files (vault provider + kv secret resources).
- Contract checks: `make quality-sdd-check` + `make quality-hooks-fast`.
- Integration checks: N/A — no HTTP routes or new API endpoints.
- E2E checks: `make infra-observability-smoke` on STACKIT profile (out-of-repo; documented as manual acceptance criterion).

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
- App onboarding impact: no-impact
- Notes: No app onboarding make targets or port-forward wrappers are modified by this work item. All targets above remain unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/observability/README.md`; `docs/platform/prerequisites.md`.
- Consumer docs updates: none (STACKIT-lane internal change; consumer env-var contract unchanged).
- Mermaid diagrams updated: ADR diagrams (sequence + flowchart already drafted in architecture.md).
- Docs validation commands: `make quality-docs-check-changed`.

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP route/filter changes. STACKIT smoke is manual (requires live cluster); result recorded in `pr_context.md`.
- Publish checklist: requirement/contract coverage; key reviewer files; validation evidence; rollback notes.

## Operational Readiness
- Logging/metrics/traces: STACKIT Secrets Manager access logs provide credential read audit trail (NFR-OBS-001). No additional in-repo instrumentation.
- Alerts/ownership: OTC `ContainerCreating` stuck alert covers CSI mount failure; existing cluster health monitoring sufficient.
- Runbook updates: `docs/platform/modules/observability/README.md` — credential rotation procedure.

## Risks and Mitigations
- Risk 1: Vault Terraform provider may require a static Vault token for authentication against STACKIT Secrets Manager. Mitigation: use a Secrets Manager user token provisioned by the foundation TF layer; pass as TF variable from foundation outputs.
- Risk 2: CSI driver sync-wave ordering in ArgoCD may not be respected if observability ArgoCD Application does not declare a dependent sync-wave. Mitigation: add `argocd.argoproj.io/sync-wave` annotation to both Applications.
