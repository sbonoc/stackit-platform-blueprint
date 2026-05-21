# Workflows Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision and reconcile STACKIT Workflows (managed Airflow) and deploy DAGs.
- Enable flag: `WORKFLOWS_ENABLED` (default: `false`)
- Required inputs:
  - `STACKIT_PROJECT_ID`
  - `STACKIT_REGION`
  - `STACKIT_WORKFLOWS_DAGS_REPO_URL`
  - `STACKIT_WORKFLOWS_DAGS_REPO_BRANCH`
  - `STACKIT_WORKFLOWS_DAGS_REPO_USERNAME`
  - `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN`
  - `STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL`
  - `STACKIT_WORKFLOWS_OIDC_CLIENT_ID`
  - `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET`
  - `STACKIT_OBSERVABILITY_INSTANCE_ID`
- Make targets:
  - `infra-stackit-workflows-plan`
  - `infra-stackit-workflows-apply`
  - `infra-stackit-workflows-reconcile`
  - `infra-stackit-workflows-dag-deploy`
  - `infra-stackit-workflows-dag-parse-smoke`
  - `infra-stackit-workflows-smoke`
  - `infra-stackit-workflows-destroy`
- Outputs:
  - `STACKIT_WORKFLOWS_INSTANCE_ID`
  - `STACKIT_WORKFLOWS_INSTANCE_NAME`
  - `STACKIT_WORKFLOWS_INSTANCE_FQDN`
  - `STACKIT_WORKFLOWS_WEB_URL`
  - `STACKIT_WORKFLOWS_HEALTH_STATUS`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Overview

The Workflows module provisions a STACKIT-managed Apache Airflow instance and connects it to your DAG Git repository and Keycloak OIDC identity provider.

**STACKIT-lane only (SDD-C-014 exception).** There is no Terraform provider resource for STACKIT Workflows; all lifecycle operations call the REST API at `https://workflows.api.stackit.cloud/v1alpha` directly. The `api_contract` provision driver is used throughout. Local profiles (`local-*`) are not supported — all make targets `log_fatal` immediately on a non-STACKIT profile.

Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `WORKFLOWS_ENABLED=true`. Scaffolding paths are materialized by `make infra-bootstrap` only when `WORKFLOWS_ENABLED=true`.

## Stack Execution Model

| Action | STACKIT (`stackit-*`) |
|---|---|
| `infra-stackit-workflows-plan` | Validates env vars; generates `workflows_request_payload.json`; writes `provision_driver`, `provision_path`, `payload_file`, `display_name` to plan state |
| `infra-stackit-workflows-apply` | `POST /instances` (HTTP 201) or idempotent `GET` on HTTP 409; writes `instance_id`, `instance_fqdn`, `web_url`, `health_status` to instance state |
| `infra-stackit-workflows-reconcile` | Cardinality guard (fail if > 1 instance without explicit ID); if no instance state exists, runs apply to create; always delegates to `keycloak_reconcile` |
| `infra-stackit-workflows-dag-deploy` | `PATCH /instances/{id}/dags-repository` to set `dagsRepository` URL; writes `status=synced` and `dags_repo_url` to dag deploy state |
| `infra-stackit-workflows-dag-parse-smoke` | Validates `*dag*.py` files are absent from `apps/` (guarded path); writes smoke result |
| `infra-stackit-workflows-smoke` | Checks instance `Active` health status and live API reachability; writes `status=passed` |
| `infra-stackit-workflows-destroy` | `DELETE /instances/{id}`; writes HTTP status and instance ID to destroy state; removes state artifacts |

## Provisioning Lifecycle

Full lifecycle (first-time setup):

```
make infra-stackit-workflows-plan          # validate env + write plan state
make infra-stackit-workflows-apply         # provision instance via REST API
make infra-stackit-workflows-reconcile     # upsert Keycloak OIDC client + converge
make infra-stackit-workflows-dag-deploy    # link DAG repository to instance
make infra-stackit-workflows-smoke         # verify instance is Active + API live
```

