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
- Re-run bootstrap with Workflows disabled to prune stale scaffolding, then re-validate:
  ```bash
  WORKFLOWS_ENABLED=false make blueprint-render-makefile
  WORKFLOWS_ENABLED=false make infra-bootstrap
  WORKFLOWS_ENABLED=false make infra-validate
  ```

## Disabled module but resources still exist
- Disabling an optional module only prunes scaffolding and targets from the repository.
- Already provisioned resources are not destroyed automatically.
- Run disabled-module teardown first, then prune scaffolding:
  ```bash
  make infra-destroy-disabled-modules
  WORKFLOWS_ENABLED=false make blueprint-render-makefile
  WORKFLOWS_ENABLED=false make infra-bootstrap
  ```
- If you prefer explicit module-level teardown, run the module destroy target directly while the module flag is still enabled.

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
