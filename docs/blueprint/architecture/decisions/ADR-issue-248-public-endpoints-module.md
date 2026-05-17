# ADR — issue-248: public-endpoints module TLS + external-dns

- **Status:** proposed
- **Date:** 2026-05-17
- **Work item:** 2026-05-17-issue-248-public-endpoints-module
- **Deciders:** bonos

## Context

The public-endpoints module provides the shared Kubernetes Gateway API edge (Envoy Gateway controller + shared `GatewayClass`/`Gateway`) that exposes marketplace UI, API, and auth surfaces. The module previously exposed only an HTTP listener on port 80. Two capabilities are added in this work item:

1. **HTTPS with cert-manager** — TLS termination at the shared Gateway using automatically provisioned certificates.
2. **Automatic DNS record management** — The STACKIT SKE DNS extension creates A-records for the base domain from a standard annotation on the Gateway resource.

Both capabilities were validated against the `sbonoc/agentic-graphrag` consumer reference implementation, which uses the same Envoy Gateway + cert-manager + Let's Encrypt ACME + STACKIT DNS extension stack.

## Decisions

### D-1: HTTPS listener added to the shared Gateway (port 443, `tls.mode: Terminate`)

**Decision:** Add a port-443 HTTPS listener to `scripts/templates/infra/bootstrap/infra/gateway/public-endpoints.yaml.tmpl` alongside the existing port-80 HTTP listener. TLS terminates at the Gateway using a cert-manager-provisioned Secret.

**Alternatives considered:**
- **D-1-A (rejected): TLS passthrough** — Route TLS to backends; backends terminate. Incompatible with the IAP SecurityPolicy pattern that requires the Gateway to inspect decrypted traffic.
- **D-1-B (rejected): TLS at HTTPRoute level only** — No shared Gateway HTTPS listener; consumers attach per-route certs. Breaks the shared edge contract and forces every consumer to manage their own listener.

**Rationale:** Terminate at the shared Gateway so the IAP module can apply SecurityPolicy to decrypted requests. Consistent with the agentic-graphrag pattern and the Gateway API design recommendation for shared infrastructure.

---

### D-2: Namespace-scoped `Issuer` (not `ClusterIssuer`) in the `network` namespace

**Decision:** The Issuer used by the platform Gateway cert lives in the `network` namespace (same namespace as the Gateway). For STACKIT profiles: Let's Encrypt ACME HTTP01 solver via `gatewayHTTPRoute`. For local profiles: `selfSigned` issuer.

**Alternatives considered:**
- **D-2-A (rejected): `ClusterIssuer`** — Cluster-wide ACME account shared across all namespaces. Requires cluster-admin permissions for consumers; breaks namespace-scoped policy model; blast radius extends to all namespaces if the ACME account is misconfigured.

**Rationale:** Namespace scope matches the agentic-graphrag pattern (all consumer Issuers are namespace-scoped) and the blueprint's least-privilege policy model. The `network` namespace is the natural home — it already contains the shared Gateway.

---

### D-3: `external-dns.alpha.kubernetes.io/hostname` annotation on the shared Gateway (no standalone external-dns pod)

**Decision:** Add the standard external-dns annotation to the rendered Gateway manifest. The STACKIT SKE DNS extension (already provisioned in `foundation/main.tf` when `DNS_ENABLED=true`, lines 8–17) watches this annotation and reconciles A-records in the configured STACKIT DNS zones. No standalone external-dns Helm chart is deployed.

**Alternatives considered:**
- **D-3-A (rejected): Standalone Bitnami external-dns Helm chart** — Separate controller deployment configured for the STACKIT provider. Adds a new component to the module with its own lifecycle, version pin, and credential management. Unnecessary because the SKE DNS extension already provides this capability.
- **D-3-B (rejected): Manual DNS record management** — No annotation; operators update registrar manually after apply. Defeats the purpose of automating the public-endpoints workflow.

**Rationale:** The SKE DNS extension is a first-class STACKIT feature already wired in the foundation TF. Using it instead of a standalone pod keeps the module minimal and avoids credential duplication.

---

### D-4: cert-manager Gateway API feature gate (`ExperimentalGatewayAPISupport=true`)

**Decision:** Add `featureGates: ExperimentalGatewayAPISupport=true` to `infra/local/helm/core/cert-manager.values.yaml` and its bootstrap template mirror. This enables the `gatewayHTTPRoute` HTTP01 solver type, required for cert-manager to place challenge HTTPRoutes via the Envoy Gateway.

**Rationale:** Without this flag, cert-manager silently ignores `gatewayHTTPRoute` solver configuration and no HTTP01 challenge is initiated. cert-manager v1.20.1 (already pinned) fully supports this feature gate. The change is additive — cert-manager restarts gracefully with the new flag; existing issued certs are unaffected.

---

### D-5: AppProject edge whitelist expanded for cert-manager resources in `network` namespace

**Decision:** Add `cert-manager.io/Issuer` and `cert-manager.io/Certificate` to the `namespaceResourceWhitelist` for the `network` namespace destination in `appproject-edge.yaml` (all four environments).

**Rationale:** The `platform-edge-*` ArgoCD projects own the shared Gateway, Issuer, and Certificate in the `network` namespace. Without this whitelist entry, ArgoCD cannot apply or sync the Issuer and Certificate resources, and the app would show an OutOfSync status.

## Consequences

- cert-manager restarts once when the featureGate is applied on next `infra-deploy`. Issued certs in other namespaces are unaffected.
- DNS record creation depends on `DNS_ENABLED=true` and the SKE DNS extension being active. If `DNS_ENABLED=false`, the external-dns annotation is present but ignored — no records are created, no error.
- TLS certificate issuance requires HTTP01 challenge traffic to reach the Envoy Gateway. Firewall rules must allow inbound HTTP on port 80 to the STACKIT LB (Let's Encrypt ACME challenge solver will create a temporary HTTPRoute for `/.well-known/acme-challenge/` — this is handled automatically by cert-manager and the `gatewayHTTPRoute` solver).
- Wildcard certificates (DNS01 ACME challenge) are out of scope — no STACKIT cert-manager DNS01 webhook exists as of provider v0.88.0. Parked in backlog `on-scope: infra`.