Day-2 reconciliation:

```
make infra-stackit-workflows-reconcile     # cardinality guard + keycloak converge
```

DAG validation before deploy:

```
make infra-stackit-workflows-dag-parse-smoke   # validate DAG file locations
```

## API Contract Approach

Provisioning uses the STACKIT Workflows REST API (`v1alpha`). No Terraform resource exists for this service in provider versions through v0.96.0; the `api_contract` provision driver is the canonical approach until a provider resource becomes available.

Endpoint base: `https://workflows.api.stackit.cloud/v1alpha/projects/{projectId}/regions/{region}`

Key operations:

| Operation | Method | Path |
|---|---|---|
| Create instance | `POST` | `/instances` |
| Get instance | `GET` | `/instances/{instanceId}` |
| Update DAG repo | `PATCH` | `/instances/{instanceId}/dags-repository` |
| Delete instance | `DELETE` | `/instances/{instanceId}` |

The apply script handles HTTP 409 (instance already exists) as an idempotency signal: it re-fetches the existing instance and writes the same state keys as a successful create. Re-running `infra-stackit-workflows-apply` when the instance already exists is safe.

## Keycloak OIDC Contract

`make infra-stackit-workflows-reconcile` (which internally calls the Keycloak reconcile script) upserts a confidential OIDC client in Keycloak so that the Airflow web UI can authenticate users via the platform identity provider.

Client configuration applied:

| Field | Value |
|---|---|
| Client type | Confidential (client_secret) |
| Standard flow | Enabled |
| Direct access grants | Enabled |
| Redirect URIs | Base wildcard: `https://*.workflows.{region}.stackit.cloud/*`; resolved instance URL appended from instance state when available |
| Web origins | Base wildcard: `https://*.workflows.{region}.stackit.cloud`; resolved web origin appended from instance state when available |
| Realm roles | `Admin`, `User`, `Viewer`, `Op` |
| Roles claim mapper | `roles` — included in ID token, access token, and userinfo |

State written to `artifacts/infra/workflows_keycloak_reconcile.env`:

| Key | Description |
|---|---|
| `status` | `reconciled` |
| `realm` | Keycloak realm name |
| `client_id` | OIDC client ID registered in Keycloak |
| `redirect_uris` | Space-separated list of allowed redirect URIs |
| `web_origins` | Space-separated list of allowed web origins |
| `admin_username` | Keycloak admin username used for reconciliation |
| `timestamp_utc` | ISO-8601 timestamp of last reconciliation |

Neither `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` (OIDC client secret) nor `STACKIT_WORKFLOWS_ADMIN_PASSWORD` (Keycloak admin credential) is ever written to any state file.

## DAG Repository Requirements

The DAG repository is a standard Git repository. Requirements:

- URL must end with `.git` (enforced by `workflows_init_env()` with `log_fatal`)
- The branch specified by `STACKIT_WORKFLOWS_DAGS_REPO_BRANCH` must exist
- DAG Python files matching `*dag*.py` must NOT be placed under an `apps/` directory — `infra-stackit-workflows-dag-parse-smoke` will fail fast with `"DAG entrypoints must live in repository-root dags/"` if any such files are found under `apps/`
- The deploy token (`STACKIT_WORKFLOWS_DAGS_REPO_TOKEN`) is passed directly to the API and is never written to state files

## State File Outputs

All artifacts are written to `artifacts/infra/` with the following naming convention and key contracts:

### `workflows_plan.env`

| Key | Description |
|---|---|
| `provision_driver` | Always `api_contract` |
| `provision_path` | `/projects/{projectId}/regions/{region}/instances` |
| `payload_file` | Path to the generated `workflows_request_payload.json` |
| `display_name` | Instance display name (≤ 16 chars, `a-z0-9-`) |

### `workflows_instance.env`

