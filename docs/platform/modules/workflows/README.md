# Workflows Module (Optional)

## Purpose
Provision and reconcile STACKIT Workflows (managed Airflow) and deploy DAGs.

## Stack Execution Model
- Supported only on `stackit-*` profiles.
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `WORKFLOWS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `WORKFLOWS_ENABLED=true`.
- Provisioning/reconciliation uses STACKIT Workflows API contract:
  - `POST /projects/{projectId}/regions/{region}/instances`
  - plus wrapper reconciliation in `scripts/bin/infra/stackit_workflows_*.sh`
- API payload/state artifacts are generated under:
  - `artifacts/infra/workflows_*.env`

## Enable
Set:

```bash
export WORKFLOWS_ENABLED=true
```

## Required Inputs
- `STACKIT_PROJECT_ID`
- `STACKIT_REGION`
- `STACKIT_WORKFLOWS_DAGS_REPO_URL` (must end with `.git`)
- `STACKIT_WORKFLOWS_DAGS_REPO_BRANCH`
- `STACKIT_WORKFLOWS_DAGS_REPO_USERNAME`
- `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN`
- `STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL`
- `STACKIT_WORKFLOWS_OIDC_CLIENT_ID`
- `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET`
- `STACKIT_OBSERVABILITY_INSTANCE_ID`

## Reconciliation Rules
- If one active instance exists, reconcile it.
- If none exists, create a new one.
- If more than one exists and no explicit instance is set, fail fast.

## Keycloak Contract
- Confidential client
- Standard flow enabled
- Direct access grants enabled
- Realm roles: `Admin`, `User`, `Viewer`, `Op`
- Roles mapper claim must be `roles` in ID token, access token, and userinfo.

## Commands
- `make infra-stackit-workflows-plan`
- `make infra-stackit-workflows-apply`
- `make infra-stackit-workflows-reconcile`
- `make infra-stackit-workflows-dag-deploy`
- `make infra-stackit-workflows-dag-parse-smoke`
- `make infra-stackit-workflows-smoke`
- `make infra-stackit-workflows-destroy`

## Smoke Expectations
- Instance is `Active`
- OIDC login works
- DAG parsing has no import errors
- Expected DAGs are visible

## Outputs
- `STACKIT_WORKFLOWS_INSTANCE_ID`
- `STACKIT_WORKFLOWS_INSTANCE_NAME`
- `STACKIT_WORKFLOWS_INSTANCE_FQDN`
- `STACKIT_WORKFLOWS_WEB_URL`
