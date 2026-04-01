# Runtime Credentials (ESO)

This guide defines the canonical source-to-target runtime credential contract for generated consumers.

## Contract Overview

Blueprint-owned security manifests are materialized under:
- `infra/gitops/platform/base/security/kustomization.yaml`
- `infra/gitops/platform/base/security/runtime-source-store.yaml`
- `infra/gitops/platform/base/security/runtime-external-secrets-core.yaml`

Drift-safe consumer extension surface:
- `infra/gitops/platform/base/extensions/kustomization.yaml`

Canonical reconciliation command:
```bash
make auth-reconcile-eso-runtime-secrets
```

## Source To Target Flow

1. Source credentials exist in `security/runtime-credentials-source` (or are provided by a provider-backed store configuration).
2. ESO reads source credentials through `ClusterSecretStore/runtime-credentials-source-store`.
3. ESO reconciles canonical target credentials declared in the runtime identity contract.
4. Reconcile checks validate:
- CRDs established:
  - `clustersecretstores.external-secrets.io`
  - `externalsecrets.external-secrets.io`
- `ExternalSecret` readiness (`Ready=True`) for mandatory and enabled optional targets
- target secret existence and required key sets

<!-- BEGIN GENERATED RUNTIME IDENTITY CONTRACT SUMMARY -->
## Contract Summary (Generated)

### Runtime Defaults
- `KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED`: `true`
- `RUNTIME_CREDENTIALS_SOURCE_NAMESPACE`: `security`
- `RUNTIME_CREDENTIALS_TARGET_NAMESPACE`: `apps`
- `RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT`: `180`
- `RUNTIME_CREDENTIALS_REQUIRED`: `false`

### ESO Target Secrets
| Contract ID | Module Gate | Namespace | ExternalSecret | Target Secret | Required Keys |
| --- | --- | --- | --- | --- | --- |
| `runtime-credentials` | `mandatory` | `apps` | `runtime-credentials` | `runtime-credentials` | `username,password` |
| `keycloak-runtime-credentials` | `mandatory` | `security` | `keycloak-runtime-credentials` | `keycloak-runtime-credentials` | `KEYCLOAK_ADMIN_PASSWORD,KEYCLOAK_DATABASE_HOST,KEYCLOAK_DATABASE_PORT,KEYCLOAK_DATABASE_NAME,KEYCLOAK_DATABASE_USERNAME,KEYCLOAK_DATABASE_PASSWORD` |
| `iap-runtime-credentials` | `mandatory` | `security` | `iap-runtime-credentials` | `iap-runtime-credentials` | `client-id,client-secret,cookie-secret` |
| `postgres-runtime-credentials` | `postgres` | `data` | `postgres-runtime-credentials` | `postgres-runtime-credentials` | `POSTGRES_DB_NAME,POSTGRES_USER,POSTGRES_PASSWORD` |
| `neo4j-runtime-credentials` | `neo4j` | `data` | `neo4j-runtime-credentials` | `neo4j-runtime-credentials` | `NEO4J_AUTH_USERNAME,NEO4J_AUTH_PASSWORD` |
| `workflows-runtime-credentials` | `workflows` | `security` | `workflows-runtime-credentials` | `workflows-runtime-credentials` | `STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL,STACKIT_WORKFLOWS_OIDC_CLIENT_ID,STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` |
| `langfuse-runtime-credentials` | `langfuse` | `observability` | `langfuse-runtime-credentials` | `langfuse-runtime-credentials` | `LANGFUSE_OIDC_ISSUER_URL,LANGFUSE_OIDC_CLIENT_ID,LANGFUSE_OIDC_CLIENT_SECRET,LANGFUSE_DATABASE_URL,LANGFUSE_SALT,LANGFUSE_ENCRYPTION_KEY,LANGFUSE_NEXTAUTH_SECRET` |

### Keycloak Realms
| Realm ID | Module Gate | Realm Env | Default Realm | Client Display | Roles | Admin Role |
| --- | --- | --- | --- | --- | --- | --- |
| `iap` | `identity-aware-proxy` | `KEYCLOAK_REALM_IAP` | `iap` | `Identity-Aware Proxy` | `-` | `-` |
| `workflows` | `workflows` | `KEYCLOAK_REALM_WORKFLOWS` | `workflows` | `STACKIT Workflows` | `Admin,User,Viewer,Op` | `Admin` |
| `langfuse` | `langfuse` | `KEYCLOAK_REALM_LANGFUSE` | `langfuse` | `Langfuse` | `admin,user` | `-` |
<!-- END GENERATED RUNTIME IDENTITY CONTRACT SUMMARY -->

## Keycloak + IAP Contract

- Keycloak is deployed in namespace `security`.
- Keycloak is mandatory and rendered from:
  - `infra/gitops/argocd/core/<env>/keycloak.yaml`
- Keycloak admin and DB bootstrap credentials come from ESO target:
  - `security/keycloak-runtime-credentials`
- Module-scoped realms are used by default:
  - IAP realm: `KEYCLOAK_REALM_IAP` (default `iap`)
  - Workflows realm: `KEYCLOAK_REALM_WORKFLOWS` (default `workflows`)
  - Langfuse realm: `KEYCLOAK_REALM_LANGFUSE` (default `langfuse`)
- Keycloak public DNS host is consumer-supplied (`KEYCLOAK_PUBLIC_HOST`) and consumed by all issuer/discovery URLs.
- Identity-aware proxy (`oauth2-proxy`) consumes:
  - `security/iap-runtime-credentials`
- IAP issuer must point to Keycloak (`KEYCLOAK_ISSUER_URL` contract).

## Runtime Knobs

Defaults live in `blueprint/repo.init.env`.
`KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED` gates optional-module Keycloak reconciliation (Workflows/Langfuse) during module deploy flows.
`RUNTIME_CREDENTIALS_REQUIRED` does not disable reconciliation; it only switches reconcile failures from warning mode (`false`) to hard-fail mode (`true`).

Additional reconcile knobs:
- `RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME` (default `runtime-credentials-source`)
- `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` (format: `key=value,key2=value2`)
- `RUNTIME_CREDENTIALS_TARGET_SECRET_NAME` (default `runtime-credentials`)
- `RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS` (default `username,password`)

## Local Profile Flow

For deterministic local seeding without storing plaintext credentials in Git:
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS='username=local-user,password=local-password'
make auth-reconcile-eso-runtime-secrets
```

Resulting state artifact:
- `artifacts/infra/runtime_credentials_eso_reconcile.env`

## Managed Profile Flow

The ESO source->target contract stays the same across profiles; only the source-store/provider wiring changes.
Provider-specific store wiring should be done via the extension surface (`infra/gitops/platform/base/extensions`) so drift-locked root files remain untouched.

Recommended managed adaptation:
1. Keep mandatory target `ExternalSecret` contracts unchanged.
2. Patch or replace source store wiring through extension manifests.
3. Re-run `make auth-reconcile-eso-runtime-secrets` to validate readiness and target-key coverage.

## Troubleshooting Matrix

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| CRD readiness timeout | ESO not fully bootstrapped | Check ESO controller health and rerun reconcile |
| `ExternalSecret` not Ready | source store auth/config invalid | Verify `runtime-credentials-source-store` provider wiring and source secret access |
| Target secret missing | source secret missing | Seed source values (`RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS`) or wire managed source store |
| Target secret missing keys | key contract mismatch | Align `RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS` with source secret keys |
