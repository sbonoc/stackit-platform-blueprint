# Public Endpoints Module (Optional)

## Purpose
Provision Gateway API public edge baseline for marketplace UI and API surfaces.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `PUBLIC_ENDPOINTS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `PUBLIC_ENDPOINTS_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles Envoy Gateway (`gateway-helm`) from `infra/gitops/argocd/optional/${ENV}/public-endpoints.yaml`, and the same rendered manifest seeds the shared `GatewayClass`/`Gateway` baseline for route attachment.
- `local-*` profiles: Helm chart (`oci://docker.io/envoyproxy/gateway-helm`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/public-endpoints/values.yaml`, and the wrapper applies the rendered shared `GatewayClass`/`Gateway` manifest artifact.
- The controller chart does not own the shared `Gateway` resource. The blueprint renders that baseline separately so the route contract remains explicit and reviewable in repo-managed manifests.
- The shared `Gateway` listener allows cross-namespace `HTTPRoute` attachment so touchpoints, backend routes, and browser-authenticated proxy routes can attach without forcing all traffic through one auth mode.
- Auth remains route-specific on top of this shared edge: some hosts can stay public, some can route through `identity-aware-proxy`, and API routes can evolve independently.

## Enable
```bash
export PUBLIC_ENDPOINTS_ENABLED=true
```

## Required Inputs
- `PUBLIC_ENDPOINTS_BASE_DOMAIN`

## Optional Inputs
- `PUBLIC_ENDPOINTS_NAMESPACE`
- `PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE`
- `PUBLIC_ENDPOINTS_GATEWAY_NAME`
- `PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME`
- `PUBLIC_ENDPOINTS_HELM_RELEASE`
- `PUBLIC_ENDPOINTS_HELM_CHART`
- `PUBLIC_ENDPOINTS_HELM_CHART_VERSION`

## Commands
- `make infra-public-endpoints-plan`
- `make infra-public-endpoints-apply`
- `make infra-public-endpoints-smoke`
- `make infra-public-endpoints-destroy`

## Outputs
- `PUBLIC_ENDPOINTS_BASE_DOMAIN`
- `PUBLIC_ENDPOINTS_GATEWAY_NAME`
- `PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME`
- `PUBLIC_ENDPOINTS_NAMESPACE`
