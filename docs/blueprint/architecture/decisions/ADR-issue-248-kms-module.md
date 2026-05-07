# ADR: Issue #248 — KMS Module Implementation (Dual-Lane)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-07
- **Issue**: #248
- **Work item**: `specs/2026-05-07-issue-248-kms-module/`

## Context

The `infra/cloud/stackit/terraform/modules/kms/main.tf` is a 7-line stub (no provider resources declared). The STACKIT foundation layer already provisions KMS correctly via `stackit_kms_keyring` + `stackit_kms_key`, but the standalone module has no resources and the local lane (`kms:plan`, `kms:apply`, `kms:destroy`) dispatches to a `noop` driver — making the local-lane a silent no-op.

The remaining gaps addressed by this work item:

1. The STACKIT standalone Terraform module has no resources — `stackit_kms_keyring` and `stackit_kms_key` are not declared.
2. `KMS_ENDPOINT` is missing from `module.contract.yaml` — consumers have no lane-agnostic way to discover the KMS API address.
3. The local lane is a `noop` — developers have no KMS-equivalent locally, blocking the future data buyer encryption-at-rest feature.
4. `kms_endpoint()` does not exist in `kms.sh`.
5. The `kms_apply.sh` state file write lacks the `endpoint` key.
6. Smoke validations check only `key_id` presence; `key_ring_id` and `endpoint` are not validated.
7. No automated tests or production-grade documentation exist.

Two contract terminology mismatches with issue #248 are also resolved here:
- Issue used `KMS_INSTANCE_NAME` but STACKIT KMS uses a keyring/key model (no "instance" concept); existing `KMS_KEY_RING_NAME` is correct.
- Issue listed `KMS_KEY_ROTATION_PERIOD` as an input, but `stackit_kms_key` v0.88.0 does not expose a `rotation_period` attribute; this input is deferred.

## Decisions

### D-1: Additive standalone Terraform module mirroring foundation pattern

Implement `infra/cloud/stackit/terraform/modules/kms/` as a standalone module with `stackit_kms_keyring` and `stackit_kms_key` resources, mirroring the foundation pattern in `infra/cloud/stackit/terraform/foundation/main.tf`. The foundation layer continues to manage its own inline resources; the standalone module is for isolated use.

The `stackit_kms_keyring` resource includes `lifecycle { create_before_destroy = true }` to prevent silent destroy/recreate during name changes. STACKIT KMS destroy semantics follow the provider contract: keyrings are removed from Terraform state without API deletion; keys are scheduled for deletion rather than immediately deleted.

**Rejected alternative:** Have the foundation call the standalone module — rejected due to Terraform state migration risk with no active consumer driver for the refactor.

### D-2: Local lane via HashiCorp Vault Transit Secrets Engine (Q-1 resolved 2026-05-07)

STACKIT KMS cannot run on docker-desktop Kubernetes. The issue body specifies Vault Transit as the local lane: "HashiCorp Vault Transit Secrets Engine — provides encryption-as-a-service with identical conceptual operations (create key, encrypt, decrypt, rotate, BYOK)."

The local lane deploys HashiCorp Vault in dev mode (`server.dev.enabled: true`) via the `hashicorp/vault` Helm chart, installs it under the release name `blueprint-vault`, enables the Transit secrets engine post-install, and creates the KMS key in Transit. `KMS_ENDPOINT` on the local lane is the Vault Transit API path: `http://blueprint-vault.<KMS_NAMESPACE>.svc.cluster.local:8200/v1/transit`.

Vault dev mode uses ephemeral in-memory storage — keys do not persist across pod restarts. This is intentional for local dev; a `destroy` + `apply` cycle recovers the key.

**Rejected alternative:** Vault standalone mode with raft storage — rejected because it adds PersistentVolumeClaim provisioning, a significantly more complex chart configuration, and startup complexity, all disproportionate to local dev needs where no real data is encrypted.

### D-3: `KMS_ENDPOINT` — regional REST API URL on STACKIT, Vault Transit path on local lane

`KMS_ENDPOINT` is a new output added to `module.contract.yaml`. On the STACKIT lane, `kms_endpoint()` returns the STACKIT KMS REST API base URL constructed from the active region (pattern: `https://kms.api.<region>.stackit.cloud`). On the local lane, it returns the Vault Transit API path. Consumer applications use this endpoint together with `KMS_KEY_ID` to perform encryption/decryption operations against the KMS API without branching on environment.

**Rejected alternative:** Expose only `KMS_KEY_ID` and require consumers to hard-code the endpoint — rejected because the endpoint differs between local and STACKIT lanes; hard-coding creates the environment-branching anti-pattern the blueprint explicitly prohibits.

### D-4: `KMS_INSTANCE_NAME` vs `KMS_KEY_RING_NAME` — keep existing contract input names

Issue #248 used `KMS_INSTANCE_NAME` and `KMS_KEY_ROTATION_PERIOD` as input names. STACKIT KMS uses a keyring/key model with no "instance" abstraction. The existing `module.contract.yaml` with `KMS_KEY_RING_NAME` + `KMS_KEY_NAME` correctly maps to `stackit_kms_keyring.display_name` and `stackit_kms_key.display_name`. Renaming to `KMS_INSTANCE_NAME` would obscure the provider model.

`KMS_KEY_ROTATION_PERIOD` is deferred: `stackit_kms_key` v0.88.0 does not expose a `rotation_period` attribute. A backlog entry tracks this for when provider support ships.

**Rejected alternative:** Rename `KMS_KEY_RING_NAME` → `KMS_INSTANCE_NAME` to match issue wording — rejected because STACKIT KMS has no "instance" concept; the rename would mislead implementers and consumers.

### D-5: Vault root token delivered via K8s Secret, not values.yaml

The Vault root token in dev mode MUST NOT be stored in plaintext in `values.yaml` or any rendered artifact. `kms_reconcile_runtime_secret()` writes a K8s Secret in `KMS_NAMESPACE` containing the Vault token and endpoint. `kms_render_values_file()` reads the token from `KMS_VAULT_ROOT_TOKEN` env var with a dev-only sentinel default.

**Rejected alternative:** Hardcode `devRootToken: root` in `values.yaml` — rejected because plaintext secrets in rendered artifacts violate NFR-SEC-001 and the blueprint credential delivery contract.

## Consequences

- STACKIT standalone Terraform module enables isolated KMS provisioning outside the foundation deployment pattern.
- Local lane (`kms:plan`, `kms:apply`, `kms:smoke`, `kms:destroy`) transitions from a silent no-op to a fully functional Vault-backed local KMS implementation.
- `KMS_ENDPOINT` is available in the runtime state artifact and via ESO-synced env vars, enabling consumer applications to perform envelope encryption/decryption against the KMS API without branching on environment.
- `KMS_KEY_ROTATION_PERIOD` is explicitly deferred; a backlog entry ensures it surfaces when the STACKIT provider adds support.
