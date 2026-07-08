# Troubleshooting

Common first-day issues for generated repositories.

## `make blueprint-init-repo` fails
- Ensure required variables are exported or present in `blueprint/repo.init.env`:
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
- Check `docs/docusaurus.config.js` and `blueprint/contract.yaml` are writable.
- If the repo is already initialized, rerun only when you intentionally want to re-apply init-owned files:
  ```bash
  BLUEPRINT_INIT_FORCE=true make blueprint-init-repo
  ```

## `make blueprint-init-repo-interactive` fails in CI
- The interactive target requires a TTY terminal.
- In CI/non-interactive shells, use env-file mode with `make blueprint-init-repo`.

## `make blueprint-bootstrap` fails with a missing consumer-initialized file
- Generated repos do not recreate consumer-owned root files during bootstrap.
- Restore them intentionally, then rerun bootstrap:
  ```bash
  make blueprint-resync-consumer-seeds
  BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
  make blueprint-bootstrap
  ```
- Missing files are classified as `auto-refresh` (`action=create`) and are recreated by safe apply:
  `BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds`.
- Use `BLUEPRINT_RESYNC_APPLY_ALL=true make blueprint-resync-consumer-seeds` only when full overwrite is intentional
  for files classified as `manual-merge`.

## `make infra-bootstrap` fails with a missing init-managed file
- Generated repos do not recreate init-managed identity files from ambient env during infra bootstrap.
- Restore them intentionally, then rerun infra bootstrap:
  ```bash
  BLUEPRINT_INIT_FORCE=true make blueprint-init-repo
  make infra-bootstrap
  ```

## `make infra-validate` fails with branch naming errors
- Branch names must match contract prefixes (for example `feature/...`, `fix/...`, `chore/...`, `docs/...`).
- Compatibility prefixes `codex/...` and `copilot/...` are accepted even when older consumer contracts do not yet list them.
- If running in CI, ensure `GITHUB_HEAD_REF`/`GITHUB_REF_NAME` is available or set `BLUEPRINT_BRANCH_NAME`.

## `make blueprint-check-placeholders` fails
- Re-run `make blueprint-init-repo` with correct values.
- Confirm `blueprint/repo.init.env` does not contain stale identity overrides.
- Confirm `blueprint/repo.init.secrets.env` exists (copy from `blueprint/repo.init.secrets.example.env` when missing).
- For enabled optional modules, confirm required non-sensitive inputs in `blueprint/repo.init.env` and required sensitive inputs in `blueprint/repo.init.secrets.env` are non-empty.
- Confirm contract and docs identity values match your repository owner/name.
- Confirm `blueprint/contract.yaml` sets `repo_mode: generated-consumer`.

## `make blueprint-resync-consumer-seeds` reports `manual-merge`
- `manual-merge` means the current file diverged from the latest seed and appears customized.
- Keep dry-run as the default review step, then decide per file:
  - merge manually if you need to preserve local customizations
  - use safe apply for untouched/missing files:
    ```bash
    BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
    ```
  - use full overwrite only when intentional:
    ```bash
    BLUEPRINT_RESYNC_APPLY_ALL=true make blueprint-resync-consumer-seeds
    ```

## `make blueprint-resync-consumer-seeds` fails with unresolved `{{...}}` token errors
- Resync now fails fast when a seeded template still contains unresolved blueprint tokens after rendering.
- Typical cause: a consumer-seeded template introduced a token that is not part of the supported replacement set.
- Keep dry-run first, then inspect the template path reported in the error and replace unsupported tokens with concrete values or supported placeholders.

## `make blueprint-install-codex-skill` fails with `skill source not found`
- The installer first checks the repo-local skill source under `.agents/skills/<skill-name>`.
- If repo-local skill files are missing, it falls back to consumer template assets under `scripts/templates/consumer/init/.agents/skills/<skill-name>`.
- If both paths are missing, sync blueprint-managed assets first and rerun:
  ```bash
  make blueprint-upgrade-consumer
  BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
  make blueprint-install-codex-skill
  ```
- The same remediation applies to:
  - `make blueprint-install-codex-skill-consumer-ops`
  - `make blueprint-install-codex-skill-sdd-step01-intake`
  - `make blueprint-install-codex-skill-sdd-step02-resolve-questions`
  - `make blueprint-install-codex-skill-sdd-step03-spec-complete`
  - `make blueprint-install-codex-skill-sdd-step04-plan-slicer`
  - `make blueprint-install-codex-skill-sdd-step05-implement`
  - `make blueprint-install-codex-skill-sdd-step06-document-sync`
  - `make blueprint-install-codex-skill-sdd-step07-pr-packager`
  - `make blueprint-install-codex-skill-sdd-traceability-keeper`
  - `make blueprint-install-codex-skills`

