# Work Item Context Pack

## Context Snapshot
- Work item: 2026-05-27-issue-312-observability-csi-hardening
- Track: blueprint
- SPEC_READY: true (all sign-offs recorded; implementation unlocked)
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-312-observability-csi-hardening.md
- ADR status: approved

## Problem Being Solved
The observability module delivers STACKIT credentials to the OTC pod via a K8s Secret (`blueprint-observability-auth`) stored in etcd. This exposes credentials to anyone with cluster-admin access and provides no credential-read audit trail. This work item replaces the K8s Secret with direct delivery via the Secrets Store CSI Driver backed by STACKIT Secrets Manager.

## Affected Files (Key)
- `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` — extraVolumes block
- `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` — SecretProviderClass
- `infra/cloud/stackit/terraform/modules/observability/` — Vault provider + kv_secret resources
- `scripts/bin/infra/observability_apply.sh`, `observability_destroy.sh` — reconcile/delete call removal
- `scripts/lib/infra/observability.sh` — deprecation guard
- `tests/infra/modules/observability/test_contract.py` — 5 assertions updated, 3+ new
- `blueprint/modules/observability/module.contract.yaml`
- `docs/platform/modules/observability/README.md`
- New: `infra/gitops/argocd/core/secrets-store-csi-driver.yaml`
- New: `infra/gitops/argocd/core/secrets-store-csi-driver-vault-provider.yaml`
- New: `docs/blueprint/architecture/decisions/ADR-issue-312-observability-csi-hardening.md`

## Guardrail Controls
- Applicable control IDs: SDD-C-001 through SDD-C-011, SDD-C-013 through SDD-C-021

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
