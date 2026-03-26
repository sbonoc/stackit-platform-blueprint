# Identity-Aware Proxy Module (Optional)

## Purpose
Provision identity-aware access proxy capability and enforce Keycloak OIDC integration for protected marketplace routes.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `IDENTITY_AWARE_PROXY_ENABLED=true`.
- `stackit-*` profiles: runtime reconciliation through ArgoCD optional manifest `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml`.
- `local-*` profiles: Helm chart (`oauth2-proxy/oauth2-proxy`) using `infra/local/helm/identity-aware-proxy/values.yaml`.

## Enable
```bash
export IDENTITY_AWARE_PROXY_ENABLED=true
```

## Required Inputs
- `IAP_UPSTREAM_URL`
- `KEYCLOAK_ISSUER_URL`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_CLIENT_SECRET`

## OIDC Contract
- Keycloak remains a core capability.
- This module requires Keycloak issuer and client configuration.
- OIDC issuer/client mismatch is a hard failure in smoke checks.

## Commands
- `make infra-identity-aware-proxy-plan`
- `make infra-identity-aware-proxy-apply`
- `make infra-identity-aware-proxy-smoke`
- `make infra-identity-aware-proxy-destroy`

## Outputs
- `IAP_PUBLIC_URL`
- `IAP_UPSTREAM_URL`
- `IAP_OIDC_ISSUER`
