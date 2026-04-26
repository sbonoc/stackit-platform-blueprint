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
   - For full blueprint-managed drift upgrades, use `make blueprint-upgrade-consumer` (plan/apply) followed by `make blueprint-upgrade-consumer-validate` and `make blueprint-upgrade-consumer-postcheck`.
   - The plan phase audits every file in the blueprint source tree against the contract (`required_files`, `init_managed`, `conditional_scaffold`, `feature_gated`, `blueprint_managed_roots`, `source_only`). Any uncovered file is emitted as a WARNING and counted in `upgrade_plan.json` under `uncovered_source_files_count`. The validate gate hard-fails (`make blueprint-upgrade-consumer-validate` exits non-zero) when `uncovered_source_files_count > 0`; this indicates a blueprint contract authoring error that must be resolved before any consumer apply can proceed. The `feature_gated` class covers paths that are conditionally present based on a feature flag (e.g., `apps/catalog`); declare them under `spec.repository.ownership_path_classes.feature_gated` in `blueprint/contract.yaml`.
   - After apply, the reconcile report (`artifacts/blueprint/upgrade/upgrade_reconcile_report.json`) tracks `conflicts_unresolved` by scanning the working tree for active `<<<<<<<` / `=======` / `>>>>>>>` merge markers. Only files with live markers are counted; auto-merged files (no markers remaining) and manually-resolved files (markers cleared) are excluded. A file is counted at most once regardless of how many source paths reference it.
   - The postcheck includes a **behavioral validation gate** that runs `bash -n` and a grep-based symbol-resolution check on every `result=merged` shell script produced by the apply phase. If a merged script has a syntax error or calls a function whose definition was silently dropped during merge, the postcheck fails and reports the findings in `artifacts/blueprint/upgrade_postcheck.json` under the `behavioral_check` key (fields: `status`, `files_checked`, `syntax_errors` `[{file, error}]`, `unresolved_symbols` `[{file, symbol, line}]`, `extra_excluded_count`). The symbol resolver excludes: case-label alternation tokens (`token|)` and `token | )`), bare-word elements inside `local`/`declare`/`readonly`/`typeset` array initializer blocks (`var=(`), and all standard shell builtins, common external commands, and blueprint bootstrap-chain runtime functions (including `tar`, `pnpm`, `blueprint_require_runtime_env`, `ensure_file_from_template`, and others). Consumer repos can extend the exclusion set without patching blueprint code by declaring additional token names in `blueprint/contract.yaml` under `spec.upgrade.behavioral_check.extra_excluded_tokens`; these are merged with the base set per invocation and the count is recorded in `extra_excluded_count`.
   - To skip the behavioral gate for a known acceptable case (e.g., complex macros or generated scripts), set `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true`. This emits a log warning and records `behavioral_check.skipped=true` in the postcheck report. Do not use this as a permanent workaround; the flag is intended for exceptional cases only.
   - The validate phase also scans the consumer working tree for files matching `source_artifact_prune_globs_on_init` (currently: `specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*` and `docs/blueprint/architecture/decisions/ADR-*.md`). These patterns match files that belong to the blueprint source repository and are pruned during `blueprint-init-repo`, so any matching files in a generated-consumer repo indicate an accidental carry-over from upgrade apply. When violations are found, `prune_glob_check.status` is set to `failure` in `artifacts/blueprint/upgrade_validate.json`, each violation is emitted to stderr as `prune-glob violation: <path> (matches: <glob>)`, and the postcheck adds `prune-glob-violations` to `blocked_reasons`. Remove the offending files and re-run `make blueprint-upgrade-consumer-validate` before proceeding.
   - After apply, run `make blueprint-upgrade-fresh-env-gate` to verify CI equivalence. The gate creates a temporary git worktree from `HEAD`, seeds the upgrade artifact directory (`artifacts/blueprint/`) from the working tree into the worktree (since gitignored files are absent from a fresh checkout by design), then runs `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` inside the clean worktree. A divergence report is written to `artifacts/blueprint/fresh_env_gate.json`. The gate compares SHA-256 checksums of all files under `artifacts/blueprint/` between the clean worktree and the working tree; any file whose checksum differs appears in the `divergences` array as `{"path": "...", "worktree_checksum": "...", "working_tree_checksum": "..."}`. The gate exits non-zero when divergences are non-empty even if both make targets exit 0, meaning CI would produce different artifact content from the local upgrade run.
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
For local profiles, `infra-provision-deploy` can run an optional post-deploy hook contract after smoke (`LOCAL_POST_DEPLOY_HOOK_ENABLED`, `LOCAL_POST_DEPLOY_HOOK_CMD`, `LOCAL_POST_DEPLOY_HOOK_REQUIRED`).

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
- ArgoCD topology validation uses `kustomize build --load-restrictor=LoadRestrictionsNone`:
  - STACKIT overlays intentionally reference shared manifests under `infra/gitops/argocd/core/<env>/`,
  - keep references inside the `infra/gitops/argocd/**` tree (do not reference paths outside the GitOps root).
- Bootstraps application catalog contract.
- Maintains baseline app runtime GitOps workload scaffold under `infra/gitops/platform/base/apps` when `APP_RUNTIME_GITOPS_ENABLED=true` (default), so Argo runtime paths include deployable `Deployment`/`Service` workloads from day one.
- Runs optional module deployment/reconciliation steps.
- Writes state artifacts to `artifacts/infra/deploy.env`.

