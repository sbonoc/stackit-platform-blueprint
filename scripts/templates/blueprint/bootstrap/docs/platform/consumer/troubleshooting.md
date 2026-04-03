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

## CI warns about deprecated Node 20 GitHub actions
- Upgrade your generated repository to the latest blueprint ref so CI picks up Node-24-ready action majors:
  - `.github/actions/prepare-blueprint-ci/action.yml` (`actions/setup-python@v6`, `actions/setup-node@v6`)
  - `.github/workflows/ci.yml` (`actions/checkout@v6`)
- Use the upgrade flow from the repository root:
  ```bash
  make blueprint-resync-consumer-seeds
  BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
  make blueprint-upgrade-consumer
  BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer
  make blueprint-upgrade-consumer-validate
  ```
- Temporary fallback only if you cannot upgrade immediately:
  - set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` in workflow/job env.

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
  make auth-reconcile-eso-runtime-secrets
  ```
- Inspect reconciliation state:
  - `artifacts/infra/runtime_credentials_eso_reconcile.env`
- Common failure modes:
  - source secret missing:
    - seed with `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS='username=...,password=...'`
      before rerunning
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
