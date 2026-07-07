# Postgres Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision PostgreSQL and expose canonical DSN/credentials for runtime consumers.
- Enable flag: `POSTGRES_ENABLED` (default: `false`)
- Required inputs:
  - `POSTGRES_DB_NAME`
  - `POSTGRES_USER`
- Make targets:
  - `infra-postgres-plan`
  - `infra-postgres-apply`
  - `infra-postgres-smoke`
  - `infra-postgres-destroy`
- Outputs:
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_DB_NAME`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_DSN`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `POSTGRES_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `POSTGRES_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `POSTGRES_ENABLED` contract flag.
  - Required inputs `POSTGRES_DB_NAME` and `POSTGRES_USER` are passed through to the foundation layer. `POSTGRES_INSTANCE_NAME` is optional (v1.12.2+); Terraform derives a unique per-environment name from `naming_prefix` when unset. `POSTGRES_EXTRA_ALLOWED_CIDRS` is optional and defaults to empty.
  - `POSTGRES_VERSION` defaults to `17` across local and STACKIT paths, and can be overridden explicitly when provider support changes.
  - Runtime artifacts resolve provider-generated host/port/password outputs after apply; dry-run mode keeps deterministic placeholders.
- `local-*` profiles: Helm chart (`bitnami/postgresql`) using `infra/local/helm/postgres/values.yaml`.
- Local chart/image pins stay on the latest stable Bitnami chart carrying the PostgreSQL `17` line so the in-cluster fallback stays aligned with the current STACKIT managed-service major version.
  - The pinned fallback image uses `docker.io/bitnamilegacy/postgresql`; despite the registry namespace, the pinned tag stays on the latest stable supported PostgreSQL `17` image line while remaining multi-arch for both amd64 CI nodes and arm64 Docker Desktop clusters. When `bitnamilegacy` retires old major-version tags, bump `POSTGRES_LOCAL_IMAGE_TAG` in `versions.baseline.sh`, `versions.sh`, and `infra/local/helm/postgres/values.yaml` to the latest `17.x.x-debian-12-rN` tag that passes `make infra-audit-version`.
  - `fullnameOverride` is pinned to the Helm release name so the local service host matches the published runtime contract exactly.

## ACL Policy
- Derive the base allowlist from SKE egress ranges when `ske_enabled=true`
- Merge `POSTGRES_EXTRA_ALLOWED_CIDRS` with the SKE-derived ranges when provided
- If `ske_enabled=false`, explicit extra CIDRs are required
- No open-world default (`0.0.0.0/0` forbidden by default)

## Credentials

Credentials are delivered via a Kubernetes Secret named `blueprint-postgres-auth` (Secret key: `password`). No plaintext credentials appear in rendered Helm values or bootstrap templates.

**Local lane apply flow:**
1. `postgres_reconcile_runtime_secret` creates or updates Secret `blueprint-postgres-auth` in namespace `data` with the value of `POSTGRES_PASSWORD` before the Helm upgrade runs. `POSTGRES_PASSWORD` is required on local profiles; on STACKIT profiles it is provider-generated and not an input (v1.12.2+).
2. The Bitnami postgresql chart mounts the Secret via `auth.existingSecret: blueprint-postgres-auth`.
3. `postgres_delete_runtime_secret` removes the Secret on destroy.

**STACKIT lane:** credentials are provider-generated; no pre-provisioned Secret is required.

## Standalone STACKIT Terraform Module

A standalone Terraform module is available at `infra/cloud/stackit/terraform/modules/postgres/` for isolated PostgreSQL Flex provisioning outside the foundation deployment pattern.

Resources declared: `stackit_postgresflex_instance`, `stackit_postgresflex_user`, `stackit_postgresflex_database`.

Key variables:

| Variable | Description | Default |
|---|---|---|
| `stackit_project_id` | STACKIT project ID | required |
| `postgres_instance_name` | Instance name | required |
| `postgres_db_name` | Database name | `app` |
| `postgres_username` | Runtime username | `app` |
| `postgres_version` | PostgreSQL major version | `17` |
| `postgres_replicas` | Replica count | `1` |
| `postgres_acl` | CIDR allowlist (non-empty or `ske_enabled=true`) | `[]` |

Key outputs: `postgres_host`, `postgres_port`, `postgres_username`, `postgres_password`, `postgres_database`.

Validate: `terraform validate` from `infra/cloud/stackit/terraform/modules/postgres/`.

## Runtime State

Apply writes `artifacts/infra/postgres_runtime.env` with all six contract output keys:

| Key | Description |
|---|---|
| `host` | PostgreSQL service host |
| `port` | PostgreSQL service port |
| `db_name` | Database name |
| `user` | Runtime username |
| `password` | Runtime password |
| `dsn` | `postgresql://user:password@host:port/db_name` |

State file keys follow the strict prefix-strip convention: `POSTGRES_DB_NAME` → `db_name`, `POSTGRES_USER` → `user`. Consumers reading `artifacts/infra/postgres_runtime.env` directly must use the stripped key names. Consumers using ESO-synced env vars (`POSTGRES_DB_NAME`, `POSTGRES_USER`) are unaffected.

## Smoke Checks

`make infra-postgres-smoke` validates the runtime state file. Checks performed:

- `dsn` starts with `postgresql://`
- `host` is non-empty
- `port` is non-empty
- `db_name` is non-empty
- `POSTGRES_CONNECT_TIMEOUT_SECONDS` is numeric

Smoke writes `artifacts/infra/postgres_smoke.env` with `status=passed` on success.

## Destroy

`make infra-postgres-destroy` removes the Helm release (local lane) or delegates to the foundation Terraform layer (STACKIT lane) and removes all runtime state files.

**Local lane destroy sequence:**
1. `run_helm_uninstall` (idempotent — tolerates missing release via `--ignore-not-found`)
2. `postgres_delete_runtime_secret` (idempotent — tolerates missing Secret)
3. `remove_state_files_by_prefix postgres_`

Re-running destroy when resources are already absent exits 0.
