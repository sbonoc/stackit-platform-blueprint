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
make auth-reconcile-runtime-identity
```

Consolidated diagnostics command:
```bash
make auth-runtime-identity-doctor
```

Direct ESO-only reconciliation command:
```bash
make auth-reconcile-eso-runtime-secrets
```

Direct ArgoCD repository credential reconciliation command:
```bash
make auth-reconcile-argocd-repo-credentials
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
- `ARGOCD_REPO_USERNAME`: `x-access-token`
- `ARGOCD_REPO_CREDENTIALS_REQUIRED`: `false`

### ESO Target Secrets
| Contract ID | Module Gate | Namespace | ExternalSecret | Target Secret | Required Keys |
| --- | --- | --- | --- | --- | --- |
| `runtime-credentials` | `mandatory` | `apps` | `runtime-credentials` | `runtime-credentials` | `username,password` |
| `keycloak-runtime-credentials` | `mandatory` | `security` | `keycloak-runtime-credentials` | `keycloak-runtime-credentials` | `KEYCLOAK_ADMIN_PASSWORD,KEYCLOAK_DATABASE_HOST,KEYCLOAK_DATABASE_PORT,KEYCLOAK_DATABASE_NAME,KEYCLOAK_DATABASE_USERNAME,KEYCLOAK_DATABASE_PASSWORD` |
| `iap-runtime-credentials` | `mandatory` | `security` | `iap-runtime-credentials` | `iap-runtime-credentials` | `client-id,client-secret,cookie-secret` |
| `argocd-gitops-repo` | `mandatory` | `argocd` | `argocd-gitops-repo` | `argocd-gitops-repo` | `type,url,username,password` |
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
- Local overlay keeps Keycloak Argo sync manual by default (`infra/gitops/argocd/overlays/local/keycloak.yaml`)
  so local-lite smoke does not fail before runtime credentials are available.
- Module-scoped realms are used by default:
  - IAP realm: `KEYCLOAK_REALM_IAP` (default `iap`)
  - Workflows realm: `KEYCLOAK_REALM_WORKFLOWS` (default `workflows`)
  - Langfuse realm: `KEYCLOAK_REALM_LANGFUSE` (default `langfuse`)
- Keycloak public DNS host is consumer-supplied (`KEYCLOAK_PUBLIC_HOST`) and consumed by all issuer/discovery URLs.
- Identity-aware proxy (`oauth2-proxy`) consumes:
  - `security/iap-runtime-credentials`
- IAP issuer must point to Keycloak (`KEYCLOAK_ISSUER_URL` contract).

## ArgoCD Repository Access Contract

- Canonical Argo Git repository URL is HTTPS-only and must match across all managed Argo manifests:
  - `https://github.com/<org>/<repo>.git`
- Canonical Argo repository credential secret is reconciled to:
  - `argocd/argocd-gitops-repo`
- Secret contract is provider-agnostic and materialized through ESO with required keys:
  - `type`
  - `url`
  - `username`
  - `password`
- Argo repository credentials must use a GitHub PAT:
  - accepted prefixes: `ghp_`, `github_pat_`
  - rejected prefix: `gho_`
- Static URL/scheme consistency checks run in `make infra-validate`.
- Live secret readiness + payload checks run in execute mode when calling:
  - `make auth-reconcile-argocd-repo-credentials`

## Runtime Knobs

Defaults live in `blueprint/repo.init.env`.
`KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED` gates optional-module Keycloak reconciliation (Workflows/Langfuse) during module deploy flows.
Generated-consumer module reconcile wrappers should reuse canonical helper primitives from
`scripts/lib/infra/keycloak_identity_contract.sh`:
- `keycloak_optional_module_reconcile_should_run`
- `keycloak_identity_contract_resolve_effective_realm_settings`
- `keycloak_optional_module_write_reconciled_state`
`RUNTIME_CREDENTIALS_REQUIRED` does not disable reconciliation; it only switches reconcile failures from warning mode (`false`) to hard-fail mode (`true`).
If the effective contract set resolves to empty (`contracts=0`), reconciliation exits as a no-op success (`status=noop-empty-contract-set`) and skips source-secret checks.

