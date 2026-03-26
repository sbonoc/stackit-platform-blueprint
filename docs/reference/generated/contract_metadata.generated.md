# Contract Metadata (Generated)

- Generated at: `2026-03-26T11:43:05Z`
- Contract name: `stackit-k8s-reusable-blueprint`
- Contract version: `1.0.0`

## Supported Profiles
- `local-full`
- `local-lite`
- `stackit-dev`
- `stackit-stage`
- `stackit-prod`

## Required Make Targets
- `help`
- `blueprint-init-repo`
- `blueprint-init-repo-interactive`
- `blueprint-check-placeholders`
- `blueprint-template-smoke`
- `blueprint-release-notes`
- `blueprint-migrate`
- `blueprint-bootstrap`
- `blueprint-clean-generated`
- `blueprint-render-makefile`
- `blueprint-render-module-wrapper-skeletons`
- `quality-hooks-run`
- `infra-prereqs`
- `infra-help-reference`
- `infra-bootstrap`
- `infra-validate`
- `infra-smoke`
- `infra-provision`
- `infra-deploy`
- `infra-provision-deploy`
- `infra-stackit-bootstrap-preflight`
- `infra-stackit-bootstrap-plan`
- `infra-stackit-bootstrap-apply`
- `infra-stackit-bootstrap-destroy`
- `infra-stackit-foundation-preflight`
- `infra-stackit-foundation-plan`
- `infra-stackit-foundation-apply`
- `infra-stackit-foundation-destroy`
- `infra-stackit-foundation-fetch-kubeconfig`
- `infra-stackit-foundation-refresh-kubeconfig`
- `infra-stackit-ci-github-setup`
- `infra-stackit-destroy-all`
- `infra-stackit-runtime-prerequisites`
- `infra-stackit-runtime-inventory`
- `infra-stackit-runtime-deploy`
- `infra-stackit-smoke-foundation`
- `infra-stackit-smoke-runtime`
- `infra-stackit-provision-deploy`
- `infra-argocd-topology-render`
- `infra-argocd-topology-validate`
- `infra-doctor`
- `infra-context`
- `infra-status`
- `infra-status-json`
- `infra-audit-version`
- `infra-audit-version-cached`
- `apps-bootstrap`
- `apps-smoke`
- `apps-audit-versions`
- `apps-audit-versions-cached`
- `apps-publish-ghcr`
- `backend-test-unit`
- `backend-test-integration`
- `backend-test-contracts`
- `backend-test-e2e`
- `touchpoints-test-unit`
- `touchpoints-test-integration`
- `touchpoints-test-contracts`
- `touchpoints-test-e2e`
- `test-unit-all`
- `test-integration-all`
- `test-contracts-all`
- `test-e2e-all-local`
- `docs-install`
- `docs-run`
- `docs-build`
- `docs-smoke`

## Optional Modules
| Module | Enabled by default | Enable flag | Contract path |
|---|---:|---|---|
| `langfuse` | `false` | `LANGFUSE_ENABLED` | `blueprint/modules/langfuse/module.contract.yaml` |
| `neo4j` | `false` | `NEO4J_ENABLED` | `blueprint/modules/neo4j/module.contract.yaml` |
| `observability` | `false` | `OBSERVABILITY_ENABLED` | `blueprint/modules/observability/module.contract.yaml` |
| `postgres` | `false` | `POSTGRES_ENABLED` | `blueprint/modules/postgres/module.contract.yaml` |
| `workflows` | `false` | `WORKFLOWS_ENABLED` | `blueprint/modules/workflows/module.contract.yaml` |

## Module: `langfuse`

- Purpose: Deploy Langfuse with OIDC authentication and LLM observability wiring.
- Enabled by default: `false`
- Enable flag: `LANGFUSE_ENABLED`

### Required Environment Variables
- `LANGFUSE_PUBLIC_DOMAIN`
- `LANGFUSE_OIDC_ISSUER_URL`
- `LANGFUSE_OIDC_CLIENT_ID`
- `LANGFUSE_OIDC_CLIENT_SECRET`
- `LANGFUSE_DATABASE_URL`
- `LANGFUSE_SALT`
- `LANGFUSE_ENCRYPTION_KEY`
- `LANGFUSE_NEXTAUTH_SECRET`

### Make Targets
- `infra-langfuse-plan`
- `infra-langfuse-apply`
- `infra-langfuse-deploy`
- `infra-langfuse-smoke`
- `infra-langfuse-destroy`

### Produced Outputs
- `LANGFUSE_PUBLIC_URL`
- `LANGFUSE_HEALTH_STATUS`

## Module: `neo4j`

- Purpose: Deploy Neo4j graph database and publish canonical runtime connection contract.
- Enabled by default: `false`
- Enable flag: `NEO4J_ENABLED`

### Required Environment Variables
- `NEO4J_AUTH_USERNAME`
- `NEO4J_AUTH_PASSWORD`

### Make Targets
- `infra-neo4j-plan`
- `infra-neo4j-apply`
- `infra-neo4j-deploy`
- `infra-neo4j-smoke`
- `infra-neo4j-destroy`

### Produced Outputs
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

## Module: `observability`

- Purpose: Provision and deploy observability stack plus OTEL/Faro runtime wiring for all components.
- Enabled by default: `false`
- Enable flag: `OBSERVABILITY_ENABLED`

### Required Environment Variables

### Make Targets
- `infra-observability-plan`
- `infra-observability-apply`
- `infra-observability-deploy`
- `infra-observability-smoke`
- `infra-observability-destroy`

### Produced Outputs
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_PROTOCOL`
- `OTEL_TRACES_ENABLED`
- `OTEL_METRICS_ENABLED`
- `OTEL_LOGS_ENABLED`
- `FARO_ENABLED`
- `FARO_COLLECT_PATH`
- `STACKIT_OBSERVABILITY_INSTANCE_ID`
- `STACKIT_OBSERVABILITY_GRAFANA_URL`

## Module: `postgres`

- Purpose: Provision PostgreSQL and expose canonical DSN/credentials for runtime consumers.
- Enabled by default: `false`
- Enable flag: `POSTGRES_ENABLED`

### Required Environment Variables
- `POSTGRES_INSTANCE_NAME`
- `POSTGRES_DB_NAME`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

### Make Targets
- `infra-postgres-plan`
- `infra-postgres-apply`
- `infra-postgres-smoke`
- `infra-postgres-destroy`

### Produced Outputs
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DSN`

## Module: `workflows`

- Purpose: Provision and reconcile STACKIT Workflows (managed Airflow) and deploy DAGs.
- Enabled by default: `false`
- Enable flag: `WORKFLOWS_ENABLED`

### Required Environment Variables
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

### Make Targets
- `infra-stackit-workflows-plan`
- `infra-stackit-workflows-apply`
- `infra-stackit-workflows-reconcile`
- `infra-stackit-workflows-dag-deploy`
- `infra-stackit-workflows-dag-parse-smoke`
- `infra-stackit-workflows-smoke`
- `infra-stackit-workflows-destroy`

### Produced Outputs
- `STACKIT_WORKFLOWS_INSTANCE_ID`
- `STACKIT_WORKFLOWS_INSTANCE_NAME`
- `STACKIT_WORKFLOWS_INSTANCE_FQDN`
- `STACKIT_WORKFLOWS_WEB_URL`
- `STACKIT_WORKFLOWS_HEALTH_STATUS`
