# Consumer Quickstart

This page is the canonical onboarding path for repositories generated from this GitHub template.
If you want a faster onboarding checklist first, use [First 30 Minutes](first_30_minutes.md).

## 1) Create Repository
1. Click **Use this template** in GitHub.
2. Select owner/name and create your repository.
3. Clone the generated repository locally.

## 2) Initialize Repository Identity
Interactive wizard:
```bash
make blueprint-init-repo-interactive
```

Non-interactive (env-file) mode:
```bash
cp blueprint/repo.init.secrets.example.env blueprint/repo.init.secrets.env
${EDITOR:-vi} blueprint/repo.init.env blueprint/repo.init.secrets.env
make blueprint-init-repo
```

Minimum required variables for env-file mode:
- `BLUEPRINT_REPO_NAME`
- `BLUEPRINT_GITHUB_ORG`
- `BLUEPRINT_GITHUB_REPO`
- `BLUEPRINT_DEFAULT_BRANCH`
- `BLUEPRINT_STACKIT_REGION`
- `BLUEPRINT_STACKIT_TENANT_SLUG`
- `BLUEPRINT_STACKIT_PLATFORM_SLUG`
- `BLUEPRINT_STACKIT_PROJECT_ID`
- `BLUEPRINT_STACKIT_TFSTATE_BUCKET`
- `BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX`

`make blueprint-init-repo` creates or refreshes tracked defaults in `blueprint/repo.init.env`
and local-sensitive defaults in `blueprint/repo.init.secrets.env` (scaffolded from `blueprint/repo.init.secrets.example.env`).
When optional modules are enabled, required non-sensitive module inputs are seeded in `blueprint/repo.init.env`,
while required sensitive module inputs are scaffolded in the secrets files with non-empty placeholders.
Later `make blueprint-check-placeholders` and infra targets auto-load both files when present.
Infra targets run `blueprint-check-placeholders` first, so missing required inputs fail fast before mutable operations.
After first init, re-apply init-owned files only with `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`.
For existing generated repos that need template seed updates, start with:
```bash
make blueprint-resync-consumer-seeds
```
Then apply only safe updates when appropriate:
```bash
BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
```
For full blueprint-managed upgrades on existing generated repos (non-destructive plan/apply workflow):
```bash
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer-preflight
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer
make blueprint-upgrade-consumer-validate
make blueprint-upgrade-consumer-postcheck
```
Use the preflight report `artifacts/blueprint/upgrade_preflight.json` to inspect auto-apply candidates,
manual-merge/conflict paths, required follow-up commands, and missing contract-required consumer-owned Make targets before apply mode.
Inspect `artifacts/blueprint/upgrade_plan.json`, `artifacts/blueprint/upgrade_apply.json`, and
`artifacts/blueprint/upgrade_summary.md` after each run. Inspect
`artifacts/blueprint/upgrade/upgrade_reconcile_report.json` for blocking buckets.
When `required_manual_actions` is non-empty,
resolve the listed dependency paths first, then re-run `make blueprint-upgrade-consumer-validate`.
When postcheck reports status `failure`, resolve blocked reasons and re-run `make blueprint-upgrade-consumer-postcheck`.
For missing required consumer-owned Make targets, define the target in `make/platform.mk` or linked includes under `make/platform/*.mk`
using the exact target name from the manual-action reason.
When `LOCAL_POST_DEPLOY_HOOK_ENABLED=true`, preflight also flags a blocking manual action if
`infra-post-deploy-consumer` is still placeholder in `make/platform.mk`.
Set `BLUEPRINT_UPGRADE_SOURCE` when the blueprint source repository differs from your default `origin` remote.
By default, the upgrade target resolves `BLUEPRINT_UPGRADE_SOURCE` from `remote.upstream.url`
when present, and falls back to `remote.origin.url`.
To install/sync all bundled Codex skills into your local Codex skills directory:
```bash
make blueprint-install-codex-skills
```
Install only the upgrade skill when needed:
```bash
make blueprint-install-codex-skill
```
Install only the consumer operations skill when needed:
```bash
make blueprint-install-codex-skill-consumer-ops
```
Override install location when needed:
```bash
BLUEPRINT_CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills" make blueprint-install-codex-skill
BLUEPRINT_CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills" make blueprint-install-codex-skill-consumer-ops
```
Install SDD-specialized skills when needed:
```bash
make blueprint-install-codex-skill-sdd-intake-decompose
make blueprint-install-codex-skill-sdd-clarification-gate
make blueprint-install-codex-skill-sdd-plan-slicer
make blueprint-install-codex-skill-sdd-traceability-keeper
make blueprint-install-codex-skill-sdd-document-sync
make blueprint-install-codex-skill-sdd-pr-packager
```

