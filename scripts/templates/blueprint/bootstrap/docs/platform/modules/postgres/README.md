# Postgres Module (Optional)

## Purpose
Provision PostgreSQL and publish canonical connection contract for runtime consumers.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `POSTGRES_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `POSTGRES_ENABLED=true`.
- `stackit-*` profiles: Terraform module under `infra/cloud/stackit/terraform/modules/postgres`.
- `local-*` profiles: Helm chart (`bitnami/postgresql`) using `infra/local/helm/postgres/values.yaml`.

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
- Auto-align ACL with SKE egress ranges
- Merge explicit extra CIDRs if provided
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
