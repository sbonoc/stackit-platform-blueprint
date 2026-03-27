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
set -a
source blueprint/repo.init.example.env
set +a
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

## 3) Bootstrap and Validate
```bash
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
```

## 4) Optional Consumer Smoke
```bash
make blueprint-template-smoke
```

`make blueprint-template-smoke` respects exported `BLUEPRINT_PROFILE` and optional-module flags, so you can dry-run the exact generated-repo scenario you want to validate before provisioning live infrastructure.

## 5) Continue with Delivery Flow
```bash
make infra-provision-deploy
make infra-status-json
```

`make infra-provision-deploy` already runs the canonical smoke stage and writes
`artifacts/infra/smoke_result.json` plus `artifacts/infra/smoke_diagnostics.json`.
`make infra-status-json` captures the latest consolidated snapshot at
`artifacts/infra/infra_status_snapshot.json`.

Before publishing hosts or API routes, review [Endpoint Exposure Model](endpoint_exposure_model.md)
so public UI, protected UI, direct APIs, and internal SSR/BFF flows stay separated intentionally.
If you plan to expose bearer-token APIs on the shared edge, review
[Protected API Routes](protected_api_routes.md) before attaching JWT policy resources.

## 6) STACKIT MVP Provision/Deploy (Optional)
For managed STACKIT execution (`BLUEPRINT_PROFILE=stackit-dev|stackit-stage|stackit-prod`), export:
- `STACKIT_PROJECT_ID`
- `STACKIT_REGION` (for example `eu01`)
- `STACKIT_SERVICE_ACCOUNT_KEY`
- `STACKIT_TFSTATE_ACCESS_KEY_ID`
- `STACKIT_TFSTATE_SECRET_ACCESS_KEY`

These values should align with initialized blueprint values:
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
```

`infra-deploy` / `infra-stackit-runtime-deploy` already call
`infra-stackit-foundation-seed-runtime-secret` automatically; running it explicitly
is useful for debugging foundation output-to-runtime contract wiring.
