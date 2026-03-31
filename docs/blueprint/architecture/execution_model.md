# Execution Model (End-to-End)

This page is the single, practical explanation of how the blueprint executes provisioning and deployment across local and STACKIT environments.

## GitHub Template Onboarding
For repositories created via GitHub template:
1. Initialize repository identity:
   - Interactive wizard: `make blueprint-init-repo-interactive`
   - Env-file mode (CI-friendly): copy `blueprint/repo.init.secrets.example.env` to `blueprint/repo.init.secrets.env`, edit `blueprint/repo.init.env` + `blueprint/repo.init.secrets.env`, and run `make blueprint-init-repo`
   - First init also switches the contract from `template-source` to `generated-consumer`, replaces consumer-owned root docs/governance/CI seeds, and prunes disabled conditional optional scaffolding from the raw template copy.
   - `make blueprint-init-repo` creates or refreshes tracked non-sensitive defaults in `blueprint/repo.init.env` (including required non-sensitive module inputs for enabled modules), placeholder scaffolding in `blueprint/repo.init.secrets.example.env`, and local-sensitive defaults in `blueprint/repo.init.secrets.env` (including required sensitive module placeholders for enabled modules).
   - For existing generated repos, use `make blueprint-resync-consumer-seeds` to compare consumer-seeded files with latest templates before deciding what to refresh.
   - For full blueprint-managed drift upgrades, use `make blueprint-upgrade-consumer` (plan/apply) followed by `make blueprint-upgrade-consumer-validate`.
   - Reapply init-managed files only with `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`.
2. Run `make blueprint-bootstrap`.
3. Run `make infra-bootstrap`.
4. Run `make infra-validate`.

## Core Idea
The execution flow is always the same:
1. `infra-provision`
2. `infra-deploy`
3. `infra-smoke`

`infra-provision-deploy` runs those three in order.

## What Each Phase Does
### 1) Provision
- Validates contracts and repository structure.
- Chooses the provisioning driver from `BLUEPRINT_PROFILE`.
- For local profiles, bootstraps Crossplane baseline (`infra/local/crossplane` + Crossplane Helm chart) on the selected local Kubernetes context.
- For STACKIT profiles, runs layered Terraform:
  - `bootstrap` with remote S3 backend using pre-provisioned tfstate bucket/credentials.
  - `foundation` with remote S3 backend using the same bucket contract and a separate state key.
- Runs optional module provisioning when enabled:
  - provider-backed modules reconcile through `foundation`,
  - fallback modules run runtime/API contracts (for example module-specific ArgoCD Applications or Workflows API).
- Writes state artifacts to `artifacts/infra/provision.env`.

### 2) Deploy
- Bootstraps runtime core components (ArgoCD + External Secrets Operator) via Helm.
- Applies ArgoCD base + environment overlay.
- Bootstraps application catalog contract.
- Runs optional module deployment/reconciliation steps.
- Writes state artifacts to `artifacts/infra/deploy.env`.

### 3) Smoke
- Verifies baseline infra and app contracts.
- Verifies optional modules (if enabled).
- In live mode, captures pod inventory plus workload readiness for blueprint-managed namespaces only (`apps`, `data`, `messaging`, `network`, `security`, `observability`, `argocd`, `external-secrets`, `crossplane-system`, `envoy-gateway-system`).
- Writes state artifacts to `artifacts/infra/smoke.env`.

## Profile Routing
`BLUEPRINT_PROFILE` selects the execution path:

| Profile | Provisioning Path | Deployment Path |
|---|---|---|
| `local-full` | `infra/local/crossplane` + local Helm values | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/local` |
| `local-lite` | `infra/local/crossplane` + local Helm values | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/local` |
| `stackit-dev` | `infra/cloud/stackit/terraform/bootstrap` + `infra/cloud/stackit/terraform/foundation` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/dev` |
| `stackit-stage` | `infra/cloud/stackit/terraform/bootstrap` + `infra/cloud/stackit/terraform/foundation` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/stage` |
| `stackit-prod` | `infra/cloud/stackit/terraform/bootstrap` + `infra/cloud/stackit/terraform/foundation` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/prod` |

Local context routing:
- Workstation execution prefers the `docker-desktop` Kubernetes context when it exists.
- CI prefers `kind-*` contexts, with `kind-blueprint-e2e` as the canonical default when available.
- Set `LOCAL_KUBE_CONTEXT` to override the local default explicitly.
- Run `make infra-context` to see the resolved context and selection source before live execution.

## Optional Modules
Optional modules are controlled by canonical flags:
- `OBSERVABILITY_ENABLED`
- `WORKFLOWS_ENABLED`
- `LANGFUSE_ENABLED`
- `POSTGRES_ENABLED`
- `NEO4J_ENABLED`
- `OBJECT_STORAGE_ENABLED`
- `RABBITMQ_ENABLED`
- `DNS_ENABLED`
- `PUBLIC_ENDPOINTS_ENABLED`
- `SECRETS_MANAGER_ENABLED`
- `KMS_ENABLED`
- `IDENTITY_AWARE_PROXY_ENABLED`

If a flag is `true`, the module plan/apply/deploy/smoke scripts run and persist their own artifacts under `artifacts/infra/`.
`blueprint-render-makefile` (or `blueprint-bootstrap`) materializes optional-module Make targets when the corresponding module flag is enabled.
`make blueprint-init-repo` prunes disabled conditional optional-module scaffolding from fresh generated repos so the initial working tree is lean.
In generated repos, `blueprint-bootstrap` does not recreate consumer-seeded files and `infra-bootstrap` does not recreate init-managed identity files.
Use `make blueprint-resync-consumer-seeds` for consumer-seeded files, `make blueprint-upgrade-consumer` for blueprint-managed file drift, and forced init (`BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`) for init-managed identity files.
`infra-bootstrap` materializes optional-module infra scaffolding when enabled and preserves already-materialized disabled-module scaffolding so later flag toggles cannot silently delete tracked repo content.
`infra-destroy-disabled-modules` runs module destroy actions for modules currently disabled by flags when resources may already exist.

Examples:
- `WORKFLOWS_ENABLED=true` creates `dags/` scaffolding and Workflows API payload/runtime artifacts in generated repos.
- `LANGFUSE_ENABLED=true` and `NEO4J_ENABLED=true` materialize optional GitOps manifests under `infra/gitops/argocd/optional/${ENV}/`.
- `RABBITMQ_ENABLED=true`, `PUBLIC_ENDPOINTS_ENABLED=true`, and `IDENTITY_AWARE_PROXY_ENABLED=true` materialize module-specific ArgoCD `Application` manifests under `infra/gitops/argocd/optional/${ENV}/`.
- `POSTGRES_ENABLED=true`, `OBJECT_STORAGE_ENABLED=true`, `DNS_ENABLED=true`, `SECRETS_MANAGER_ENABLED=true`, and `OBSERVABILITY_ENABLED=true` are reconciled by the STACKIT `foundation` Terraform layer.

## Make and Script Ownership
- `Makefile` is a blueprint-managed loader.
- blueprint-managed targets are rendered into `make/blueprint.generated.mk`.
- platform-owned targets live in `make/platform.mk` and `make/platform/*.mk` (seeded if missing, then editable).
- platform-owned scripts live in `scripts/bin/platform/**` and `scripts/lib/platform/**`.

## Observability Module Behavior
- `OBSERVABILITY_ENABLED=false` by default.
- When enabled, observability runs as a standard optional module with:
  - `infra-observability-plan`
  - `infra-observability-apply`
  - `infra-observability-deploy`
  - `infra-observability-smoke`
- OTEL/Faro runtime contract values are materialized and consumed by app configuration (`apps/catalog/manifest.yaml`).

## Dry-Run vs Live Execution
`DRY_RUN` controls whether cloud/cluster tools are executed:

- `true` (default): dry-run mode.
  - Scripts validate contracts, resolve paths, and produce artifacts.
  - No real `terraform`, `kubectl`, or `helm` side effects.
- `false`: live mode.
  - Real commands are executed against your configured environment.

## Where To Look When Something Fails
Start with:
- `artifacts/infra/provision.env`
- `artifacts/infra/deploy.env`
- `artifacts/infra/smoke.env`
- `artifacts/infra/workload_health.json`
- `artifacts/infra/workload_pods.json`
- `artifacts/infra/local_crossplane_bootstrap.env`
- `artifacts/infra/core_runtime_bootstrap.env`
- `artifacts/infra/core_runtime_smoke.env`
- `artifacts/apps/apps_bootstrap.env`
- `artifacts/apps/apps_smoke.env`
- `artifacts/docs/docs_build.env`
- `artifacts/docs/docs_smoke.env`

Then inspect module-specific artifacts, for example:
- `artifacts/infra/workflows_*.env`
- `artifacts/infra/langfuse_*.env`
- `artifacts/infra/postgres_*.env`
- `artifacts/infra/neo4j_*.env`

These files include selected driver, selected path, and key contract outputs.

`make infra-runtime-inventory` prints export-ready runtime hints for the active profile.
- local profiles can call `make infra-local-runtime-inventory` directly.
- stackit profiles can call `make infra-stackit-runtime-inventory` directly.
Sensitive values are redacted by default; set `LOCAL_RUNTIME_INVENTORY_INCLUDE_SENSITIVE=true` (local) or `STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE=true` (stackit) to print them.

Cleanup:
- `make infra-local-destroy-all` removes blueprint-managed resources from the selected local cluster and preserves the cluster itself.
- `make infra-stackit-destroy-all` tears down the canonical STACKIT bootstrap/foundation chain.

## Most Common Command Patterns
Dry-run local:

```bash
BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make infra-provision-deploy
```

Live local:

```bash
export DRY_RUN=false
export BLUEPRINT_PROFILE=local-full
export OBSERVABILITY_ENABLED=true
make infra-context
make infra-provision-deploy
```

Live STACKIT dev:

```bash
export DRY_RUN=false
export BLUEPRINT_PROFILE=stackit-dev
export OBSERVABILITY_ENABLED=true
make infra-provision-deploy
```

## Contract and Governance References
- Platform contract: `blueprint/contract.yaml`
- Governance: `AGENTS.md`
- Module contracts: `blueprint/modules/*/module.contract.yaml`