## 3) Start Spec-Driven Work Item Before Implementation
Create a work-item folder first:
```bash
make spec-scaffold SPEC_SLUG=<work-item-slug>
```

Then enforce the readiness gate before writing implementation code:
- complete `Discover`, `High-Level Architecture`, `Specify`, and `Plan` in `specs/<YYYY-MM-DD>-<work-item-slug>/`
- if requirements are incomplete, record `BLOCKED_MISSING_INPUTS` and keep `SPEC_READY=false`
- map applicable `SDD-C-###` controls from `.spec-kit/control-catalog.md` in `spec.md`
- use `Managed service preference: stackit-managed-first` by default for `stackit-*` runtime capabilities; if you choose an alternative, record `explicit-consumer-exception` with rationale and approved ADR/decision-log entry
- start implementation only after `spec.md` records `SPEC_READY=true`

Before closing the work item, run `Document` and `Publish` phases:
- update affected `docs/platform/**`
- run `make docs-build` and `make docs-smoke`
- run `make quality-sdd-check-all`
- run `make quality-hardening-review`
- run `make spec-pr-context`

## 4) Bootstrap and Validate
```bash
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
```

## 5) Optional Consumer Smoke
```bash
make blueprint-template-smoke
```

`make blueprint-template-smoke` respects exported `BLUEPRINT_PROFILE` and optional-module flags, so you can dry-run the exact generated-repo scenario you want to validate before provisioning live infrastructure.

### App Catalog/Test-Lane Scaffold (Opt-In)
`APP_CATALOG_SCAFFOLD_ENABLED` is disabled by default so minimal generated repos are not forced into a multi-app catalog layout.

Enable it when you want the canonical app contract (`apps/catalog/manifest.yaml` + `apps/catalog/versions.lock`) and the test-lane baseline to stay synchronized:
```bash
APP_CATALOG_SCAFFOLD_ENABLED=true make apps-bootstrap
APP_CATALOG_SCAFFOLD_ENABLED=true make apps-smoke
```

Keep these surfaces synchronized after changes:
- `apps/catalog/manifest.yaml` (topology + runtime/framework pin contract)
- `apps/catalog/versions.lock` (script-friendly pin mirror)
- app test lanes in `make/platform.mk` (`backend-*`, `touchpoints-*`, and aggregate `test-*-all` targets)
- onboarding/target baseline in [App Onboarding Contract](app_onboarding.md)

### App Runtime GitOps Scaffold (Enabled by Default)
`APP_RUNTIME_GITOPS_ENABLED` defaults to `true` and keeps the baseline app runtime workload path active under:
- `infra/gitops/platform/base/apps/kustomization.yaml`
- `infra/gitops/platform/base/apps/backend-api-*.yaml`
- `infra/gitops/platform/base/apps/touchpoints-web-*.yaml`

Validate scaffold and runtime-path wiring:
```bash
APP_RUNTIME_GITOPS_ENABLED=true make infra-bootstrap
APP_RUNTIME_GITOPS_ENABLED=true make infra-validate
```

In execute mode (`DRY_RUN=false`), runtime smoke guardrails also assert live workload presence:
- `APP_RUNTIME_MIN_WORKLOADS` controls the minimum expected `Deployment`/`StatefulSet` count in namespace `apps` (default `1`).
- `make apps-smoke` performs the live check directly.
- The `infra-smoke` wrapper records the same assertion and emits explicit empty-runtime diagnostics in `artifacts/infra/smoke_diagnostics.json`.

When app catalog scaffold is also enabled, `apps/catalog/manifest.yaml` includes:
- `deliveryTopology` for baseline workload/service mapping
- `runtimeDeliveryContract` with canonical GitOps manifest paths and default image contract values

To replace scaffold defaults with real runtime images and wiring:
1. Publish images (`make apps-publish-ghcr`).
2. Update `apps/catalog/manifest.yaml` (`runtimeDeliveryContract.gitopsWorkloads[*].defaultImage`) and mirror those image refs in `infra/gitops/platform/base/apps/*deployment.yaml`.
3. Add app env/secret references in deployment manifests (`env`, `envFrom`, secret/configMap refs) using your runtime credential contract outputs.
4. Reconcile runtime (`make infra-deploy` or Argo sync of `platform-<env>-core`).

## 6) Continue with Delivery Flow
```bash
make infra-context
make infra-provision-deploy
make auth-reconcile-runtime-identity
make infra-status-json
```

