# KMS Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed key-management capability for encryption/signing workloads.
- Enable flag: `KMS_ENABLED` (default: `false`)
- Required inputs:
  - `KMS_KEY_RING_NAME`
  - `KMS_KEY_NAME`
- Make targets:
  - `infra-kms-plan`
  - `infra-kms-apply`
  - `infra-kms-smoke`
  - `infra-kms-destroy`
- Outputs:
  - `KMS_KEY_RING_NAME`
  - `KMS_KEY_NAME`
  - `KMS_KEY_RING_ID`
  - `KMS_KEY_ID`
  - `KMS_ENDPOINT`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Overview

The KMS module provisions a key-management service on both lanes:

- **Local lane (`local-*` profiles):** deploys [HashiCorp Vault](https://developer.hashicorp.com/vault) in dev mode via the `hashicorp/vault` Helm chart, enables the [Transit Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transit), and creates a named encryption key. Vault dev mode uses ephemeral in-memory storage — keys do not survive pod restarts. A `destroy` + `apply` cycle recovers the key.
- **STACKIT lane (`stackit-*` profiles):** provisions `stackit_kms_keyring` and `stackit_kms_key` resources via the STACKIT Terraform foundation layer.

## Stack Execution Model

Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `KMS_ENABLED=true`. Scaffolding paths are materialized by `make infra-bootstrap` only when `KMS_ENABLED=true`.

| Action | Local (`local-*`) | STACKIT (`stackit-*`) |
|---|---|---|
| `infra-kms-plan` | Renders Vault Helm values file (dry-run) | Warns missing foundation Terraform diff |
| `infra-kms-apply` | Installs `blueprint-vault` via Helm, enables Transit, creates key, writes K8s Secret | Applies STACKIT foundation Terraform |
| `infra-kms-smoke` | Validates non-empty `key_ring_id`, `key_id`, `endpoint` in runtime state | Same |
| `infra-kms-destroy` | Uninstalls Vault Helm release, removes K8s Secret | Removes keyring from state; schedules key deletion |

## Local Lane — HashiCorp Vault Transit

The local lane runs Vault in development mode. Vault dev mode starts with a known root token, has the KV secrets engine pre-enabled on `secret/`, and stores all data in memory.

### Prerequisites

- `hashicorp` Helm repository added: `helm repo add hashicorp https://helm.releases.hashicorp.com`
- `kubectl` context pointed at `docker-desktop`

### Configuration

| Variable | Default | Description |
|---|---|---|
| `KMS_NAMESPACE` | `kms` | Kubernetes namespace for the Vault release |
| `KMS_VAULT_HELM_RELEASE` | `blueprint-vault` | Helm release name |
| `KMS_VAULT_ROOT_TOKEN` | `blueprint-vault-root-token` | Vault dev mode root token (dev-only sentinel) |

The root token is delivered to consumers via a K8s Secret (`blueprint-vault-credentials` in `KMS_NAMESPACE`), not stored in plaintext in `values.yaml`.

### Vault Transit API access

On the local lane, `KMS_ENDPOINT` resolves to:

```
http://blueprint-vault.<KMS_NAMESPACE>.svc.cluster.local:8200/v1/transit
```

Consumer applications perform encrypt/decrypt operations against this endpoint using the `KMS_KEY_ID` key name and the token from the K8s Secret.

## STACKIT Lane — Managed KMS

On STACKIT profiles, the foundation Terraform layer provisions:

- `stackit_kms_keyring`: a keyring named by `KMS_KEY_RING_NAME`
- `stackit_kms_key`: a key named by `KMS_KEY_NAME`, with configurable algorithm, purpose, and protection

`KMS_ENDPOINT` resolves to the STACKIT KMS REST API base URL for the active region:

```
https://kms.api.<region>.stackit.cloud
```

## KMS_ENDPOINT Usage

`KMS_ENDPOINT` is available in the runtime state artifact and via ESO-synced environment variables after `infra-kms-apply` completes. Consumer applications use `KMS_ENDPOINT` together with `KMS_KEY_ID` to perform envelope encryption/decryption without branching on environment.

```python
import os, httpx

endpoint = os.environ["KMS_ENDPOINT"]
key_id = os.environ["KMS_KEY_ID"]
token = os.environ["VAULT_TOKEN"]  # or STACKIT KMS credentials

resp = httpx.post(
    f"{endpoint}/encrypt/{key_id}",
    headers={"X-Vault-Token": token},
    json={"plaintext": "<base64-encoded>"},
)
```

## Destroy Semantics

- **Local lane:** Uninstalls the Vault Helm release and removes the K8s Secret. Because Vault dev mode is ephemeral, all key material is lost. A subsequent `infra-kms-apply` will reinstall Vault and recreate the key.
- **STACKIT lane:** STACKIT KMS destroy follows the provider contract — keyrings are removed from Terraform state **without API deletion**, and keys are **scheduled for deletion** rather than being immediately deleted.

## Optional Inputs

| Variable | Default | Description |
|---|---|---|
| `KMS_KEY_RING_DESCRIPTION` | `Blueprint-managed KMS keyring.` | Keyring description (STACKIT) |
| `KMS_KEY_DESCRIPTION` | `Blueprint-managed KMS key.` | Key description (STACKIT) |
| `KMS_KEY_ALGORITHM` | `aes_256_gcm` | Key algorithm |
| `KMS_KEY_PURPOSE` | `symmetric_encrypt_decrypt` | Key purpose |
| `KMS_KEY_PROTECTION` | `software` | Key protection mode |
| `KMS_KEY_ACCESS_SCOPE` | `PUBLIC` | Key access scope |
| `KMS_KEY_IMPORT_ONLY` | `false` | Whether the key is import-only |
