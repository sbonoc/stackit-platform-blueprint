# OpenSearch Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed OpenSearch and expose canonical endpoint/credentials for runtime consumers.
- Enable flag: `OPENSEARCH_ENABLED` (default: `false`)
- Required inputs:
  - `OPENSEARCH_INSTANCE_NAME`
  - `OPENSEARCH_VERSION`
  - `OPENSEARCH_PLAN_NAME`
- Make targets:
  - `infra-opensearch-plan`
  - `infra-opensearch-apply`
  - `infra-opensearch-smoke`
  - `infra-opensearch-destroy`
- Outputs:
  - `OPENSEARCH_HOST`
  - `OPENSEARCH_HOSTS`
  - `OPENSEARCH_PORT`
  - `OPENSEARCH_SCHEME`
  - `OPENSEARCH_URI`
  - `OPENSEARCH_DASHBOARD_URL`
  - `OPENSEARCH_USERNAME`
  - `OPENSEARCH_PASSWORD`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OPENSEARCH_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `OPENSEARCH_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `OPENSEARCH_ENABLED` contract flag.
  - Required contract inputs are passed through to foundation (`OPENSEARCH_INSTANCE_NAME`, `OPENSEARCH_VERSION`, `OPENSEARCH_PLAN_NAME`).
  - Runtime artifacts resolve provider-generated host/credential outputs after apply; dry-run mode keeps deterministic placeholders.
- `local-*` profiles: no managed OpenSearch counterpart; module plan/apply is a no-op contract stub.
