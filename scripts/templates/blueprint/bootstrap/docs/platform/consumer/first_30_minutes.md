# First 30 Minutes

This guide helps template consumers get from clone to validated baseline quickly.

## 0) Preconditions
- You created the repository via GitHub **Use this template**.
- You cloned the generated repository locally.
- You have `bash`, `git`, `make`, and `python3` installed.

## 1) Initialize Repository Identity (5 min)
Interactive mode:
```bash
make blueprint-init-repo-interactive
```

CI/non-interactive mode:
```bash
set -a
source blueprint/repo.init.example.env
set +a
make blueprint-init-repo
```

Expected outcome:
- `blueprint/contract.yaml` metadata is updated for your repository identity.
- `docs/docusaurus.config.js` owner/repo/edit links are aligned.

## 2) Bootstrap Template and Infra Scaffolding (10 min)
```bash
make blueprint-bootstrap
make infra-bootstrap
```

Expected outcome:
- `make/blueprint.generated.mk` is rendered for current module flags.
- Optional scaffolding is materialized or pruned based on enabled flags.

## 3) Validate Baseline (10 min)
```bash
make infra-validate
make infra-smoke
```

Expected outcome:
- Contract, structure, and docs/template sync checks pass.
- Baseline infra smoke artifacts are written under `artifacts/infra/`, including `smoke_result.json` and `smoke_diagnostics.json`.
- App/docs smoke artifacts are written under `artifacts/apps/` and `artifacts/docs/`.

## 4) Next Steps (5 min)
- Run `make infra-status-json` to capture the latest machine-readable runtime snapshot at `artifacts/infra/infra_status_snapshot.json`.
- Review [Quickstart](quickstart.md) for full flow.
- Review [Endpoint Exposure Model](endpoint_exposure_model.md) before exposing mixed public/protected UI or API routes.
- Review [Troubleshooting](troubleshooting.md) if any command fails.
- Review [Upgrade Runbook](upgrade_runbook.md) before applying template upgrades later.
