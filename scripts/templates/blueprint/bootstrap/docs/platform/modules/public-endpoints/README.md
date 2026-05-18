# Public Endpoints Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision Gateway API public edge baseline for consumer application UI, API, and auth surfaces.
- Enable flag: `PUBLIC_ENDPOINTS_ENABLED` (default: `false`)
- Required inputs:
  - `PUBLIC_ENDPOINTS_BASE_DOMAIN`
- Make targets:
  - `infra-public-endpoints-plan`
  - `infra-public-endpoints-apply`
  - `infra-public-endpoints-deploy`
  - `infra-public-endpoints-smoke`
  - `infra-public-endpoints-destroy`
- Outputs:
  - `PUBLIC_ENDPOINTS_BASE_DOMAIN`
  - `PUBLIC_ENDPOINTS_GATEWAY_NAME`
  - `PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME`
  - `PUBLIC_ENDPOINTS_NAMESPACE`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `PUBLIC_ENDPOINTS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `PUBLIC_ENDPOINTS_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles Envoy Gateway (`gateway-helm`) from `infra/gitops/argocd/optional/${ENV}/public-endpoints.yaml`, and the wrapper waits for the Gateway API CRDs before applying the separately rendered shared `GatewayClass`/`Gateway` baseline artifact.
- `local-*` profiles: Helm chart (`oci://docker.io/envoyproxy/gateway-helm`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/public-endpoints/values.yaml`, and the wrapper applies the rendered shared `GatewayClass`/`Gateway` manifest artifact.
- The controller chart does not own the shared `Gateway` resource. The blueprint renders that baseline separately so the route contract stays explicit and reviewable in repo-managed manifests.
- The shared edge reconciles through a dedicated `platform-edge-<env>` Argo CD project so `GatewayClass`/shared `Gateway` resources stay isolated from app-route policy resources.
- The shared `Gateway` lives in the `network` namespace, which comes from the platform GitOps baseline so route attachments have a stable home across environments.
- The shared `Gateway` listener allows cross-namespace `HTTPRoute` attachment so touchpoints, backend routes, and browser-authenticated proxy routes can attach without forcing all traffic through one auth mode.
- Auth is route-specific on top of this shared edge: some hosts can stay public, some can route through `identity-aware-proxy`, and API routes can evolve independently.
- See [Endpoint Exposure Model](../../consumer/endpoint_exposure_model.md) for the mixed public/protected route classes that sit on top of this shared edge.
- See [Protected API Routes](../../consumer/protected_api_routes.md) for the consumer-owned JWT route policy pattern that sits behind the shared edge.

## Optional Inputs
- `PUBLIC_ENDPOINTS_NAMESPACE`
- `PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE`
- `PUBLIC_ENDPOINTS_GATEWAY_NAME`
- `PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME`
- `PUBLIC_ENDPOINTS_HELM_RELEASE`
- `PUBLIC_ENDPOINTS_HELM_CHART`
- `PUBLIC_ENDPOINTS_HELM_CHART_VERSION`
- `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME` (default: `letsencrypt-public-endpoints`)
- `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL` (required for STACKIT profiles using ACME)
- `PUBLIC_ENDPOINTS_ACME_SERVER` (profile-aware default — see TLS Stack Execution Model)
- `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` (default: `public-endpoints-gateway-tls`)

## TLS Stack Execution Model

The HTTPS listener requires a TLS certificate issued by cert-manager. The blueprint renders four additional resources alongside the `GatewayClass`/`Gateway` baseline:

1. **Issuer** (`public-endpoints.issuer.yaml`) — a namespace-scoped cert-manager `Issuer`. For `stackit-*` profiles this is an ACME issuer using HTTP01 challenges routed through the shared `Gateway`. For `local-*` profiles this is a `selfSigned` issuer.
2. **Certificate** (`public-endpoints.certificate.yaml`) — a cert-manager `Certificate` resource that references the `Issuer` and produces the TLS secret consumed by the `Gateway` HTTPS listener.
3. **ClientTrafficPolicy** (embedded in `public-endpoints.yaml.tmpl`) — enforces TLS 1.2 minimum and prohibits TLS 1.0/1.1 on the HTTPS listener.
4. **NetworkPolicy** manifests (`public-endpoints.networkpolicy.yaml`) — default-deny ingress for the `network` namespace with explicit allow for Envoy proxy pods on ports 80/443 and for cert-manager ACME HTTP01 challenge traffic.

The `Gateway` HTTPS listener references the TLS secret by name. cert-manager provisions and renews the secret automatically. The `renewBefore: 720h` field ensures renewal begins 30 days before expiry.

### Profile-Aware ACME Server

| Profile | ACME Server |
|---|---|
| `stackit-dev`, `stackit-stage` | `https://acme-staging-v02.api.letsencrypt.org/directory` (staging CA, not browser-trusted) |
| `stackit-prod` | `https://acme-v02.api.letsencrypt.org/directory` (production CA, browser-trusted) |
| `local-*` | N/A — `selfSigned` issuer used instead |

Using staging ACME for non-prod profiles avoids Let's Encrypt production rate limits and prevents the HSTS pinning risk from reaching browser trust stores during development.

## TLS Secret RBAC Constraint (NFR-SEC-003)

The TLS secret produced by cert-manager is accessible only by the Envoy Gateway controller service account. Consumer application service accounts must not reference this secret directly. Consumers attach `HTTPRoute` resources to the shared `Gateway` listeners — they do not manage TLS termination.

## HTTP Plain-Text Security Trade-Off (NFR-SEC-005)

Port 80 remains open on the shared `Gateway` to support ACME HTTP01 challenges and to allow consumer `HTTPRoute` authors to implement redirect-to-HTTPS logic. Consumer HTTPRoute authors are responsible for restricting sensitive routes to the HTTPS listener. The blueprint does not enforce HTTPS-only at the gateway level because some ACME challenge paths must be plain-text.

## HSTS Policy (NFR-SEC-006)

Envoy Gateway 1.x does not support gateway-level `Strict-Transport-Security` injection via `BackendTrafficPolicy` or `ClientTrafficPolicy`. Gateway-wide HSTS via `EnvoyPatchPolicy` is parked for a follow-up work item (see `AGENTS.backlog.md`).

Consumer `HTTPRoute` authors should add HSTS using a `ResponseHeaderModifier` filter on their HTTPS routes:

```yaml
filters:
  - type: ResponseHeaderModifier
    responseHeaderModifier:
      add:
        - name: Strict-Transport-Security
          value: "max-age=31536000; includeSubDomains"
```

For `stackit-prod`, once a browser pins the HSTS header the domain cannot serve plain-text HTTP for at least one year without breaking browser access. For `stackit-dev` and `stackit-stage`, the staging ACME CA is not browser-trusted, so HSTS pinning does not propagate to user browsers.

## Network Isolation (NFR-SEC-007)

Three `NetworkPolicy` resources are rendered in the `network` namespace:

1. **default-deny-ingress** — denies all ingress to all pods in the namespace unless explicitly permitted.
2. **allow-public-https** — permits inbound TCP on ports 80 and 443 to Envoy proxy pods (`app.kubernetes.io/component: proxy`).
3. **allow-certmanager-acme** — permits inbound TCP on port 80 from the `cert-manager` namespace to Envoy proxy pods, allowing ACME HTTP01 challenge traffic.

## KMS Dependency (NFR-SEC-008)

For `stackit-stage` and `stackit-prod` profiles, the KMS module must be enabled to encrypt the TLS secret and the ACME account private key at rest. Without KMS, the `public_endpoints_apply.sh` script emits a `log_warn` but does not fail — the operator must act on this warning before deploying to production. Enable the KMS module by setting `KMS_ENABLED=true`.

## Certificate Renewal and Expiry Monitoring (NFR-OBS-002)

The `Certificate` manifest includes `renewBefore: 720h` (30 days). cert-manager will attempt renewal 30 days before the certificate expires. Monitoring of cert-manager renewal failures is deferred to the observability module. Operators should configure alerting on cert-manager `CertificateRequest` failures and on expiring certificates.

## Destroy Warning (NFR-REL-001)

The destroy script deletes resources in this order to avoid orphaned finalizers:

1. `Certificate` — removed first so cert-manager stops managing the TLS secret.
2. `Issuer` — removed after the Certificate is gone.
3. `NetworkPolicy` resources — removed to prevent blocking ingress if the namespace is reused.
4. Gateway baseline (GatewayClass/Gateway) — removed last.

During destroy, existing TLS sessions terminate as Envoy Gateway removes the listener. Plan a maintenance window before destroying in production environments.
