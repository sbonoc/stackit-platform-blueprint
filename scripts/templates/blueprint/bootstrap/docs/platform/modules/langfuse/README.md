# Langfuse Module (Optional)

## Purpose
Deploy Langfuse with app-level OIDC and wire runtime for LLM observability.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `LANGFUSE_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `LANGFUSE_ENABLED=true`.
- Runtime deployment intent is managed via ArgoCD optional manifests:
  - `infra/gitops/argocd/optional/<env>/langfuse.yaml`
- Local Helm values are maintained in:
  - `infra/local/helm/langfuse/values.yaml`

## Enable
Set:

```bash
export LANGFUSE_ENABLED=true
```

## Required Inputs
- `LANGFUSE_PUBLIC_DOMAIN` (example: `dhe-langfuse-dev.runs.onstackit.cloud`)
- `LANGFUSE_OIDC_ISSUER_URL`
- `LANGFUSE_OIDC_CLIENT_ID`
- `LANGFUSE_OIDC_CLIENT_SECRET`
- `LANGFUSE_DATABASE_URL`
- `LANGFUSE_SALT`
- `LANGFUSE_ENCRYPTION_KEY`
- `LANGFUSE_NEXTAUTH_SECRET`

## Commands
- `make infra-langfuse-plan`
- `make infra-langfuse-apply`
- `make infra-langfuse-deploy`
- `make infra-langfuse-smoke`
- `make infra-langfuse-destroy`

## Smoke Expectations
- Pods healthy
- OIDC login works
- New traces contain non-empty input/output fields
