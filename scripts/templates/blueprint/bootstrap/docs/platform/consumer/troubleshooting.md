# Troubleshooting

Common first-day issues for generated repositories.

## `make blueprint-init-repo` fails
- Ensure required variables are exported:
  - `BLUEPRINT_REPO_NAME`
  - `BLUEPRINT_GITHUB_ORG`
  - `BLUEPRINT_GITHUB_REPO`
  - `BLUEPRINT_DEFAULT_BRANCH`
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

## Template smoke fails in CI
- Ensure required local tools are available (`bash`, `git`, `make`, `python3`, `tar`).
- Confirm CI job exports init variables before `make blueprint-template-smoke`.
