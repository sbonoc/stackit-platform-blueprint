# Public Endpoints Module (Optional)

## Purpose
Provision Gateway API public edge baseline for marketplace UI and API surfaces.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `PUBLIC_ENDPOINTS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `PUBLIC_ENDPOINTS_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles Envoy Gateway (`gateway-helm`) from `infra/gitops/argocd/optional/${ENV}/public-endpoints.yaml`, and the wrapper waits for the Gateway API CRDs before applying the separately rendered shared `GatewayClass`/`Gateway` baseline artifact.
- `local-*` profiles: Helm chart (`oci://docker.io/envoyproxy/gateway-helm`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/public-endpoints/values.yaml`, and the wrapper applies the rendered shared `GatewayClass`/`Gateway` manifest artifact.
- The controller chart does not own the shared `Gateway` resource. The blueprint renders that baseline separately so the route contract remains explicit and reviewable in repo-managed manifests.
- The shared edge reconciles through a dedicated `platform-edge-<env>` Argo CD project so `GatewayClass`/shared `Gateway` resources stay isolated from app-route policy resources.
- The shared `Gateway` lives in the `network` namespace, which is seeded by the platform GitOps baseline so route attachments have a stable home across environments.
- The shared `Gateway` listener allows cross-namespace `HTTPRoute` attachment so touchpoints, backend routes, and browser-authenticated proxy routes can attach without forcing all traffic through one auth mode.
- Auth remains route-specific on top of this shared edge: some hosts can stay public, some can route through `identity-aware-proxy`, and API routes can evolve independently.
- See [Endpoint Exposure Model](../../consumer/endpoint_exposure_model.md) for the mixed public/protected route classes that sit on top of this shared edge.
- See [Protected API Routes](../../consumer/protected_api_routes.md) for the consumer-owned JWT route policy pattern that sits behind the shared edge.

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
