# Public Endpoints Module (Optional)

## Purpose
Provision ingress/public endpoint baseline for marketplace UI and API surfaces.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `PUBLIC_ENDPOINTS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `PUBLIC_ENDPOINTS_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles `ingress-nginx/ingress-nginx` from `infra/gitops/argocd/optional/${ENV}/public-endpoints.yaml`.
- `local-*` profiles: Helm chart (`ingress-nginx/ingress-nginx`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/public-endpoints/values.yaml`.

## Enable
```bash
export PUBLIC_ENDPOINTS_ENABLED=true
```

## Required Inputs
- `PUBLIC_ENDPOINTS_BASE_DOMAIN`

## Commands
- `make infra-public-endpoints-plan`
- `make infra-public-endpoints-apply`
- `make infra-public-endpoints-smoke`
- `make infra-public-endpoints-destroy`

## Outputs
- `PUBLIC_ENDPOINTS_BASE_DOMAIN`
- `PUBLIC_ENDPOINTS_INGRESS_CLASS`
