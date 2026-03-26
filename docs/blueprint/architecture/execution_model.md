# Execution Model (End-to-End)

This page is the single, practical explanation of how the blueprint executes provisioning and deployment across local and STACKIT environments.

## GitHub Template Onboarding
For repositories created via GitHub template:
1. Initialize repository identity:
   - Interactive wizard: `make blueprint-init-repo-interactive`
   - Env-file mode (CI-friendly): fill `blueprint/repo.init.example.env` and run `make blueprint-init-repo`
2. Run `make blueprint-bootstrap`.
3. Run `make infra-bootstrap`.
4. Run `make infra-validate`.

For template upgrades:
1. Run `make blueprint-migrate`.
2. Re-run validation bundles (`quality-hooks-run`, `infra-validate`, `infra-smoke`).

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
- Runs optional module provisioning when enabled.
- Writes state artifacts to `artifacts/infra/provision.env`.

### 2) Deploy
- Applies ArgoCD base + environment overlay.
- Bootstraps application catalog contract.
- Runs optional module deployment/reconciliation steps.
- Writes state artifacts to `artifacts/infra/deploy.env`.

### 3) Smoke
- Verifies baseline infra and app contracts.
- Verifies optional modules (if enabled).
- Writes state artifacts to `artifacts/infra/smoke.env`.

## Profile Routing
`BLUEPRINT_PROFILE` selects the execution path:

| Profile | Provisioning Path | Deployment Path |
|---|---|---|
| `local-full` | `infra/local/crossplane` + local Helm values | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/local` |
| `local-lite` | `infra/local/crossplane` + local Helm values | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/local` |
| `stackit-dev` | `infra/cloud/stackit/terraform/environments/dev` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/dev` |
| `stackit-stage` | `infra/cloud/stackit/terraform/environments/stage` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/stage` |
| `stackit-prod` | `infra/cloud/stackit/terraform/environments/prod` | `infra/gitops/argocd/base` + `infra/gitops/argocd/overlays/prod` |

## Optional Modules
Optional modules are controlled by canonical flags:
- `OBSERVABILITY_ENABLED`
- `WORKFLOWS_ENABLED`
- `LANGFUSE_ENABLED`
- `POSTGRES_ENABLED`
- `NEO4J_ENABLED`

If a flag is `true`, the module plan/apply/deploy/smoke scripts run and persist their own artifacts under `artifacts/infra/`.
`blueprint-render-makefile` (or `blueprint-bootstrap`) materializes optional-module Make targets when the corresponding module flag is enabled.
`infra-bootstrap` materializes optional-module infra scaffolding when enabled and prunes stale scaffolding when flags are switched back to `false`.

Examples:
- `WORKFLOWS_ENABLED=true` creates `dags/`, Workflows Terraform scaffold, and optional GitOps manifests.
- `LANGFUSE_ENABLED=true`, `POSTGRES_ENABLED=true`, and `NEO4J_ENABLED=true` create their module-specific Terraform/Helm/test scaffolding and optional manifests.

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

`make infra-stackit-runtime-inventory` also prints export-ready runtime hints.
Sensitive values are redacted by default; set `STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE=true` to print them.

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