`make infra-provision-deploy` already runs the canonical smoke stage and writes
`artifacts/infra/smoke_result.json`, `artifacts/infra/smoke_diagnostics.json`, and `artifacts/infra/workload_health.json`.
For local profiles, it also supports an optional post-deploy hook contract:
- set `LOCAL_POST_DEPLOY_HOOK_ENABLED=true` to invoke a consumer-owned hook command after successful smoke.
- default command is `LOCAL_POST_DEPLOY_HOOK_CMD='make -C "$ROOT_DIR" infra-post-deploy-consumer'`.
- set `LOCAL_POST_DEPLOY_HOOK_REQUIRED=true` for strict fail-fast behavior; keep `false` for best-effort warn-and-continue behavior.
- hook outcomes are persisted in `artifacts/infra/local_post_deploy_hook.env` and emitted as `local_post_deploy_hook_duration_seconds` metrics.
`make infra-status-json` captures the latest consolidated snapshot at
`artifacts/infra/infra_status_snapshot.json`.
For local live execution, the blueprint prefers the `docker-desktop` Kubernetes context when it exists.
Set `LOCAL_KUBE_CONTEXT` before running `infra-provision-deploy` if you want to override that default.
For consumer-maintained scripts that need direct cluster/Helm access, use shared wrappers instead of raw `kubectl`/`helm` calls:
```bash
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/port_forward.sh"

run_helm_with_active_access list --all-namespaces
start_port_forward "example" "apps" "svc/backend-api" "18080" "8080"
wait_for_local_port "example" "18080" "20"
stop_port_forward "example"
```
Use `cleanup_port_forwards` in `trap` handlers for long-running scripts.
For deterministic operator workflows, prefer make wrappers:
```bash
PF_NAME=backend-api PF_NAMESPACE=apps PF_RESOURCE=svc/backend-api PF_LOCAL_PORT=18080 PF_REMOTE_PORT=8080 make infra-port-forward-start
make infra-port-forward-stop PF_NAME=backend-api
make infra-port-forward-cleanup
```
Use `make auth-reconcile-runtime-identity` whenever you need an explicit runtime identity reconciliation pass
(ESO source-to-target checks + Argo repo access + Keycloak/module contract coverage).
For local profiles, Keycloak Argo sync is manual by default; after a successful reconcile run,
sync `platform-keycloak-local` explicitly from ArgoCD UI/CLI when you want to activate browser login.
See [Runtime Credentials (ESO)](runtime_credentials_eso.md) for local seeding and managed-store wiring.

Before publishing hosts or API routes, review [Endpoint Exposure Model](endpoint_exposure_model.md)
so public UI, protected UI, direct APIs, and internal SSR/BFF flows stay separated intentionally.
If you plan to expose bearer-token APIs on the shared edge, review
[Protected API Routes](protected_api_routes.md) before attaching JWT policy resources.
For async choreography and tenant-aware service boundaries, also review:
- [Event Messaging Baseline](event_messaging_baseline.md)
- [Zero-Downtime Evolution](zero_downtime_evolution.md)
- [Tenant Context Propagation](tenant_context_propagation.md)

## 7) STACKIT MVP Provision/Deploy (Optional)
For managed STACKIT execution (`BLUEPRINT_PROFILE=stackit-dev|stackit-stage|stackit-prod`), export:
- `STACKIT_PROJECT_ID`
- `STACKIT_REGION` (for example `eu01`)
- `STACKIT_SERVICE_ACCOUNT_KEY`
- `STACKIT_TFSTATE_ACCESS_KEY_ID`
- `STACKIT_TFSTATE_SECRET_ACCESS_KEY`

These values should align with the repository identity values:
- `BLUEPRINT_STACKIT_REGION`
- `BLUEPRINT_STACKIT_PROJECT_ID`
- `BLUEPRINT_STACKIT_TFSTATE_BUCKET`
- `BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX`

Before first live apply (`DRY_RUN=false`), pre-create the Object Storage bucket referenced by
`BLUEPRINT_STACKIT_TFSTATE_BUCKET` and provision an access key/secret with read/write access to it.
The blueprint does not auto-create backend bucket credentials.

Then run:
```bash
export BLUEPRINT_PROFILE=stackit-dev
make infra-stackit-bootstrap-preflight
make infra-stackit-bootstrap-apply
make infra-stackit-foundation-preflight
make infra-stackit-foundation-apply
make infra-stackit-foundation-seed-runtime-secret
make infra-stackit-foundation-fetch-kubeconfig
make infra-stackit-runtime-prerequisites
make infra-stackit-runtime-deploy
make auth-reconcile-runtime-identity
```

`infra-deploy` / `infra-stackit-runtime-deploy` already call
`infra-stackit-foundation-seed-runtime-secret` automatically; running it explicitly
is useful for debugging foundation output-to-runtime contract wiring.

Cleanup:
- Local cluster resources only: `make infra-local-destroy-all`
- Managed STACKIT layers: `make infra-stackit-destroy-all`