## `make blueprint-upgrade-consumer` fails with `RuntimeError: git merge-file failed:` (empty detail)
- This usually means the repository is still executing a stale local upgrade engine from an older consumer baseline.
- Current blueprint upgrade wrappers default to `BLUEPRINT_UPGRADE_ENGINE_MODE=source-ref`, which runs the engine script resolved from `BLUEPRINT_UPGRADE_SOURCE@BLUEPRINT_UPGRADE_REF`.
- Current local engine behavior also treats any positive `git merge-file` return code as conflict-present and emits normal conflict artifacts/report output instead of an internal abort.
- If your repository still has the legacy wrapper behavior, run a one-time source-driven upgrade engine call, then rerun validation:
  ```bash
  TMP_DIR="$(mktemp -d)"
  git clone --quiet --no-checkout "${BLUEPRINT_UPGRADE_SOURCE}" "${TMP_DIR}/source"
  git -C "${TMP_DIR}/source" checkout --quiet "${BLUEPRINT_UPGRADE_REF}"
  python3 "${TMP_DIR}/source/scripts/lib/blueprint/upgrade_consumer.py" \
    --repo-root "$PWD" \
    --source "${BLUEPRINT_UPGRADE_SOURCE}" \
    --ref "${BLUEPRINT_UPGRADE_REF}" \
    --apply \
    --plan-path artifacts/blueprint/upgrade_plan.json \
    --apply-path artifacts/blueprint/upgrade_apply.json \
    --summary-path artifacts/blueprint/upgrade_summary.md
  rm -rf "${TMP_DIR}"
  make blueprint-upgrade-consumer-validate
  make blueprint-upgrade-consumer-postcheck
  ```
- After the upgrade lands, keep using `make blueprint-upgrade-consumer` with the default engine mode (`source-ref`) for deterministic future runs.

## How to read `merge-required` semantic annotations in the upgrade plan

Every `merge-required` entry in `upgrade_plan.json` and `upgrade_summary.md` carries a `semantic`
annotation with three fields:

- `kind` — category of change (see table below)
- `description` — human-readable summary naming the changed symbol and new value
- `verification_hints` — concrete actions to verify after applying the merge

| `kind` | What changed |
|---|---|
| `function-added` | A shell function was added to the source; check that its call sites are correct after merge |
| `function-removed` | A shell function was removed from the source; check that no call sites still reference it |
| `variable-changed` | A variable assignment changed value; verify the new value is correct in your merged file |
| `source-directive-added` | A `source` or `.` directive was added; confirm the sourced file exists at the expected path |
| `structural-change` | Complex diff or new file — manually review the full diff before resolving the merge |

`structural-change` is the fallback for diffs that do not match a specific pattern; it is always
actionable via manual review and does not indicate an error in the annotator.

The **Merge-Required Annotations** section in `artifacts/blueprint/upgrade_summary.md` lists every
annotated entry with its kind, description, and bullet hints — read it before starting manual merges.

## Consumer-renamed manifest deleted after `make blueprint-upgrade-consumer BLUEPRINT_UPGRADE_ALLOW_DELETE=true`

If a file in your consumer repository has been renamed but the original blueprint path
still exists in the upgrade payload, the upgrade apply step may delete the original path
rather than recognising that it is referenced by a `kustomization.yaml` in the same directory.

**Root cause:** The upgrade apply stage checks three layers before deleting any entry:

1. Contract ownership — `consumer_seeded`, `source_only`, and `init_managed` entries are never deleted.
2. Consumer-owned workload fast path — any file under `base/apps/` whose YAML `metadata.name`
   or `metadata.labels.app` matches an existing `kustomization.yaml` resource is preserved.
3. Kustomization-ref guard — any file whose basename appears in the `resources:` or `patches:`
   list of a `kustomization.yaml` in the same directory is preserved, regardless of its path.

If your renamed manifest was still deleted, check:

- The file's basename exactly matches a `resources:` or `patches:` entry in the sibling
  `kustomization.yaml`. Path values are compared case-sensitively.
- The sibling `kustomization.yaml` is valid YAML. If it contains syntax errors the guard
  falls back to `False` and logs a warning to stderr:
  ```
  warning: _is_kustomization_referenced: failed to parse <path>: <error>
  ```
  Fix the YAML syntax and rerun the upgrade.
- Check `artifacts/blueprint/upgrade_summary.md` — the `consumer_kustomization_ref_count`
  field shows how many entries were preserved by the kustomization-ref guard in the last run.

**Recovery:** If the file was already deleted, restore it from git history:
```bash
git checkout HEAD~1 -- <path/to/deleted-file.yaml>
git add <path/to/deleted-file.yaml>
git commit -m "fix: restore <filename> deleted incorrectly during blueprint upgrade"
```

## `.tf` file contains duplicate resource blocks after `make blueprint-upgrade-consumer`

When the upgrade apply stage merges a `.tf` file, it scans for top-level Terraform block
declarations that appear more than once (same block type, name, and label).

- **Byte-identical duplicates** are automatically removed. The result is recorded as
  `merged-deduped` in the apply summary and the removed block is listed in the
  `deduplication_log` section of `artifacts/blueprint/upgrade_summary.md`.
  Check the `tf_dedup_count` summary field to see how many were removed.

- **Non-identical duplicates** (blocks with the same header but different bodies) cannot
  be resolved automatically. The upgrade produces a `conflict` artifact at the same path
  and leaves both block variants in the file separated by conflict markers. Resolve manually:

  1. Open the file flagged as `conflict` in `artifacts/blueprint/upgrade_summary.md`.
  2. Identify the two block variants between the conflict markers.
  3. Decide which variant (or which merged result) is correct for your repository.
  4. Remove the conflict markers and the rejected variant.
  5. Run `terraform validate` to confirm the file is syntactically valid.
  6. Commit the resolution before rerunning the bootstrap or plan targets.

