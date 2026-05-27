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

### Post-Provision Configuration (per environment)

After running `make infra-stackit-foundation-apply` for the first time in each STACKIT environment:

1. **Set `vaultAddress`** in both files:
   - `infra/gitops/argocd/core/{env}/secrets-store-csi-driver-vault-provider.yaml` — Helm values `vaultAddress`
   - `infra/gitops/argocd/optional/{env}/observability.yaml` — `SecretProviderClass.spec.parameters.vaultAddress`

   The value is the `secrets_manager_vault_address` TF output:
   ```
   terraform -chdir=infra/cloud/stackit/terraform/foundation output -raw secrets_manager_vault_address
   ```
   Format: `https://secrets.<region>.onstackit.cloud/<sm-instance-name>`

2. **Configure Vault authentication** in the `SecretProviderClass` for each environment. Two options:

   **Option A — Kubernetes JWT auth (recommended, no K8s Secret needed):**
   Configure STACKIT Secrets Manager to trust the SKE cluster OIDC endpoint, create a Vault role bound to the `observability` service account, then set:
   ```yaml
   roleName: "<vault-role-name>"
   vaultKubernetesMountPath: "kubernetes"
   ```
   Replace placeholder values `CHANGE_ME_VAULT_ROLE_NAME` in `optional/{env}/observability.yaml`.

   **Option B — Token auth (simpler bootstrap, token stored in etcd):**
   Create a K8s Secret in the `observability` namespace with the SM user password as the token, then add `nodePublishSecretRef` to the `SecretProviderClass`:
   ```bash
   SM_PASSWORD=$(terraform -chdir=infra/cloud/stackit/terraform/foundation output -raw secrets_manager_password)
   kubectl create secret generic vault-sm-auth -n observability --from-literal=token="$SM_PASSWORD"
   ```
   Add to `SecretProviderClass.spec.parameters`:
   ```yaml
   nodePublishSecretRef:
     name: vault-sm-auth
     key: token
   ```
   Remove the `roleName` and `vaultKubernetesMountPath` placeholders.

3. **Commit the updated files** and push — ArgoCD will apply the changes on the next sync.

## Adding a New Prerequisite

To add a cluster-level prerequisite:
1. Create an ArgoCD Application manifest in `infra/gitops/argocd/core/{env}/` with `sync-wave: -1` (or a lower wave number than any dependent Application).
2. Add the manifest to the relevant `infra/gitops/argocd/overlays/{env}/kustomization.yaml`.
3. Document it in this file.
4. Add a `required_core_capabilities` entry in the affected module's `blueprint/modules/<module>/module.contract.yaml`.
