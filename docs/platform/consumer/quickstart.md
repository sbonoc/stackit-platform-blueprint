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

## 5) Continue with Delivery Flow
```bash
make infra-provision-deploy
make infra-smoke
```