Additional reconcile knobs:
- `RUNTIME_CREDENTIALS_SOURCE_SECRET_NAME` (default `runtime-credentials-source`)
- `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` (format: `key=value,key2=value2`)
- `RUNTIME_CREDENTIALS_TARGET_SECRET_NAME` (default `runtime-credentials`)
- `RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS` (default `username,password`)
- `ARGOCD_REPO_USERNAME` (default `x-access-token`)
- `ARGOCD_REPO_CREDENTIALS_REQUIRED` (default `false`; when `true`, Argo repo credential mismatches/missing token fail fast)

## Local Profile Flow

For deterministic local seeding without storing plaintext credentials in Git:
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS='username=local-user,password=local-password'
make auth-reconcile-runtime-identity
```

For deterministic Argo private-repo credential reconciliation:
```bash
export ARGOCD_REPO_TOKEN='github_pat_your_token'
make auth-reconcile-runtime-identity
```

Local-lite Postgres note:
- When `BLUEPRINT_PROFILE=local-lite`, `POSTGRES_ENABLED=true`, and `artifacts/infra/postgres_runtime.env` is owned by local-lite/local runtime (`profile=local-lite`, `stack=local`) with a valid PostgreSQL DSN, runtime-credentials reconciliation skips the ESO readiness/target checks for `data/postgres-runtime-credentials`.
- This prevents false `warn-and-skip` noise when local Postgres runtime is already healthy through the local Helm/runtime-state path.
- Reconcile state artifacts surface this as `skipped_contract_count` and `skipped_contracts`.

Resulting state artifacts:
- `artifacts/infra/runtime_credentials_eso_reconcile.env`
- `artifacts/infra/runtime_credentials_eso_reconcile.json`
- `artifacts/infra/runtime_credentials_eso_target_secret_checks.json` (aggregated typed target-secret diagnostics)
- `artifacts/infra/runtime_credentials_eso_target_secret_checks/*.json` (per-contract typed target-secret diagnostics)
- `artifacts/infra/argocd_repo_credentials_reconcile.env`
- `artifacts/infra/argocd_repo_credentials_reconcile.json`
- `artifacts/infra/runtime_identity_reconcile.env`
- `artifacts/infra/runtime_identity_reconcile.json`
- `artifacts/infra/runtime_identity_doctor.env`
- `artifacts/infra/runtime_identity_doctor.json`
- `artifacts/infra/runtime_identity_doctor_report.json` (consolidated Argo/ESO/contract diagnostics)

To diagnose using the latest reconcile state by default:
```bash
make auth-runtime-identity-doctor
```

To diagnose from existing artifacts without re-running reconciliation:
```bash
export RUNTIME_IDENTITY_DOCTOR_REFRESH=false
make auth-runtime-identity-doctor
```

After local runtime credentials are ready, manually sync the local Keycloak Argo application (UI or CLI):
```bash
argocd app sync platform-keycloak-local
```

## Managed Profile Flow

The ESO source->target contract stays the same across profiles; only the source-store/provider wiring changes.
Provider-specific store wiring should be done via the extension surface (`infra/gitops/platform/base/extensions`) so drift-locked root files remain untouched.

Recommended managed adaptation:
1. Keep mandatory target `ExternalSecret` contracts unchanged.
2. Patch or replace source store wiring through extension manifests.
3. Re-run `make auth-reconcile-runtime-identity` to validate readiness and target-key coverage.

## Troubleshooting Matrix

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| CRD readiness timeout | ESO not fully bootstrapped | Check ESO controller health and rerun reconcile |
| `ExternalSecret` not Ready | source store auth/config invalid | Verify `runtime-credentials-source-store` provider wiring and source secret access |
| Target secret missing | source secret missing | Seed source values (`RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS`) or wire managed source store |
| Target secret missing keys | key contract mismatch | Align `RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS` with source secret keys |
| Argo repo URL mismatch | Mixed SSH/HTTPS or inconsistent GitHub repo URL across Argo manifests | Run `make infra-validate` and align all managed Argo GitHub repo URLs to one HTTPS URL |
| Argo repo auth rejected | `ARGOCD_REPO_TOKEN` missing or non-PAT token | Set `ARGOCD_REPO_TOKEN` to a GitHub PAT (`ghp_` or `github_pat_`) and rerun `make auth-reconcile-argocd-repo-credentials` |
