# ADR: Issue #248 — Identity-Aware Proxy Module (Retroactive SDD Compliance)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-21
- **Issue**: #248
- **Work item**: `specs/2026-05-21-issue-248-identity-aware-proxy/`

## Context

The `identity-aware-proxy` optional module was implemented in pre-SDD commits. The full implementation exists:
- Five lifecycle scripts (`plan`, `apply`, `deploy`, `smoke`, `destroy`) in `scripts/bin/infra/`
- `scripts/lib/infra/identity_aware_proxy.sh` with all helper functions
- `blueprint/modules/identity-aware-proxy/module.contract.yaml` with full contract declaration
- `infra/local/helm/identity-aware-proxy/values.yaml` — Helm values scaffold for local lane
- `infra/cloud/stackit/terraform/modules/identity-aware-proxy/main.tf` — TF stub (no provider resources; IAP is Helm/ArgoCD-managed, not provider-backed)
- `infra/gitops/argocd/optional/${ENV}/identity-aware-proxy.yaml` — STACKIT ArgoCD Application manifests

The `oauth2-proxy/oauth2-proxy` Helm chart (version `10.4.0`, image `quay.io/oauth2-proxy/oauth2-proxy:v7.15.0`) is used on both lanes. On the STACKIT lane, the chart reconciles via ArgoCD and sources OIDC credentials from an ESO-issued `security/iap-runtime-credentials` Secret. On the local lane, the chart installs directly via Helm with credentials written to a Kubernetes Secret named `${IAP_HELM_RELEASE}-config` (default: `blueprint-iap-config`) by `identity_aware_proxy_reconcile_runtime_secret()`.

The README existed but was thin — it lacked the environment variable table, make target descriptions, provisioning lifecycle steps, security contract documentation, and teardown section. No spec, ADR, traceability, or PR context artifact existed.

This ADR documents the design decisions already encoded in the implementation and records the rationale for the documentation-only scope of this compliance PR.

## Decisions

### D-1: oauth2-proxy as the IAP implementation — no STACKIT managed equivalent

Use `oauth2-proxy/oauth2-proxy` (CNCF project) for browser OIDC session management. STACKIT does not offer a managed browser OIDC reverse proxy. The OIDC identity provider (Keycloak) is STACKIT-managed. This exception to the SDD-C-013 managed-service-first preference is consistent with the pattern used for `local-workflows` (Airflow), `langfuse`, and `neo4j`.

**Rejected alternative:** Build a custom OIDC session proxy using Envoy ext-authz or a sidecar pattern. Rejected; oauth2-proxy is the CNCF-standard solution with a stable Helm chart, well-defined Gateway API integration via `gatewayApi.enabled`, and broad community adoption.

### D-2: Gateway API `HTTPRoute` rendered by the oauth2-proxy chart — not the public-endpoints module

The `HTTPRoute` that attaches the protected host to the shared Gateway is rendered by the `oauth2-proxy` chart itself (via `gatewayApi.enabled: true` and `gatewayApi.gatewayRef`). The shared Gateway and GatewayClass are owned by `public-endpoints`. This separation follows the platform's route-attachment model: each module that exposes a service renders its own `HTTPRoute` and attaches to the shared Gateway, rather than asking the Gateway owner to manage route configuration.

**Rejected alternative:** Render the `HTTPRoute` as a standalone blueprint manifest in `infra/gitops/argocd/optional/${ENV}/`. Rejected; the chart already does this correctly and removing it would require a separate rendered manifest to track in sync.

### D-3: IAP_COOKIE_SECRET validated at 16, 24, or 32 bytes — hard failure otherwise

`identity_aware_proxy_validate_cookie_secret()` rejects any cookie secret that is not exactly 16, 24, or 32 bytes. This matches the AES-GCM key sizes supported by oauth2-proxy's session cookie encryption. A shorter or longer secret produces a hard failure at plan time rather than a runtime decryption error.

**Rejected alternative:** Accept any non-empty secret and let oauth2-proxy surface the error at runtime. Rejected; runtime failures are harder to diagnose and the byte-length constraint is known and deterministic.

### D-4: Credentials on the STACKIT lane via ESO `iap-runtime-credentials` — not hardcoded in ArgoCD Application

The ArgoCD Application sources OIDC credentials from an ESO-issued `security/iap-runtime-credentials` Secret rather than from ArgoCD `secretRef` fields or hardcoded chart values. This follows the blueprint ESO credential delivery pattern and avoids storing credentials in GitOps manifests.

**Rejected alternative:** Reference credentials via ArgoCD `secretRef` pointing to a separately managed Kubernetes Secret. Rejected; ESO is the established platform-wide credential delivery mechanism.

### D-5: Documentation scope only — no implementation changes

All implementation artifacts are complete and correct. The compliance PR scope is limited to README hardening and bootstrap template mirror. No script, Helm value, TF module, or ArgoCD manifest is changed.

**Rejected alternative:** Refactor the existing README into a full public-endpoints-style document with inline code examples and NFR prose. Rejected; the existing Stack Execution Model and OIDC Contract sections are accurate and sufficient. Rewriting correct content is scope creep.
