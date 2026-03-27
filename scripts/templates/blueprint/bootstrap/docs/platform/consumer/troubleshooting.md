# Troubleshooting

Common first-day issues for generated repositories.

## `make blueprint-init-repo` fails
- Ensure required variables are exported:
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

## `make blueprint-init-repo-interactive` fails in CI
- The interactive target requires a TTY terminal.
- In CI/non-interactive shells, use env-file mode with `make blueprint-init-repo`.

## `make infra-validate` fails with branch naming errors
- Branch names must match contract prefixes (for example `feature/...`, `fix/...`, `chore/...`, `docs/...`).
- If running in CI, ensure `GITHUB_HEAD_REF`/`GITHUB_REF_NAME` is available or set `BLUEPRINT_BRANCH_NAME`.

## `make blueprint-check-placeholders` fails
- Re-run `make blueprint-init-repo` with correct values.
- Confirm contract and docs identity values match your repository owner/name.

## `dags/` appears unexpectedly
- `dags/` should exist only when `WORKFLOWS_ENABLED=true`.
- If `WORKFLOWS_ENABLED=false` but `dags/` is still present, treat it as repository state drift and re-sync from the blueprint templates, then re-validate:
  ```bash
  git restore dags infra/cloud/stackit/terraform/modules/workflows tests/infra/modules/workflows
  WORKFLOWS_ENABLED=false make blueprint-render-makefile
  WORKFLOWS_ENABLED=false make infra-bootstrap
  WORKFLOWS_ENABLED=false make infra-validate
  ```

## Disabled module but resources still exist
- Disabling an optional module removes its generated Make targets, but scaffold files are intentionally preserved.
- Already provisioned resources are not destroyed automatically.
- Run disabled-module teardown first, then refresh the repo state for the new flag set:
  ```bash
  make infra-destroy-disabled-modules
  WORKFLOWS_ENABLED=false make blueprint-render-makefile
  WORKFLOWS_ENABLED=false make infra-bootstrap
  ```
- If you prefer explicit module-level teardown, run the module destroy target directly while the module flag is still enabled.

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
- Live smoke now fails when blueprint-managed workloads are not healthy.
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

## STACKIT preflight fails on backend contract
- Ensure backend files exist under:
  - `infra/cloud/stackit/terraform/bootstrap/state-backend/<env>.hcl`
  - `infra/cloud/stackit/terraform/foundation/state-backend/<env>.hcl`
- Ensure each backend file contains:
  - `skip_requesting_account_id`
  - `use_path_style`
  - STACKIT object storage endpoint (`object.storage...`)
- Ensure initialized values are coherent:
  - `BLUEPRINT_STACKIT_REGION`
  - `BLUEPRINT_STACKIT_TFSTATE_BUCKET`
  - `BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX`

## STACKIT foundation preflight fails on SKE permission probe
- In execution mode (`DRY_RUN=false`), foundation preflight now probes SKE API access before Terraform apply.
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
- Ensure backend bucket exists and matches initialized identity:
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
- `infra-stackit-foundation-apply` now retries a bounded number of times when STACKIT returns the known transient PostgreSQL Flex race:
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

## STACKIT runtime prerequisites time out waiting for Kubernetes API readiness
- `infra-stackit-runtime-prerequisites` now waits for the SKE API hostname to resolve and for `/readyz` to answer before the first `kubectl apply`.
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
- If a cluster remains in `STATE_DELETING`, inspect whether in-cluster resources are still attached and retry the destroy after provider-side cleanup finishes.
