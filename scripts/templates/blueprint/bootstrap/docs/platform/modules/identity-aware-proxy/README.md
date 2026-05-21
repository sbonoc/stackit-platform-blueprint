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

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `IAP_UPSTREAM_URL` | Yes | — | Upstream service URL that the proxy forwards authenticated requests to (e.g. `http://catalog.apps.svc.cluster.local:8080`). |
| `IAP_COOKIE_SECRET` | Yes | — | AES-GCM session cookie encryption key. MUST be exactly 16, 24, or 32 bytes; any other length is a hard failure at plan time. |
| `KEYCLOAK_ISSUER_URL` | Yes | — | Keycloak realm OIDC issuer URL (e.g. `https://keycloak.example.com/realms/myrealm`). |
| `KEYCLOAK_CLIENT_ID` | Yes | — | Keycloak OIDC client identifier registered for this proxy. |
| `KEYCLOAK_CLIENT_SECRET` | Yes | — | Keycloak OIDC client secret. Never written to state files or log output. |
| `IAP_PUBLIC_HOST` | No | `iap.local` | Public hostname the `HTTPRoute` attaches to on the shared Gateway. |
| `IAP_NAMESPACE` | No | `security` | Kubernetes namespace where the proxy Helm release is deployed. |
| `IAP_HELM_RELEASE` | No | `blueprint-iap` | Helm release name. The runtime credential Secret is named `${IAP_HELM_RELEASE}-config`. |
| `IAP_HELM_CHART` | No | `oauth2-proxy/oauth2-proxy` | Helm chart reference. |
| `IAP_HELM_CHART_VERSION` | No | `10.4.0` | Pinned chart version. Override only to upgrade intentionally. |
| `PUBLIC_ENDPOINTS_NAMESPACE` | No | `network` | Namespace of the shared Gateway resource provided by `public-endpoints`. |
| `PUBLIC_ENDPOINTS_GATEWAY_NAME` | No | `public-endpoints` | Name of the shared Gateway resource the `HTTPRoute` attaches to. |

## Make Targets

| Target | Description | State file keys written |
|---|---|---|
| `infra-identity-aware-proxy-plan` | Validates all required inputs (including `IAP_COOKIE_SECRET` byte-length check), resolves the provisioning driver (`helm` or `argocd`), and writes plan state. | `identity_aware_proxy_plan`: `provision_driver`, `provision_path`, `public_host`, `public_url`, `upstream_url`, `gateway_name`, `gateway_namespace`, `keycloak_issuer`, `keycloak_client_id` |
| `infra-identity-aware-proxy-apply` | Reconciles the runtime credential Secret on the target lane and writes apply state. | `identity_aware_proxy_runtime`: `provision_status`, `auth_mode=browser_oidc_proxy`, `route_mode=gateway_api` |
| `infra-identity-aware-proxy-deploy` | Installs or syncs the `oauth2-proxy/oauth2-proxy` Helm release (local lane) or ArgoCD Application (STACKIT lane). | — |
| `infra-identity-aware-proxy-smoke` | Asserts OIDC issuer/client contract and protected browser route reachability through the shared Gateway. | `identity_aware_proxy_smoke`: `status=passed` |
| `infra-identity-aware-proxy-destroy` | Removes the Helm release or ArgoCD Application, the credential Secret, and all `identity_aware_proxy_*` state files. | — |

All five targets exit 0 without side effects when `IDENTITY_AWARE_PROXY_ENABLED=false`.

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

## Provisioning Lifecycle

> **Prerequisite — Keycloak OIDC client**
> Create an OIDC client in your Keycloak realm before running the lifecycle. Set the allowed redirect URI to:
> ```
> https://${IAP_PUBLIC_HOST}/oauth2/callback
> ```
> Record the client ID and client secret — they are required inputs below.

### 1. Enable the module

Set `IDENTITY_AWARE_PROXY_ENABLED=true` in your environment profile, then re-render the Makefile so the lifecycle targets are available:

```bash
make blueprint-render-makefile
```

### 2. Export required environment variables

```bash
export IAP_UPSTREAM_URL="http://catalog.apps.svc.cluster.local:8080"
export IAP_COOKIE_SECRET="<16, 24, or 32 byte secret>"
export KEYCLOAK_ISSUER_URL="https://keycloak.example.com/realms/myrealm"
export KEYCLOAK_CLIENT_ID="iap-proxy"
export KEYCLOAK_CLIENT_SECRET="<client secret from Keycloak>"
```

### 3. Run the lifecycle in order

```bash
make infra-identity-aware-proxy-plan
make infra-identity-aware-proxy-apply
make infra-identity-aware-proxy-deploy
make infra-identity-aware-proxy-smoke
```

Each target exits 0 on success. The smoke target confirms the OIDC issuer/client contract and protected browser route reachability through the shared Gateway.

### STACKIT lane — update ArgoCD manifests before syncing

On `stackit-*` profiles the deploy step applies the ArgoCD Application manifests in `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml`. These manifests ship with scaffold placeholder values and **must be updated** before ArgoCD reconciles the chart:

| Field | Location in manifest | Replace with |
|---|---|---|
| `oidcIssuerURL` | `spec.source.helm.values` | Your Keycloak realm issuer URL (value of `KEYCLOAK_ISSUER_URL`) |
| `redirect-url` (extraArgs) | `spec.source.helm.values` | `https://${IAP_PUBLIC_HOST}/oauth2/callback` |
| `upstreams` | `spec.source.helm.values` | Your upstream service URL (value of `IAP_UPSTREAM_URL`) |
| `hostnames` | `spec.source.helm.values` | Your public host (value of `IAP_PUBLIC_HOST`) |

The `config.existingSecret` field is pre-set to `iap-runtime-credentials` and matches the ESO-issued Secret name — do not change it.

## Security

- **`IAP_COOKIE_SECRET` byte-length constraint.** The value MUST be exactly 16, 24, or 32 bytes, matching the AES-GCM key sizes supported by oauth2-proxy's session cookie encryption. `identity_aware_proxy_validate_cookie_secret()` enforces this at plan time; any other length produces a hard failure before any resources are created.
- **Credential non-persistence.** `KEYCLOAK_CLIENT_SECRET` and `IAP_COOKIE_SECRET` are NEVER written to any state file or log output. Plan state (`identity_aware_proxy_plan`) and smoke state (`identity_aware_proxy_smoke`) contain only non-sensitive keys (`keycloak_client_id`, `public_host`, `status`, etc.).
- **Local lane credential delivery.** `identity_aware_proxy_reconcile_runtime_secret()` creates a Kubernetes Secret named `${IAP_HELM_RELEASE}-config` (default: `blueprint-iap-config`) in `${IAP_NAMESPACE}` (default: `security`). This Secret holds `client-id`, `client-secret`, and `cookie-secret` and is consumed by the Helm chart at deploy time.
- **STACKIT lane credential delivery.** The ArgoCD Application sources credentials from an ESO-issued `security/iap-runtime-credentials` Secret, following the platform-wide ESO credential delivery pattern. Credentials are not stored in ArgoCD manifests or GitOps-tracked files.

## Teardown

```bash
make infra-identity-aware-proxy-destroy
```

The destroy script removes:
- The `oauth2-proxy/oauth2-proxy` Helm release (local lane) or ArgoCD Application (STACKIT lane).
- The Kubernetes credential Secret (`${IAP_HELM_RELEASE}-config` on the local lane; `security/iap-runtime-credentials` is managed by ESO and is not removed by this script on the STACKIT lane).
- All `identity_aware_proxy_*` state files in `.state/`.
