# Identity-Aware Proxy Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision browser-facing identity-aware access proxy wired to Keycloak OIDC for protected touchpoint routes.
- Enable flag: `IDENTITY_AWARE_PROXY_ENABLED` (default: `false`)
- Required inputs:
  - `IAP_UPSTREAM_URL`
  - `IAP_COOKIE_SECRET`
  - `KEYCLOAK_ISSUER_URL`
  - `KEYCLOAK_CLIENT_ID`
  - `KEYCLOAK_CLIENT_SECRET`
- Make targets:
  - `infra-identity-aware-proxy-plan`
  - `infra-identity-aware-proxy-apply`
  - `infra-identity-aware-proxy-deploy`
  - `infra-identity-aware-proxy-smoke`
  - `infra-identity-aware-proxy-destroy`
- Outputs:
  - `IAP_PUBLIC_URL`
  - `IAP_PUBLIC_HOST`
  - `IAP_UPSTREAM_URL`
  - `IAP_OIDC_ISSUER`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles `oauth2-proxy/oauth2-proxy` from `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml`, with OIDC credentials sourced from ESO-issued `security/iap-runtime-credentials`, and the chart creating an `HTTPRoute` that attaches to the shared Gateway baseline from `public-endpoints`.
- `local-*` profiles: Helm chart (`oauth2-proxy/oauth2-proxy`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/identity-aware-proxy/values.yaml`, and the chart creates the same Gateway API `HTTPRoute` locally.
- This module is intentionally browser-oriented: it protects selected touchpoint hosts with OIDC login/session flow and should not be treated as the universal front door for public or bearer-token APIs.
- Public touchpoints and direct API routes can coexist with this module. Only the protected browser hosts that opt into the proxy should route through it.
- See [Endpoint Exposure Model](../../consumer/endpoint_exposure_model.md) for the broader mixed-route policy model around this browser-authenticated path.

## Optional Inputs
- `IAP_PUBLIC_HOST`
- `IAP_NAMESPACE`
- `IAP_HELM_RELEASE`
- `IAP_HELM_CHART`
- `IAP_HELM_CHART_VERSION`
- `PUBLIC_ENDPOINTS_NAMESPACE`
- `PUBLIC_ENDPOINTS_GATEWAY_NAME`

## OIDC Contract
- Keycloak is the core identity capability.
- This module requires Keycloak issuer and client configuration.
- `public-endpoints` must provide the shared Gateway baseline that the route attaches to.
- OIDC issuer/client mismatch is a hard failure in smoke checks.
- Local and fallback runtime paths pin the `oauth2-proxy` image explicitly so browser-authenticated routes do not drift with chart defaults.
