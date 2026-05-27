# PR Context

## Summary
- Work item: issue-312-observability-csi-hardening
- Objective: Eliminate etcd as a credential store for the observability module on STACKIT lanes by replacing the `blueprint-observability-auth` K8s Secret with Secrets Store CSI Driver delivery from STACKIT Secrets Manager.
- Scope boundaries: STACKIT-lane OTC credential delivery only. Local lane unchanged. Mount path and OTC `${file:...}` references unchanged.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-010, NFR-SEC-001 through NFR-SEC-003, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-005
- Acceptance criteria covered: AC-001 (no K8s Secret post-deploy), AC-002 (pod starts, tmpfs populated), AC-003 (smoke passes), AC-004 (pytest passes), AC-005 (local lane unchanged)
- Contract surfaces changed: `blueprint/modules/observability/module.contract.yaml` (new CSI prerequisite); `make infra-observability-apply` no longer creates `blueprint-observability-auth` on STACKIT profiles; `make infra-observability-destroy` no longer deletes it.

## Key Reviewer Files
- Primary files to review first: `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` (CSI volume); `infra/cloud/stackit/terraform/modules/observability/main.tf` (Vault kv_secret writes); new `infra/gitops/argocd/core/secrets-store-csi-driver*.yaml`; `scripts/bin/infra/observability_apply.sh` (reconcile removal).
- High-risk files: `scripts/lib/infra/observability.sh` (deprecation guard must not break local path); `tests/infra/modules/observability/test_contract.py` (5 assertions removed/rewritten).

## Validation Evidence
- Required commands executed: pending (to be filled at implementation time)
- Result summary: pending
- Artifact references: `traceability.md`, `hardening_review.md`

## Risk and Rollback
- Main risks: CSI driver unavailable at OTC deploy time → pod stuck in ContainerCreating (fail-safe, documented); Vault TF provider authentication against Secrets Manager requires SM user token from foundation outputs.
- Rollback strategy: revert `extraVolumes` block in STACKIT OTC values to `secret` type; re-run `make infra-observability-apply` to recreate `blueprint-observability-auth`.

## Deferred Proposals
- Proposal A (not implemented): Automated credential rotation trigger — rotate on expiry event from Secrets Manager; deferred; trigger: on-scope: observability security hardening.
- Proposal B (not implemented): Local lane CSI driver support — local lane retains K8s Secret; deferred; trigger: when Docker Desktop supports Secrets Store CSI Driver natively.
- Proposal C (not implemented): KMS envelope encryption for Secrets Manager stored credentials — out of scope; KMS module is a separate optional module.
