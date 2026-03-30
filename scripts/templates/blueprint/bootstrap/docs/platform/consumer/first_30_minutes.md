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
cp blueprint/repo.init.secrets.example.env blueprint/repo.init.secrets.env
${EDITOR:-vi} blueprint/repo.init.env blueprint/repo.init.secrets.env
make blueprint-init-repo
```

Expected outcome:
- `blueprint/contract.yaml` metadata reflects your repository identity.
- `blueprint/contract.yaml` persists the optional modules you selected during init; later commands use that contract as the default module set unless you override flags explicitly.
- `docs/docusaurus.config.js` owner/repo/edit links match your repository.
- `blueprint/repo.init.env` is tracked for non-sensitive defaults and auto-loaded by later validation/infra commands.
- `blueprint/repo.init.secrets.env` exists locally (gitignored) for sensitive runtime inputs.

## 2) Bootstrap Template and Infra Scaffolding (10 min)
```bash
make blueprint-bootstrap
make infra-bootstrap
```

Expected outcome:
- `make/blueprint.generated.mk` is rendered for current module flags.
- Optional scaffolding is materialized for enabled modules while disabled-module scaffold files stay available for later enablement.

## 3) Validate Baseline (10 min)
```bash
make infra-validate
make infra-smoke
```

Expected outcome:
- Contract, structure, and docs/template sync checks pass.
- Baseline infra smoke artifacts are written under `artifacts/infra/`, including `smoke_result.json`, `smoke_diagnostics.json`, and `workload_health.json`.
- App/docs smoke artifacts are written under `artifacts/apps/` and `artifacts/docs/`.

## 4) Next Steps (5 min)
- Reapply init-owned files only when you mean to: `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`
- Run `make infra-status-json` to capture the latest machine-readable runtime snapshot at `artifacts/infra/infra_status_snapshot.json`.
- For live local runs, `docker-desktop` is preferred automatically when present; run `make infra-context` or set `LOCAL_KUBE_CONTEXT` before provisioning if you want a different cluster.
- Review [Quickstart](quickstart.md) for full flow.
- Review [Endpoint Exposure Model](endpoint_exposure_model.md) before exposing mixed public/protected UI or API routes.
- Review [Protected API Routes](protected_api_routes.md) before exposing bearer-token APIs for SPA or direct clients.
- Review [Troubleshooting](troubleshooting.md) if any command fails.