### 3) Smoke
- Verifies baseline infra and app contracts.
- Verifies optional modules (if enabled).
- In live mode, captures pod inventory plus workload readiness for blueprint-managed namespaces only (`apps`, `data`, `messaging`, `network`, `security`, `observability`, `argocd`, `external-secrets`, `crossplane-system`, `envoy-gateway-system`).
- Writes state artifacts to `artifacts/infra/smoke.env`.
- When local post-deploy hook contract is enabled, writes hook outcome to `artifacts/infra/local_post_deploy_hook.env` after smoke.

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

## Context-Safe Kubernetes/Helm Helper Contract
- Source shared helpers from:
  - `scripts/lib/infra/tooling.sh`
  - `scripts/lib/infra/port_forward.sh` (for port-forward lifecycle primitives)
- `run_helm_upgrade_install`, `run_helm_template`, and `run_helm_uninstall` now execute Helm with explicit `--kubeconfig` and `--kube-context` resolved from the canonical cluster-access path.
- Shared runtime helpers for optional-module secrets, public endpoint Gateway lifecycle, and Keycloak runtime identity reconciliation now route kubectl calls through the same active-access wrappers (no implicit-context kubectl calls in those helper paths).
- Consumers can call shared wrappers directly for custom scripts:
  - `run_kubectl_with_active_access ...`
  - `run_kubectl_capture_with_active_access ...`
  - `run_helm_with_active_access ...`
- Helm repo refresh retries are standardized via shared retry/backoff helpers:
  - `HELM_REPO_UPDATE_RETRY_MAX_ATTEMPTS` (default `3`)
  - `HELM_REPO_UPDATE_RETRY_BASE_DELAY_SECONDS` (default `2`)
  - `HELM_REPO_UPDATE_RETRY_MAX_DELAY_SECONDS` (default `20`)
  - `HELM_REPO_UPDATE_RETRY_BACKOFF_MULTIPLIER` (default `2`)
- Generic port-forward primitives are service-agnostic and reusable:
  - `start_port_forward <name> <namespace> <resource> <local_port> <remote_port> [log_path]`
  - `wait_for_local_port <name> <local_port> [timeout_seconds]`
  - `stop_port_forward <name> [force_kill]`
  - `cleanup_port_forwards [force_kill]`

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

## Merge-Required Semantic Annotations

Every `merge-required` entry in the upgrade plan carries a `semantic` annotation generated from
the baseline-to-source static diff. Annotations appear in three upgrade artifacts:

- `artifacts/blueprint/upgrade_plan.json` — under each `merge-required` entry as `entry.semantic`
- `artifacts/blueprint/upgrade_summary.md` — in the **Merge-Required Annotations** section
- `artifacts/blueprint/upgrade_apply.json` — under each `result=merged` or `result=conflict` result item

Each annotation has three fields:

| Field | Type | Description |
|---|---|---|
| `kind` | string (closed set) | Category of change detected |
| `description` | string | Human-readable summary naming the changed symbol and its new value |
| `verification_hints` | string[] | Concrete actions the consumer should take after applying the merge |

Closed-set `kind` values (detection order — first match wins):

| `kind` | Triggered when |
|---|---|
| `function-added` | Source contains a shell function whose name is absent from the baseline |
| `function-removed` | Baseline contains a shell function whose name is absent from the source |
| `variable-changed` | A variable assignment (`VAR=value`) differs in value between baseline and source |
| `source-directive-added` | Source adds a `source` or `.` directive that is absent from the baseline |
| `structural-change` | No specific pattern matched, or the baseline is absent (additive file) |

Detection is static regex analysis only — no file content is executed.
Complex diffs or large refactors that match no pattern receive `kind=structural-change`,
a safe, always-actionable fallback ("manually review the diff").

Additive files (absent from the baseline tag, present at source HEAD) always receive
`kind=structural-change` with `description="Additive file: no baseline ancestor exists"`
because the entire file is new and a diff-based kind cannot be inferred.

A per-entry annotation failure falls back silently to `structural-change` and logs a warning;
plan generation continues uninterrupted.

Annotation coverage is logged during plan generation:
```
semantic annotator: merge-required=N auto=M fallback=P
```

## Make and Script Ownership
- `Makefile` is a blueprint-managed loader.
- blueprint-managed targets are rendered into `make/blueprint.generated.mk`.
- platform-owned targets live in `make/platform.mk` and `make/platform/*.mk` (seeded if missing, then editable).
- platform-owned scripts live in `scripts/bin/platform/**` and `scripts/lib/platform/**`.

## Shell Bootstrap Contract
- Managed shell entrypoints must use the canonical prelude:
  - `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
  - `source "$SCRIPT_DIR/.../lib/shell/bootstrap.sh"`
- `ROOT_DIR` resolution is centralized in `scripts/lib/shell/root_dir.sh` via `resolve_root_dir`.
- Do not add inline per-script `ROOT_DIR` resolver blocks.
- Non-git temp-copy execution (for quality/docs render paths) is supported through marker walk-up fallback (`Makefile` + `scripts/lib`) in the shared resolver.

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
