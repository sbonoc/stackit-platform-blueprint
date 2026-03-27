# Postgres Module (Optional)

## Purpose
Provision PostgreSQL and publish canonical connection contract for runtime consumers.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `POSTGRES_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `POSTGRES_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `POSTGRES_ENABLED` contract flag.
  - Canonical inputs `POSTGRES_INSTANCE_NAME`, `POSTGRES_DB_NAME`, `POSTGRES_USER`, and `POSTGRES_EXTRA_ALLOWED_CIDRS` are passed through to the foundation layer.
  - `POSTGRES_VERSION` defaults to `16` across local and STACKIT paths, and can be overridden explicitly when provider support changes.
  - Runtime artifacts resolve provider-generated host/port/password outputs after apply; dry-run mode keeps deterministic placeholders.
- `local-*` profiles: Helm chart (`bitnami/postgresql`) using `infra/local/helm/postgres/values.yaml`.
  - Local chart/image pins stay on the latest stable Bitnami chart carrying the PostgreSQL `16` line so the in-cluster fallback remains aligned with the current STACKIT managed-service major version.
  - The pinned fallback image uses `docker.io/bitnamilegacy/postgresql` so the same version contract works on both amd64 CI nodes and arm64 Docker Desktop clusters.
  - `fullnameOverride` is pinned to the Helm release name so the local service host matches the published runtime contract exactly.

## Enable
Set:

```bash
export POSTGRES_ENABLED=true
```

## Required Inputs
- `POSTGRES_INSTANCE_NAME`
- `POSTGRES_DB_NAME`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

## ACL Policy
- Derive the base allowlist from SKE egress ranges when `ske_enabled=true`
- Merge `POSTGRES_EXTRA_ALLOWED_CIDRS` with the SKE-derived ranges when provided
- If `ske_enabled=false`, explicit extra CIDRs are required
- No open-world default (`0.0.0.0/0` forbidden by default)

## Commands
- `make infra-postgres-plan`
- `make infra-postgres-apply`
- `make infra-postgres-smoke`
- `make infra-postgres-destroy`

## Outputs
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DSN`