## `make infra-validate` fails with `apps/descriptor.yaml: app[...]` error

`apps/descriptor.yaml` is the consumer-owned app metadata source (see
[App Onboarding Contract — App Descriptor](app_onboarding.md#app-descriptor-appsdescriptoryaml)).
`infra-validate` parses it and reports any schema, path-safety, or
kustomization-membership failure with deterministic messages naming the descriptor app,
component, and offending value.

Common error patterns and fixes:

- `apps/descriptor.yaml: apps[N].id must be a DNS-style label ...`
  - The app or component `id` contains forbidden characters (`/`, `..`, uppercase, shell
    metacharacters). Rename to lowercase alphanumerics + hyphens (e.g. `marketplace-api`).

- `apps/descriptor.yaml: app[<id>].component[<id>].manifests.<kind> must live under infra/gitops/platform/base/apps/`
  - Manifest path escapes the apps base directory or uses an absolute path. Use a relative
    path under `infra/gitops/platform/base/apps/`, or omit the explicit ref to use the
    convention default (`{component-id}-{deployment,service}.yaml`).

- `apps/descriptor.yaml: app[<id>].component[<id>]: <kind> manifest missing: <path>`
  - The resolved manifest file does not exist on disk. Create the missing manifest under
    `infra/gitops/platform/base/apps/` or correct the explicit ref.

- `apps/descriptor.yaml: app[<id>].component[<id>]: <kind> manifest filename not listed in infra/gitops/platform/base/apps/kustomization.yaml`
  - The manifest exists but isn't listed in the apps `kustomization.yaml`. Add the
    basename to the `resources:` list and rerun `make infra-validate`.
  - **v1.8.1-only regression (issue #230, fixed in the next blueprint patch).** Consumers
    that upgraded from v1.8.0 to v1.8.1 hit this with 4 errors at once
    (`backend-api-deployment.yaml`, `backend-api-service.yaml`,
    `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) because
    `blueprint-init-repo` force-reseeded `apps/descriptor.yaml` from the demo-app
    template while leaving the consumer's existing `kustomization.yaml` untouched.
    Recovery: upgrade to the next blueprint patch (descriptor↔kustomization paired-reseed
    via `consumer_seeded` contract) and re-run
    `make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck`. No
    consumer-side workaround is required after upgrading.

## `make blueprint-upgrade-consumer` writes `artifacts/blueprint/app_descriptor.suggested.yaml`

When an existing consumer lacks `apps/descriptor.yaml`, the upgrade flow emits a
starting-point descriptor at `artifacts/blueprint/app_descriptor.suggested.yaml` derived
from the current `infra/gitops/platform/base/apps/kustomization.yaml`. The upgrade does
**not** write `apps/descriptor.yaml` automatically — adoption is explicit.

To adopt:

1. Open `artifacts/blueprint/app_descriptor.suggested.yaml`.
2. Set `owner.team: TODO` to your real team handle for each app.
3. Adjust app/component `id` values if the suggested IDs (derived from manifest filenames)
   don't match your intended naming.
4. Add optional `service.port`, `health.*` fields per component if you want the catalog
   manifest renderer to surface them.
5. Move the file to `apps/descriptor.yaml` at your repo root:
   ```bash
   mv artifacts/blueprint/app_descriptor.suggested.yaml apps/descriptor.yaml
   ```
6. Run `make infra-validate` to confirm the descriptor is valid and all manifests resolve.

After adoption, `make blueprint-upgrade-consumer` stops emitting the suggested artifact
on subsequent runs. Apps declared in `apps/descriptor.yaml` are protected from prune as
`consumer-app-descriptor` (see `summary.consumer_app_descriptor_count` in
`artifacts/blueprint/upgrade_apply.json`).

## `make blueprint-upgrade-consumer` fails on v1.10.0 with contract coverage, behavioral check, or fresh-env errors

Four bugs in the v1.10.0 upgrade engine were fixed in the blueprint release following v1.10.0.
If you are upgrading to v1.10.0 and hitting any of the errors below, upgrade to the next blueprint
release — no consumer-side workaround is required.

| Symptom | Issue | Fixed in |
|---|---|---|
| `make blueprint-upgrade-consumer` blocked at plan phase: `uncovered_source_files_count=4` (pyproject.toml, uv.lock, opensearch/values.yaml, kms/values.yaml) | #258 | blueprint post-v1.10.0 |
| `make blueprint-upgrade-consumer-validate` runs `blueprint-template-smoke` and fails on a generated-consumer repo | #260 | blueprint post-v1.10.0 |
| `make blueprint-upgrade-consumer-postcheck` reports 29+ unresolved symbols (`uv`, `validate`, or blueprint functions defined in transitively sourced files) | #259 | blueprint post-v1.10.0 |
| `make blueprint-upgrade-fresh-env-gate` fails with checksum divergences on `upgrade_validate.json` or `required_files_status.json` | #261 | blueprint post-v1.10.0 |

**Automated workarounds (issue #268):** if you are running the blueprint pipeline with the
workaround catalogue (shipped alongside issue #268), the upgrade pipeline applies workarounds for
#258 (Stage 1c, before apply) and #259, #260, #261 (Stage 2c, after apply) automatically.
No manual steps are needed. Check `artifacts/blueprint/workarounds_applied.json` after the upgrade
to confirm which entries were applied.

If you are running an older pipeline without the catalogue, or need to apply workarounds manually:
- **#259 (`uv`, `validate` false positives):** add them to `spec.upgrade.behavioral_check.extra_excluded_tokens` in `blueprint/contract.yaml`. Remove this workaround after upgrading to the fixed blueprint.
- **#260 (template-smoke on generated-consumer):** no consumer-side workaround is available without patching the blueprint; upgrade the blueprint.
- **#258 (contract coverage gap):** manually add the 4 missing files to the correct ownership classes in `blueprint/contract.yaml`: `pyproject.toml` and `uv.lock` under `init_managed`, `infra/local/helm/opensearch/values.yaml` and `infra/local/helm/kms/values.yaml` under `conditional_scaffold`. Remove these entries after upgrading to the fixed blueprint.
- **#261 (volatile artifact divergences):** no consumer-side workaround is available without patching the blueprint; upgrade the blueprint.

## `make docs-build` fails on v1.10.0 with `docusaurus: not found` or pnpm version mismatch

Two bugs in the v1.10.0 docs tooling were fixed in the blueprint release following v1.10.0.
If you are on v1.10.0 and hitting either error below, upgrade to the next blueprint release.

| Symptom | Issue | Fixed in |
|---|---|---|
| `make docs-build` fails with `sh: docusaurus: not found`; `docs/node_modules/` is empty after `make docs-install` on a repo whose `pnpm-workspace.yaml` excludes `docs/` | #272 | blueprint post-v1.10.0 |
| `make docs-install` exits with a pnpm version mismatch error that does not name the root `package.json#packageManager` field as a cause | #273 | blueprint post-v1.10.0 |

If you cannot upgrade the blueprint immediately and need a consumer-side workaround:

- **#272 (`docusaurus: not found` — empty `docs/node_modules/`):** Locally patch `scripts/lib/docs/site.sh` to restore `--ignore-workspace` to all three pnpm invocations (`docs_pnpm_install`, `docs_pnpm_build`, `docs_pnpm_start`). For `docs_pnpm_install`, the corrected call is:
  ```bash
  run_cmd pnpm --dir "$DOCS_SITE_DIR" --ignore-workspace install --frozen-lockfile
  ```
  Apply the same `--ignore-workspace` flag to the `run build` and `run start` calls. Remove this patch after upgrading to the fixed blueprint.

- **#273 (pnpm version mismatch):** If `make docs-install` exits with a pnpm version mismatch, align all three pnpm version sources to the version declared in `docs/package.json#packageManager`:
  1. Update your local pnpm: `corepack prepare pnpm@<version> --activate`
  2. Update the root `package.json#packageManager` field to `pnpm@<version>`
  3. Update your CI workflow's corepack prepare step to pin the same version
  Run `make docs-install` again to confirm the mismatch is resolved.

## Pull requests are not auto-requesting reviewers
- Generated repositories seed `.github/CODEOWNERS` as a starter file with commented examples only.
- Replace the example owners with your real team handles before relying on GitHub review assignment.
- Keep `.github/pull_request_template.md` and `.github/ISSUE_TEMPLATE/**` aligned with your team workflow once you adopt them.

## `dags/` appears unexpectedly
- In the blueprint source repository, `dags/` is tracked intentionally as template authoring scaffolding.
- In a generated consumer repository, `make blueprint-init-repo` prunes `dags/` when `WORKFLOWS_ENABLED=false`.
- If `WORKFLOWS_ENABLED=false` and `dags/` is still present in a fresh consumer repo, rerun first init before your first commit, then re-validate:
  ```bash
  WORKFLOWS_ENABLED=false BLUEPRINT_INIT_FORCE=true make blueprint-init-repo
  WORKFLOWS_ENABLED=false make blueprint-bootstrap
  WORKFLOWS_ENABLED=false make infra-bootstrap
  WORKFLOWS_ENABLED=false make infra-validate
  ```

## Disabled module but resources still exist
- Disabling an optional module removes its generated Make targets, but already materialized scaffold files are intentionally preserved.
- Already provisioned resources are not destroyed automatically.
- Run disabled-module teardown first, then refresh the repo state for the new flag set:
  ```bash
  make infra-destroy-disabled-modules
  WORKFLOWS_ENABLED=false make blueprint-render-makefile
  WORKFLOWS_ENABLED=false make infra-bootstrap
  ```
- If you prefer explicit module-level teardown, run the module destroy target directly while the module flag is still enabled.

## Local runtime command left `make/blueprint.generated.mk` modified
- Runtime chains (`infra-provision`, `infra-deploy`, `infra-smoke`, and `infra-provision-deploy`) must be side-effect free for blueprint-managed tracked files.
- `infra-validate` now renders `make/blueprint.generated.mk` from contract defaults and ignores transient module toggle overrides during runtime flows.
- If you intentionally want to materialize optional module targets from a new module flag set, use:
  ```bash
  make blueprint-render-makefile
  ```
- Confirm clean state after runtime commands:
  ```bash
  git status --short make/blueprint.generated.mk
  ```

## Local live execution picked the wrong Kubernetes cluster
- Local profiles prefer the `docker-desktop` context when it is present.
- CI prefers `kind-*` contexts.
- Run `make infra-context` to see the resolved cluster and selection source.
- If you want to force a different local cluster, set `LOCAL_KUBE_CONTEXT` explicitly before provisioning:
  ```bash
  export LOCAL_KUBE_CONTEXT=kind-blueprint-e2e
  make infra-context
  ```

## `make infra-smoke` fails on `CrashLoopBackOff` / `ImagePullBackOff`
- Live smoke fails when blueprint-managed workloads are not healthy.
- Inspect:
  - `artifacts/infra/workload_health.json`
  - `artifacts/infra/workload_pods.json`
  - `artifacts/infra/smoke_diagnostics.json`
- Typical causes:
  - invalid module credentials or secrets (for example `IAP_COOKIE_SECRET` not being 16, 24, or 32 bytes)
  - stale local image tags if chart/image pins were edited away from the canonical versions source (`scripts/lib/infra/versions.sh`)
- Re-run the affected module plan/apply target after correcting the contract input.

## Local destroy removed resources but not the cluster
- `make infra-local-destroy-all` intentionally removes blueprint-managed resources only.
- It preserves the selected local cluster itself (`docker-desktop`, `kind-*`, or the explicit `LOCAL_KUBE_CONTEXT` override).
- Use that target before switching local clusters or before a fresh live rerun:
  ```bash
  make infra-local-destroy-all
  ```

## Template smoke fails in CI
- Ensure required local tools are available (`bash`, `git`, `make`, `python3`, `tar`).
- Confirm CI job exports init variables, `BLUEPRINT_PROFILE`, and any intended optional-module flags before `make blueprint-template-smoke`.

## CI runs on draft PRs

Consumer repos bootstrapped from the blueprint template before v1.11.0 may have
a `.github/workflows/ci.yml` that lacks the draft-PR types filter and job-level
guard. This causes the full CI pipeline to run on draft pull requests, wasting
CI minutes and producing misleading status checks.

**Symptom**: CI triggers and runs jobs immediately when a PR is opened as a draft.

**Fix**: Upgrade to blueprint v1.11.0 or later using the standard upgrade flow:

```bash
BLUEPRINT_UPGRADE_REF=<tag|commit> make blueprint-upgrade-consumer
make blueprint-upgrade-consumer-validate
make blueprint-upgrade-consumer-postcheck
```

After upgrade, `.github/workflows/ci.yml` will include:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

jobs:
  quality-fast:
    if: github.event_name == 'push' || github.event.pull_request.draft == false
```

This skips CI for draft PRs and resumes automatically when the PR is marked
ready for review.

## CI warns about deprecated Node 20 GitHub actions
- Upgrade your generated repository to the latest blueprint ref so CI picks up Node-24-ready action majors:
  - `.github/actions/prepare-blueprint-ci/action.yml` (`actions/setup-python@v6`, `actions/setup-node@v6`)
  - `.github/workflows/ci.yml` (`actions/checkout@v6`)
- Use the upgrade flow from the repository root:
  ```bash
  make blueprint-resync-consumer-seeds
  BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
  BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer
  make blueprint-upgrade-consumer-validate
  make blueprint-upgrade-consumer-postcheck
  ```
- Temporary fallback only if you cannot upgrade immediately:
  - set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` in workflow/job env.

## `apps-smoke` fails with missing `apps/catalog/manifest.yaml`
- The app catalog scaffold is opt-in and controlled by `APP_CATALOG_SCAFFOLD_ENABLED`.
- Enable and materialize the scaffold before running smoke:
  ```bash
  APP_CATALOG_SCAFFOLD_ENABLED=true make apps-bootstrap
  APP_CATALOG_SCAFFOLD_ENABLED=true make apps-smoke
  ```
- If you intentionally run a minimal repo without app catalog scaffold, keep `APP_CATALOG_SCAFFOLD_ENABLED=false`; `apps-smoke` records a skipped catalog check and still succeeds.

## Argo core app syncs but `apps` runtime workloads are missing
- Baseline app runtime GitOps scaffold is controlled by `APP_RUNTIME_GITOPS_ENABLED` (default `true`).
- Reconcile and validate scaffold contract explicitly:
  ```bash
  APP_RUNTIME_GITOPS_ENABLED=true make infra-bootstrap
  APP_RUNTIME_GITOPS_ENABLED=true make infra-validate
  ```
- Confirm runtime path includes workload manifests:
  - `infra/gitops/platform/base/kustomization.yaml` has `- apps`
  - `infra/gitops/platform/base/apps/*` contains `Deployment` and `Service` manifests
- If `APP_CATALOG_SCAFFOLD_ENABLED=true`, keep `apps/catalog/manifest.yaml` synchronized with runtime paths:
  - `deliveryTopology`
  - `runtimeDeliveryContract.gitopsWorkloads`
  - `runtimeDeliveryContract.manifestsRoot`
- If you replaced scaffold images, ensure the same refs are updated in:
  - `apps/catalog/manifest.yaml`
  - `infra/gitops/platform/base/apps/*deployment.yaml`

## `infra-smoke` fails with `empty-runtime-workloads`
- Execute-mode smoke (`DRY_RUN=false`) now fails deterministically when app runtime is declared enabled but expected runtime workloads are absent.
- Guardrail contract defaults:
  - `APP_RUNTIME_GITOPS_ENABLED=true`
  - `APP_RUNTIME_MIN_WORKLOADS=1` (minimum `Deployment`/`StatefulSet` objects in namespace `apps`)
- Inspect:
  - `artifacts/apps/apps_smoke.env` (`runtime_workload_check_*` markers)
  - `artifacts/infra/workload_health.json` (`statusReason`, `requiredNamespaceMinimumPods`, `emptyRuntimeNamespaces`)
  - `artifacts/infra/smoke_diagnostics.json` (`workloadHealth.emptyRuntimeNamespaceCount`, `appRuntime.minimumExpectedWorkloads`)
- If runtime should be intentionally empty during a transition window, set an explicit override for that run:
  ```bash
  APP_RUNTIME_MIN_WORKLOADS=0 DRY_RUN=false make infra-smoke
  ```
  Then restore `APP_RUNTIME_MIN_WORKLOADS=1` once workload deployment is expected again.

## `infra-provision-deploy` local post-deploy hook fails or is skipped unexpectedly
- The hook contract runs only for local profiles (`local-full`, `local-lite`) and only after `infra-provision`, `infra-deploy`, and `infra-smoke` succeed.
- Contract toggles:
  - `LOCAL_POST_DEPLOY_HOOK_ENABLED=false` by default (skip with `reason=disabled`).
  - `LOCAL_POST_DEPLOY_HOOK_CMD='make -C "$ROOT_DIR" infra-post-deploy-consumer'` by default.
  - `LOCAL_POST_DEPLOY_HOOK_REQUIRED=false` by default (best-effort warn-and-continue).
- Inspect the state artifact:
  - `artifacts/infra/local_post_deploy_hook.env` (`status`, `reason`, `mode`, `enabled`, `command_configured`)
  - `artifacts/infra/local_post_deploy_hook.json` (schema-validated canonical state payload)
- Common outcomes:
  - `status=skipped reason=non_local_profile`: expected for `stackit-*` profiles.
  - `status=skipped reason=disabled`: set `LOCAL_POST_DEPLOY_HOOK_ENABLED=true` to execute the hook.
  - `status=failure reason=command_failed`: hook command failed; with `LOCAL_POST_DEPLOY_HOOK_REQUIRED=false` chain continues, with `true` it fails fast.
- In generated-consumer repositories, implement deterministic commands in `make/platform.mk` target `infra-post-deploy-consumer` (the seeded target is an intentional fail-fast placeholder until you replace it).
- Upgrade preflight guardrail: when `LOCAL_POST_DEPLOY_HOOK_ENABLED=true`, `make blueprint-upgrade-consumer-preflight` reports a required manual action if `infra-post-deploy-consumer` is still placeholder.
- Upgrade preflight required-target checklist: when a contract-required consumer-owned Make target is missing, preflight reports a required manual action with the exact target name; implement it in `make/platform.mk` or `make/platform/*.mk`, then rerun `make blueprint-upgrade-consumer-validate` and `make blueprint-upgrade-consumer-postcheck`.

## CI test lanes fail on clean runners with missing `fastapi`, `vitest`, or Playwright browsers
- Ensure your workflow uses `.github/actions/prepare-blueprint-ci/action.yml` before test lanes.
- The current action bootstrap contract delegates dependency installation to `BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-ci-bootstrap`.
- CI toolchain/OS dependencies are handled by `make infra-prereqs` in the shared action.
- App/runtime dependencies are handled by `make apps-ci-bootstrap`, which composes:
  - `make apps-bootstrap` (baseline app scaffolding/state)
  - `make apps-ci-bootstrap-consumer` (consumer-owned dependency install contract)
- In generated-consumer mode, the seeded `apps-ci-bootstrap-consumer` is an intentional fail-fast placeholder. Replace it with deterministic commands for your repository layout (no directory scanning/discovery), for example:
  - backend Python dependency install from your fixed backend path(s)
  - touchpoints/package-manager dependency install from your fixed frontend/workspace path(s)
  - optional browser/runtime bootstrap only when your package metadata declares that dependency
- Keep all consumer-specific CI bootstrap commands in `apps-ci-bootstrap-consumer` in `make/platform.mk` (or `make/platform/*.mk`) as the single consumer-owned hook.
- Confirm path ownership before patching CI failures:
  - `make blueprint-ownership-check OWNERSHIP_PATHS="scripts/bin/platform/touchpoints/test_e2e.sh make/platform.mk"`
  - `scripts/bin/platform/**` and `make/platform*` ownership should resolve to `platform-owned`.
- If your repository still fails with errors such as `ModuleNotFoundError: fastapi`, `vitest: command not found`, or `Executable doesn't exist ... chrome-headless-shell`, resync and upgrade from repository root:
  ```bash
  make blueprint-resync-consumer-seeds
  BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
  BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer
  make blueprint-upgrade-consumer-validate
  make apps-ci-bootstrap
  ```

## STACKIT preflight fails on backend contract
- Ensure backend files exist under:
  - `infra/cloud/stackit/terraform/bootstrap/state-backend/<env>.hcl`
  - `infra/cloud/stackit/terraform/foundation/state-backend/<env>.hcl`
- Ensure each backend file contains:
  - `skip_requesting_account_id`
  - `use_path_style`
  - STACKIT object storage endpoint (`object.storage...`)
- Ensure repository identity values are coherent:
  - `BLUEPRINT_STACKIT_REGION`
  - `BLUEPRINT_STACKIT_TFSTATE_BUCKET`
  - `BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX`

## STACKIT foundation preflight fails on SKE permission probe
- In execution mode (`DRY_RUN=false`), foundation preflight probes SKE API access before Terraform apply.
- If you see `service account lacks SKE permissions`, ensure the identity behind `STACKIT_SERVICE_ACCOUNT_KEY` can:
  - enable/read SKE service in the project and region
  - list/read SKE clusters in the project
- Re-run preflight after updating IAM:
  ```bash
  make infra-stackit-foundation-preflight
  ```
- Check the state artifact for probe outcome:
  - `artifacts/infra/stackit_foundation_preflight.env` (`ske_access_probe=passed` expected in execute mode)

## STACKIT apply/fetch kubeconfig fails with missing credentials
- In execution mode (`DRY_RUN=false`), always export:
  - `STACKIT_PROJECT_ID`
  - `STACKIT_REGION`
  - `STACKIT_SERVICE_ACCOUNT_KEY`
  - `STACKIT_TFSTATE_ACCESS_KEY_ID`
  - `STACKIT_TFSTATE_SECRET_ACCESS_KEY`
- Ensure the backend bucket exists and matches the repository identity:
  - `BLUEPRINT_STACKIT_TFSTATE_BUCKET`
  - `BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX`
- Ensure `STACKIT_TFSTATE_ACCESS_KEY_ID` / `STACKIT_TFSTATE_SECRET_ACCESS_KEY` can read/write that bucket.
- Re-run in order:
  ```bash
  make infra-stackit-bootstrap-preflight
  make infra-stackit-bootstrap-apply
  make infra-stackit-foundation-preflight
  make infra-stackit-foundation-apply
  make infra-stackit-foundation-fetch-kubeconfig
  ```

## kubectl returns Unauthorized after infra-stackit-foundation-fetch-kubeconfig (blueprint v1.12.3+)

`stackit_ske_kubeconfig` generates a client certificate with a ~1-hour TTL. Before
v1.12.3, `make infra-stackit-foundation-fetch-kubeconfig` called `terraform apply`
which — finding no config changes — returned the expired kubeconfig from state unchanged.

**From v1.12.3 onwards this is fixed**: `infra-stackit-foundation-fetch-kubeconfig`
force-taints `stackit_ske_kubeconfig.foundation[0]` before every apply in execute mode
(`DRY_RUN=false`), so Terraform always regenerates the resource and its client certificate.
Simply re-running the target is sufficient:

```bash
make infra-stackit-foundation-fetch-kubeconfig
```

**If you are on a blueprint version prior to v1.12.3**, apply the workaround manually:

```bash
terraform -chdir=infra/cloud/stackit/terraform/foundation taint "stackit_ske_kubeconfig.foundation[0]"
make infra-stackit-foundation-fetch-kubeconfig
```

## STACKIT foundation apply fails on transient PostgreSQL Flex `404 Not Found`
- `infra-stackit-foundation-apply` retries a bounded number of times when STACKIT returns the known transient PostgreSQL Flex race:
  - `Requested instance with ID: ... cannot be found`
- Before retrying, the wrapper clears the transient Terraform taint on `stackit_postgresflex_instance.foundation[0]` so the next apply can reconcile the existing managed instance instead of destroying and recreating it.
- The retry budget is controlled by:
  - `STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS` (default `3`)
  - `STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS` (default `30`)
- If the final retry still fails:
  - check `artifacts/infra/stackit_foundation_apply.env`
  - re-run `make infra-stackit-foundation-apply`
  - if the PostgreSQL instance is visible in STACKIT but Terraform still cannot reconcile it, stop and inspect provider/service health before running destroy

## Helm repo update is flaky in live runs
- Helm repository updates are retried with bounded backoff in shared tooling.
- Tune retry budget when running on constrained CI runners or unstable networks:
  - `HELM_REPO_UPDATE_RETRY_MAX_ATTEMPTS` (default `3`)
  - `HELM_REPO_UPDATE_RETRY_BASE_DELAY_SECONDS` (default `2`)
  - `HELM_REPO_UPDATE_RETRY_MAX_DELAY_SECONDS` (default `20`)
  - `HELM_REPO_UPDATE_RETRY_BACKOFF_MULTIPLIER` (default `2`)
- Example:
  ```bash
  HELM_REPO_UPDATE_RETRY_MAX_ATTEMPTS=5 HELM_REPO_UPDATE_RETRY_BASE_DELAY_SECONDS=3 make infra-deploy
  ```

## STACKIT runtime deploy fails on missing `platform-foundation-contract` secret
- Regenerate runtime secret contract from foundation outputs:
  ```bash
  make infra-stackit-foundation-seed-runtime-secret
  ```
- Verify state artifact:
  - `artifacts/infra/stackit_foundation_runtime_secret.env`
- Re-run runtime deploy:
  ```bash
  make infra-stackit-runtime-deploy
  ```

## Runtime credentials ESO reconciliation is not converging
- Run the canonical reconciliation command directly:
  ```bash
  make auth-reconcile-runtime-identity
  ```
- Inspect reconciliation state:
  - `artifacts/infra/runtime_credentials_eso_reconcile.env`
  - `artifacts/infra/argocd_repo_credentials_reconcile.env`
  - `artifacts/infra/runtime_identity_reconcile.env`
- Common failure modes:
  - source secret missing:
    - seed with newline-separated literals before rerunning:
      `export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS=$'username=...\npassword=...'`
      (see [Runtime Credentials (ESO)](runtime_credentials_eso.md) for format details)
    - or create/manage the source secret with your provider-backed store path
  - `ExternalSecret` not `Ready=True`:
    - confirm ESO CRDs are established (`clustersecretstores.external-secrets.io`, `externalsecrets.external-secrets.io`)
    - confirm the referenced store (`runtime-credentials-source-store`) exists and authenticates correctly
  - target secret missing keys:
    - verify `RUNTIME_CREDENTIALS_TARGET_SECRET_KEYS` matches the key contract expected by workloads
    - verify the source secret contains those keys

For operator workflow details, see [Runtime Credentials (ESO)](runtime_credentials_eso.md).

## STACKIT runtime prerequisites time out waiting for Kubernetes API readiness
- `infra-stackit-runtime-prerequisites` waits for the SKE API hostname to resolve and for `/readyz` to answer before the first `kubectl apply`.
- If it times out on hostname resolution, verify the operator machine can resolve the SKE endpoint handed out in the kubeconfig:
  - `python3 - <<'PY'`
    `import socket`
    `socket.getaddrinfo("api.<cluster>.<suffix>.ske.<region>.onstackit.cloud", None)`
    `PY`
  - or `dig +short <host>`
- If resolution fails from your workstation:
  - confirm you ran `make blueprint-init-repo` before the first STACKIT bootstrap so backend and tfvars placeholders are initialized
  - wait a few minutes and re-run `make infra-stackit-foundation-fetch-kubeconfig`
  - check whether corporate DNS, VPN, or local resolver policy is blocking `*.ske.<region>.onstackit.cloud`
- Inspect `artifacts/infra/stackit_runtime_prerequisites.env` for the recorded `kube_api_server` and readiness status before retrying deploy.

## AGENTS.md structure check fails after blueprint upgrade

After a blueprint upgrade that introduces the AGENTS.md ↔ north_star.md anti-duplication
contract, `make quality-hooks-fast` may fail with:

```
[quality-docs-agents-md-structure-check] missing required section: ## Architecture Invariants — Pointers
[quality-docs-agents-md-structure-check] missing north_star.md reference within ## Mandatory Workflow section
```

**Why this happens**: the `quality-docs-agents-md-structure-check` hook enforces two structural
elements required by the AGENTS.md ↔ north_star.md contract. Consumer `AGENTS.md` files created
before this blueprint upgrade do not contain these elements.

**Remediation**:

1. Open your consumer repo's `AGENTS.md`.
2. Add the `## Architecture Invariants — Pointers` section **before** `## Mandatory Workflow`.
   Use `scripts/templates/consumer/init/AGENTS.md.tmpl` as a reference (the section is
   self-documenting). Minimum content:
   ```markdown
   ## Architecture Invariants — Pointers

   AGENTS.md does NOT contain architecture content. Architecture decisions and domain
   invariants live exclusively in `docs/platform/architecture/north_star.md` and the
   relevant ADRs under `docs/platform/architecture/decisions/`. Inlining architecture
   content here creates silent duplication that drifts without automated enforcement.

   Add one row per cross-cutting concern. The **Domain** name MUST match the exact
   `north_star.md` heading text so the cross-reference hook correctly identifies
   sanctioned navigation pointers.

   | Domain | `north_star.md` section | Canonical ADR(s) |
   |---|---|---|
   ```
   Add one row per cross-cutting concern relevant to your repository. Leave the table
   empty if no cross-cutting concerns are documented yet — an empty table satisfies
   the structural contract.
3. Add a `north_star.md` Mandatory Workflow rule inside your `## Mandatory Workflow` section.
   Reference the template for exact wording. At minimum, add:
   > Before any SDD work item touching a domain covered in
   > `docs/platform/architecture/north_star.md`, MUST read the relevant `north_star.md`
   > section and the canonical ADR(s) cited in the Pointers table above. MUST NOT
   > duplicate architecture content from `north_star.md` in `AGENTS.md`.
4. Run `make quality-docs-agents-md-structure-check` to confirm the check passes.
5. Run `make quality-hooks-fast` to confirm no regression in the full hook chain.

For background on the two-check enforcement model, see
`docs/blueprint/governance/quality_hooks.md` § *AGENTS.md ↔ north_star.md Checks*.

## STACKIT test resources still need cleanup
- Run the canonical destroy chain:
  ```bash
  make infra-stackit-destroy-all
  ```
- The destroy flow performs a best-effort delete of blueprint-managed namespaces before Terraform destroys the SKE cluster:
  - `apps`, `data`, `messaging`, `network`, `security`, `observability`
  - controller namespaces such as `argocd`, `external-secrets`, and `envoy-gateway-system`
- If a cluster still reports `STATE_DELETING` after that:
  - inspect whether Kubernetes access is still available with `kubectl get ns`
  - if access is still available, look for namespaces stuck in `Terminating` and remaining `LoadBalancer` services or Gateway resources
  - then retry `make infra-stackit-destroy-all` after those in-cluster resources are gone
