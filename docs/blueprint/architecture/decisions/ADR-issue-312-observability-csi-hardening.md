# ADR — issue-312-observability-csi-hardening: Observability Credential Delivery via Secrets Store CSI Driver

**Status:** proposed
**Date:** 2026-05-27

## Context

The observability module on STACKIT lanes delivers credentials (`username`, `password`, and three push URLs) to the OTC pod via a K8s Secret (`blueprint-observability-auth`) mounted at `/etc/otel/secrets`. The Secret object lives in etcd and is created/destroyed by a shell script. This approach:

1. Stores credentials in etcd — readable by anyone with cluster-admin access or direct etcd access if etcd is not encrypted at rest.
2. Requires the operator to hold plaintext credentials during `make infra-observability-apply`.
3. Provides no audit trail for which workload read the Secret and when.

PR #308 introduced the projected volume mount as an interim step. This ADR covers the next level: eliminating the K8s Secret entirely by routing credentials through the Secrets Store CSI Driver backed by STACKIT Secrets Manager.

## Decision 1: Secret store backend — STACKIT Secrets Manager (not KMS)

**Decision:** Use STACKIT Secrets Manager as the CSI driver backend, accessed via the Vault provider.

**Rationale:**

| Option | Pros | Cons |
|---|---|---|
| A — STACKIT Secrets Manager + Vault provider (selected) | Vault-compatible API; CSI Vault provider is production-grade; Secrets Manager is already a blueprint module; full audit trail via SM access logs | Requires writing credentials to SM after TF provision (Vault TF provider) |
| B — STACKIT KMS | — | KMS is a key management service (encrypt/decrypt/sign), not a secret store; no Vault-compatible secret-read API; no compatible CSI provider plugin exists |

STACKIT KMS manages encryption keys; it does not serve arbitrary secret values over the Vault API that the CSI Vault provider requires. STACKIT Secrets Manager exposes exactly this API and is already integrated in the blueprint foundation.

## Decision 2: CSI driver installation scope

**Decision:** Install the Secrets Store CSI Driver and its Vault provider sidecar as cluster-level ArgoCD Applications in `infra/gitops/argocd/core/`, applied during STACKIT core bootstrap. Not part of the observability module.

**Rationale:** The CSI driver is a cluster-wide DaemonSet — it serves all namespaces and should not be tied to any single optional module. Installing it at the core bootstrap layer ensures it is always available before any optional module that needs CSI secret mounts.

## Decision 3: Local lane scope

**Decision:** Local lane is out of scope. The local lane retains the existing K8s Secret path (`blueprint-observability-auth` via `observability_reconcile_runtime_secret()`).

**Rationale:** The security threat model for local Docker Desktop (single developer machine, no shared etcd) does not warrant the additional infrastructure complexity. The Secrets Store CSI Driver is not natively supported on Docker Desktop without additional setup that is out of scope.

## Decision 4: Mount path and OTC config unchanged

**Decision:** The mount path (`/etc/otel/secrets`) and all OTC `${file:/etc/otel/secrets/<key>}` config references remain unchanged.

**Rationale:** Zero consumer impact. Changing the mount path would require updating every STACKIT ArgoCD manifest and consumer documentation. The CSI volume type is transparent to the OTC process reading the mounted files.

## Consequences

- `blueprint-observability-auth` K8s Secret is no longer created on STACKIT lanes — breaking change for any consumer that queries this Secret directly.
- STACKIT Secrets Manager (`SECRETS_MANAGER_ENABLED=true`) becomes an implicit prerequisite when `OBSERVABILITY_ENABLED=true` on STACKIT profiles.
- Credential rotation is asynchronous (CSI driver polls Secrets Manager on a configurable interval, default 2 minutes). Immediate rotation requires a pod restart.
- Rollback: revert `extraVolumes` block to `secret` type and re-run `make infra-observability-apply` to recreate the K8s Secret.
