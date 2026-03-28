# Langfuse Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Deploy Langfuse with OIDC authentication and LLM observability wiring.
- Enable flag: `LANGFUSE_ENABLED` (default: `false`)
- Required inputs:
  - `LANGFUSE_PUBLIC_DOMAIN`
  - `LANGFUSE_OIDC_ISSUER_URL`
  - `LANGFUSE_OIDC_CLIENT_ID`
  - `LANGFUSE_OIDC_CLIENT_SECRET`
  - `LANGFUSE_DATABASE_URL`
  - `LANGFUSE_SALT`
  - `LANGFUSE_ENCRYPTION_KEY`
  - `LANGFUSE_NEXTAUTH_SECRET`
- Make targets:
  - `infra-langfuse-plan`
  - `infra-langfuse-apply`
  - `infra-langfuse-deploy`
  - `infra-langfuse-smoke`
  - `infra-langfuse-destroy`
- Outputs:
  - `LANGFUSE_PUBLIC_URL`
  - `LANGFUSE_HEALTH_STATUS`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `LANGFUSE_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `LANGFUSE_ENABLED=true`.
- Runtime deployment intent is managed via ArgoCD optional manifests:
  - `infra/gitops/argocd/optional/<env>/langfuse.yaml`
- Local Helm values are maintained in:
  - `infra/local/helm/langfuse/values.yaml`

## Smoke Expectations
- Pods healthy
- OIDC login works
- New traces contain non-empty input/output fields
