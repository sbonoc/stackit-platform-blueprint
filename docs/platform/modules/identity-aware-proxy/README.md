# Identity-Aware Proxy Module (Optional)

## Purpose
Provision browser-facing identity-aware access proxy capability and enforce Keycloak OIDC integration for protected touchpoint routes.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles `oauth2-proxy/oauth2-proxy` from `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml`, with OIDC credentials seeded as a Kubernetes Secret and the chart creating an `HTTPRoute` that attaches to the shared Gateway baseline from `public-endpoints`.
- `local-*` profiles: Helm chart (`oauth2-proxy/oauth2-proxy`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/identity-aware-proxy/values.yaml`, and the chart creates the same Gateway API `HTTPRoute` locally.
- This module is intentionally browser-oriented: it protects selected touchpoint hosts with OIDC login/session flow and should not be treated as the universal front door for public or bearer-token APIs.
- Public touchpoints and direct API routes can coexist with this module. Only the protected browser hosts that opt into the proxy should route through it.

## Enable
```bash
export IDENTITY_AWARE_PROXY_ENABLED=true
```

## Required Inputs
- `IAP_UPSTREAM_URL`
- `IAP_COOKIE_SECRET`
- `KEYCLOAK_ISSUER_URL`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET`

## Optional Inputs
- `IAP_PUBLIC_HOST`
- `IAP_NAMESPACE`
- `IAP_HELM_RELEASE`
- `IAP_HELM_CHART`
- `IAP_HELM_CHART_VERSION`
- `PUBLIC_ENDPOINTS_NAMESPACE`
- `PUBLIC_ENDPOINTS_GATEWAY_NAME`

## OIDC Contract
- Keycloak remains a core capability.
- This module requires Keycloak issuer and client configuration.
- `public-endpoints` must provide the shared Gateway baseline that the route attaches to.
- OIDC issuer/client mismatch is a hard failure in smoke checks.

## Commands
- `make infra-identity-aware-proxy-plan`
- `make infra-identity-aware-proxy-apply`
- `make infra-identity-aware-proxy-smoke`
- `make infra-identity-aware-proxy-destroy`

## Outputs
- `IAP_PUBLIC_URL`
- `IAP_PUBLIC_HOST`
- `IAP_UPSTREAM_URL`
- `IAP_OIDC_ISSUER`
