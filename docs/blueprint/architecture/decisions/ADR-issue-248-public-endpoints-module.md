# ADR — issue-248: public-endpoints module TLS + external-dns

- **Status:** approved
- **ADR technical decision sign-off:** approved
- **Date:** 2026-05-17
- **Work item:** 2026-05-17-issue-248-public-endpoints-module
- **Deciders:** bonos

## Context

The public-endpoints module provides the shared Kubernetes Gateway API edge (Envoy Gateway controller + shared `GatewayClass`/`Gateway`) that exposes consumer application UI, API, and auth surfaces. The module previously exposed only an HTTP listener on port 80. Two capabilities are added in this work item:

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

---

### D-6: Minimum TLS version 1.2 enforced via gateway TLS policy manifest

**Decision:** A gateway listener TLS policy manifest is rendered and applied alongside the Gateway, enforcing TLS 1.2 as the minimum version and prohibiting TLS 1.0 and TLS 1.1.

**Rationale:** TLS 1.0 and 1.1 have known protocol weaknesses (BEAST, POODLE, CRIME). Enforcing TLS 1.2+ at the platform edge is a baseline security requirement. cert-manager v1.20.1 and Envoy Gateway fully support TLS 1.2+ listener configuration. Placing the policy at the platform module level ensures all consumer surfaces benefit without requiring per-consumer configuration.

---

### D-7: HSTS `Strict-Transport-Security` header via gateway TLS policy manifest

**Decision:** The gateway TLS policy manifest adds `Strict-Transport-Security: max-age=31536000; includeSubDomains` to all HTTPS listener responses.

**Alternatives considered:**
- **D-7-A (rejected): HSTS at consumer HTTPRoute level** — Requires each consumer to add a `responseHeaderModifier` filter. Platform HSTS coverage would be incomplete and inconsistent across consumers.

**Rationale:** Platform-level HSTS ensures all consumer services benefit without consumer opt-in. `includeSubDomains` ensures subdomain coverage is also enforced.

---

### D-8: NetworkPolicy for `network` namespace (default-deny + explicit allow)

**Decision:** `NetworkPolicy` resources are rendered and applied to `PUBLIC_ENDPOINTS_NAMESPACE`: (a) default-deny all ingress to namespace pods; (b) explicit allow ingress on ports 80 and 443 to Envoy proxy pods from any source (public traffic); (c) explicit allow ingress from the `cert-manager` namespace to Envoy proxy pods for ACME HTTP01 challenge traffic.

**Alternatives considered:**
- **D-8-A (rejected): No NetworkPolicy** — Leaves the `network` namespace open to direct pod-to-pod traffic from any cluster workload, enabling lateral movement to internal Envoy endpoints.

**Rationale:** Default-deny enforces least-privilege at the network layer. The explicit cert-manager allow is necessary for the ACME HTTP01 solver to place challenge HTTPRoutes via the Envoy Gateway.

---

### D-9: Profile-aware ACME server (staging for dev/stage, production for prod)

**Decision:** `public_endpoints_init_env` sets `PUBLIC_ENDPOINTS_ACME_SERVER` to the Let's Encrypt staging endpoint (`https://acme-staging-v02.api.letsencrypt.org/directory`) for `stackit-dev` and `stackit-stage` profiles, and the production endpoint (`https://acme-v02.api.letsencrypt.org/directory`) for `stackit-prod`. Local profiles use a `selfSigned` Issuer and the ACME server is not applicable.

**Rationale:** Let's Encrypt enforces a production rate limit of 5 certificates per registered domain per week. Using staging for non-production profiles prevents rate limit exhaustion during development and CI. Staging certificates are issued by a staging CA not trusted by browsers — this is expected and documented behavior for dev/stage environments.

---

### D-10: KMS module as required dependency for `stackit-stage` and `stackit-prod` (encryption-at-rest)

**Decision:** For `stackit-stage` and `stackit-prod` profiles, the STACKIT KMS module MUST be enabled to provide Kubernetes Secret encryption at rest via envelope encryption. `public_endpoints_apply.sh` emits a warning when the KMS module is not enabled and the profile is `stackit-stage` or `stackit-prod`. This protects `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` (TLS private key) and the cert-manager ACME account key stored in the `cert-manager` namespace.

**Alternatives considered:**
- **D-10-A (rejected): KMS required for `stackit-prod` only** — Limiting KMS to prod means the encryption-at-rest setup is first validated under live production traffic. Any misconfiguration in the KMS provider integration would surface only in prod, with no prior rehearsal.
- **D-10-B (rejected): cert-manager KMS signer plugin** — Store private keys directly in STACKIT KMS rather than Kubernetes Secrets. No production-ready STACKIT cert-manager KMS plugin exists as of v1.20.1; parked in backlog `on-scope: infra`.

**Rationale:** The TLS private key and ACME account key are high-value secrets. Without KMS-backed Kubernetes encryption provider, both are stored in plaintext in etcd. Requiring KMS in `stackit-stage` validates the encryption-at-rest integration in the last pre-production environment before promotion to prod — consistent with the blueprint principle that stage mirrors production security controls. `stackit-dev` is excluded because it uses staging ACME certs (untrusted CA, low risk) and is optimised for developer velocity over security parity.

---

## Consequences

- cert-manager restarts once when the featureGate is applied on next `infra-deploy`. Issued certs in other namespaces are unaffected.
- DNS record creation depends on `DNS_ENABLED=true` and the SKE DNS extension being active. If `DNS_ENABLED=false`, the external-dns annotation is present but ignored — no records are created, no error.
- TLS certificate issuance requires HTTP01 challenge traffic to reach the Envoy Gateway. Firewall rules must allow inbound HTTP on port 80 to the STACKIT LB (Let's Encrypt ACME challenge solver will create a temporary HTTPRoute for `/.well-known/acme-challenge/` — this is handled automatically by cert-manager and the `gatewayHTTPRoute` solver).
- HSTS pinning is effectively irreversible for the `max-age` duration (1 year). If the HTTPS listener is removed after HSTS headers have been served, browsers that received the header will refuse HTTP connections for up to 1 year. Operators must not remove the HTTPS listener without a planned HSTS expiry migration.
- NetworkPolicy restricts pod-to-pod traffic in the `network` namespace. Direct `kubectl port-forward` or debug pod connections to Envoy proxy pods from other namespaces will be blocked. Operators debugging Gateway issues must use a pod within the `network` namespace or temporarily relax the policy.
- Staging ACME certificates (`stackit-dev`, `stackit-stage`) are issued by the Let's Encrypt staging CA and are not trusted by browsers or standard TLS clients — this is expected and intentional for non-production environments.
- `stackit-stage` and `stackit-prod` deployments emit a warning and may proceed (non-fatal) if the KMS module is not enabled, but the TLS Secret and ACME account key will not be encrypted at rest. Operators must treat this warning as a hard blocker for both profiles; the stage requirement exists specifically to validate the KMS integration before production promotion.
- Wildcard certificates (DNS01 ACME challenge) are out of scope — no STACKIT cert-manager DNS01 webhook exists as of provider v0.88.0. Parked in backlog `on-scope: infra`.
