# Platform Prerequisites

This document lists cluster-level prerequisites that must be present before optional modules can be deployed.

## STACKIT Lane Prerequisites

### Secrets Store CSI Driver (required for `observability` module)

The [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/) is a cluster-level DaemonSet installed as a core ArgoCD Application on STACKIT lanes. It enables pods to mount secrets from STACKIT Secrets Manager as tmpfs volumes without creating K8s Secret objects in etcd.

**ArgoCD Applications (core bootstrap, `sync-wave: -1`):**
- `infra/gitops/argocd/core/{env}/secrets-store-csi-driver.yaml` — CNCF Secrets Store CSI Driver (chart: `secrets-store-csi-driver` v1.4.6)
- `infra/gitops/argocd/core/{env}/secrets-store-csi-driver-vault-provider.yaml` — HashiCorp Vault provider sidecar (chart: `vault-csi-provider` v0.5.0)

**Namespace:** `kube-system`

**Why `sync-wave: -1`:** The CSI driver must be running before any ArgoCD Application that mounts a CSI volume (e.g., the observability module). The negative sync-wave ensures it is synced and healthy before the default wave (0) Applications.

**Affected modules:** `observability` (STACKIT lane). The CSI driver is a cluster-wide resource; future modules may also use it.

**Local lane:** Not applicable. The local lane uses the `crossplane_plus_helm` driver with K8s Secrets for credential delivery. The Secrets Store CSI Driver is not supported on Docker Desktop without additional setup outside the scope of this blueprint.

## Adding a New Prerequisite

To add a cluster-level prerequisite:
1. Create an ArgoCD Application manifest in `infra/gitops/argocd/core/{env}/` with `sync-wave: -1` (or a lower wave number than any dependent Application).
2. Add the manifest to the relevant `infra/gitops/argocd/overlays/{env}/kustomization.yaml`.
3. Document it in this file.
4. Add a `required_core_capabilities` entry in the affected module's `blueprint/modules/<module>/module.contract.yaml`.