| Key | Description |
|---|---|
| `instance_id` | STACKIT Workflows instance UUID |
| `instance_fqdn` | Fully qualified domain name of the Airflow instance |
| `web_url` | Full HTTPS URL of the Airflow web UI |
| `health_status` | Instance health as reported by the API (`Active`, etc.) |

### `workflows_keycloak_reconcile.env`

See [Keycloak OIDC Contract](#keycloak-oidc-contract) above.

### `workflows_dag_deploy.env`

| Key | Description |
|---|---|
| `status` | `synced` |
| `dags_repo_url` | Git repository URL that was registered with the instance |

### `workflows_smoke.env`

| Key | Description |
|---|---|
| `status` | `passed` |

## Security

- `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` — embedded in `artifacts/infra/workflows_request_payload.json` (a JSON artifact written by the plan step) and sent to the STACKIT API at deploy time; never written to any `.env` state file or logged. Treat `workflows_request_payload.json` as a sensitive artifact and exclude it from version control.
- `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` — used for Keycloak OIDC client reconciliation; never written to any state file or logged.
- `STACKIT_WORKFLOWS_ADMIN_PASSWORD` — Keycloak admin credential used during reconciliation; never written to any state file.
- All `.env` state files (`artifacts/infra/workflows_*.env`) are validated by `test_contract.py` to confirm the absence of token and secret keys.

## Consumer Usage

Enable the module in your consumer `.env`:

```bash
WORKFLOWS_ENABLED=true
STACKIT_WORKFLOWS_DAGS_REPO_URL=https://github.com/your-org/your-dags-repo.git
STACKIT_WORKFLOWS_DAGS_REPO_BRANCH=main
STACKIT_WORKFLOWS_DAGS_REPO_USERNAME=git-user
STACKIT_WORKFLOWS_DAGS_REPO_TOKEN=<token>          # never commit this value
STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL=https://keycloak.your-domain.com/realms/your-realm/.well-known/openid-configuration
STACKIT_WORKFLOWS_OIDC_CLIENT_ID=airflow
STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET=<secret>      # never commit this value
STACKIT_OBSERVABILITY_INSTANCE_ID=<uuid>           # from the Observability module output
```

Then run the full provisioning lifecycle:

```bash
make infra-stackit-workflows-plan
make infra-stackit-workflows-apply
make infra-stackit-workflows-reconcile
make infra-stackit-workflows-dag-deploy
make infra-stackit-workflows-smoke
```

Read outputs from the state files:

```bash
source artifacts/infra/workflows_instance.env
echo "Airflow UI: $web_url"
echo "Instance ID: $instance_id"
```

## Local Lane

For local Docker Desktop Kubernetes deployment of Airflow without STACKIT cloud access, see the [Local Workflows module](../local-workflows/README.md) (`local-workflows`).

## Troubleshooting

**`log_fatal: WORKFLOWS_ENABLED guard`** — The module detected a non-STACKIT profile. Set `BLUEPRINT_PROFILE=stackit-<env>` or check your `.env` for the active profile.

**`log_fatal: STACKIT_WORKFLOWS_DAGS_REPO_URL must end with .git`** — The DAG repository URL is missing the `.git` suffix. Update `STACKIT_WORKFLOWS_DAGS_REPO_URL`.

**Apply exits with HTTP 409** — An instance with the same name already exists. This is handled automatically (idempotent); the script re-fetches the existing instance. If the state is stale, run `make infra-stackit-workflows-reconcile`.

**More than one active instance** — `make infra-stackit-workflows-reconcile` fails fast if > 1 instance exists without an explicit `STACKIT_WORKFLOWS_INSTANCE_ID` set. Set the env var to the target instance ID and re-run.

**DAG parse smoke fails** — Check that no files matching `*dag*.py` are placed under an `apps/` subdirectory in the DAG repository. Move them to the repository-root `dags/` directory.

**Smoke reports `health_status` not `Active`** — The instance may still be starting up. Wait 2–3 minutes and re-run `make infra-stackit-workflows-smoke`. If the status does not change, check the STACKIT console for provisioning errors.
