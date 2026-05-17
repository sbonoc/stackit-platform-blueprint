# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-public-endpoints-module.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019
- Control exception rationale: SDD-C-020 and SDD-C-021 N/A — no HTTP API routes or UI rendering in scope.

## Implementation Stack Profile (Normative)
- Backend stack profile: shell_plus_terraform_helm
- Frontend stack profile: none (infra-only — no frontend changes)
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: public-endpoints has stackit_provider_supported=false; the shared Gateway API edge is reconciled from runtime manifests via Helm/ArgoCD; no STACKIT Terraform provider resource exists for load-balancer ingress.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: terraform-plus-argocd
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Consumers can expose their application UI, API, and auth surfaces over HTTPS on a stable base domain with automatic DNS record creation and TLS certificate provisioning — without manual registrar delegation or per-app cert-manager wiring.
- Success metric: `infra-public-endpoints-smoke` passes with HTTPS listener validated, Issuer and Certificate manifests present, and the external-dns annotation confirmed on the rendered gateway manifest.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST add an HTTPS listener on port 443 with `tls.mode: Terminate` and a `certificateRefs` entry pointing to `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` in `PUBLIC_ENDPOINTS_NAMESPACE` to the rendered shared Gateway manifest template (`scripts/templates/infra/bootstrap/infra/gateway/public-endpoints.yaml.tmpl`).
- FR-002 MUST render and apply a namespace-scoped cert-manager `Issuer` in `PUBLIC_ENDPOINTS_NAMESPACE`: using Let's Encrypt ACME HTTP01 solver (type: `gatewayHTTPRoute`, parentRef pointing to the shared Gateway) for STACKIT profiles; using a `selfSigned` Issuer for local profiles.
- FR-003 MUST render and apply a cert-manager `Certificate` resource in `PUBLIC_ENDPOINTS_NAMESPACE` covering `PUBLIC_ENDPOINTS_BASE_DOMAIN`, referencing `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, with the resulting TLS Secret named `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME`.
- FR-004 MUST add the annotation `external-dns.alpha.kubernetes.io/hostname: "${PUBLIC_ENDPOINTS_BASE_DOMAIN}"` to the rendered shared Gateway manifest. The STACKIT SKE DNS extension (enabled in `foundation/main.tf` when `DNS_ENABLED=true`) watches this annotation to reconcile DNS A-records automatically.
- FR-005 MUST enable the cert-manager Gateway API feature gate (`featureGates: ExperimentalGatewayAPISupport=true`) in `infra/local/helm/core/cert-manager.values.yaml` and its bootstrap template mirror (`scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml`) so the `gatewayHTTPRoute` HTTP01 solver is operational.
- FR-006 MUST declare `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_ACME_SERVER`, and `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` as optional env vars in `blueprint/modules/public-endpoints/module.contract.yaml`.
- FR-007 MUST add `cert-manager.io/Issuer` and `cert-manager.io/Certificate` to the `namespaceResourceWhitelist` for the `network` namespace in `infra/gitops/argocd/overlays/*/appproject-edge.yaml` (all four environments: dev, stage, prod, local).
- FR-008 MUST contain ≥10 objectively testable assertions in `tests/infra/modules/public-endpoints/test_contract.py`, registered in `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT write `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL` or any ACME account credential to any state file; cert private keys MUST be managed exclusively by cert-manager and stored only as Kubernetes Secrets.
- NFR-OBS-001 `public_endpoints_smoke.sh` MUST validate: (a) HTTPS listener (port 443) in the rendered gateway manifest, (b) `external-dns.alpha.kubernetes.io/hostname` annotation present in the rendered gateway manifest, (c) Issuer manifest file exists on disk, (d) Certificate manifest file exists on disk, (e) `cluster_issuer_name` key is non-empty in the runtime state.
- NFR-REL-001 Destroy (`infra-public-endpoints-destroy`) MUST attempt to delete the `Certificate` and `Issuer` resources before removing the gateway baseline; certificate destruction invalidates active TLS sessions and is irreversible without re-provisioning — MUST be documented with a destroy warning in the module README.
- NFR-OPS-001 Runtime state written by `public_endpoints_apply.sh` MUST include `cluster_issuer_name`, `cluster_issuer_type` (`acme` for STACKIT, `selfsigned` for local), and `tls_secret_name` keys in addition to the existing 11 keys.
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.
- NFR-SEC-002 MUST configure the HTTPS listener in the rendered Gateway manifest with a minimum TLS version of 1.2; TLS 1.0 and TLS 1.1 MUST NOT be permitted.
- NFR-SEC-003 The `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` Kubernetes Secret in `PUBLIC_ENDPOINTS_NAMESPACE` MUST be documented in the module README as accessible only by the Envoy Gateway controller service account; consumer service accounts MUST NOT be granted read access to Secrets in `PUBLIC_ENDPOINTS_NAMESPACE`.
- NFR-SEC-004 `public_endpoints_init_env` MUST set `PUBLIC_ENDPOINTS_ACME_SERVER` to the Let's Encrypt staging endpoint (`https://acme-staging-v02.api.letsencrypt.org/directory`) when `BLUEPRINT_PROFILE` is `stackit-dev` or `stackit-stage`, and to the production endpoint (`https://acme-v02.api.letsencrypt.org/directory`) when `BLUEPRINT_PROFILE` is `stackit-prod`; for local profiles the ACME server is not applicable (selfSigned Issuer).
- NFR-SEC-005 The HTTP listener on port 80 remains open on the shared Gateway alongside the HTTPS listener; the absence of an HTTP-to-HTTPS redirect is a known security trade-off (explicitly excluded per scope). This trade-off MUST be documented in the module README as a security constraint: consumer HTTPRoute authors MUST explicitly restrict their routes to the HTTPS listener or accept plain-HTTP exposure.
- NFR-OBS-002 The rendered Certificate manifest MUST include a `renewBefore` field (value ≤ 30 days) to make cert-manager renewal intent explicit; runtime certificate expiry monitoring is deferred to the observability module.
- NFR-SEC-006 `public_endpoints_apply.sh` MUST render and apply a gateway listener policy manifest that adds the `Strict-Transport-Security: max-age=31536000; includeSubDomains` response header to all responses served through the HTTPS listener; this prevents protocol downgrade attacks for clients that have previously visited the domain over HTTPS.
- NFR-SEC-007 `public_endpoints_apply.sh` MUST render and apply `NetworkPolicy` resources to `PUBLIC_ENDPOINTS_NAMESPACE` that: (a) default-deny all ingress to namespace pods; (b) explicitly allow ingress on ports 80 and 443 to Envoy proxy pods from any source (public traffic); (c) explicitly allow ingress from the `cert-manager` namespace to Envoy proxy pods for ACME HTTP01 challenge traffic.
- NFR-SEC-008 For `stackit-prod` profiles, the platform KMS module MUST be enabled to provide envelope encryption of Kubernetes Secrets at rest, protecting `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` and the cert-manager ACME account key stored in the `cert-manager` namespace; `public_endpoints_apply.sh` MUST emit a warning when `BLUEPRINT_PROFILE=stackit-prod` and the KMS module is not enabled; this dependency MUST be documented in the module README.

## Normative Option Decision
- Option A: Namespace-scoped `Issuer` per context (shared Gateway Issuer in `network` namespace; consumer apps create their own Issuers in their namespaces).
- Option B: Cluster-scoped `ClusterIssuer` shared across all namespaces.
- Selected option: OPTION_A
- Rationale: Matches the `sbonoc/agentic-graphrag` consumer reference pattern. Namespace scope limits the ACME account blast radius and keeps cert lifecycle isolation per context. `ClusterIssuer` would require cluster-admin permissions and conflicts with the blueprint's namespace-scoped policy model.

## Contract Changes (Normative)
- Config/Env contract: New optional env vars: `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME` (default: `letsencrypt-public-endpoints`), `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL` (no default — must be set for STACKIT profiles), `PUBLIC_ENDPOINTS_ACME_SERVER` (default: profile-aware — `https://acme-staging-v02.api.letsencrypt.org/directory` for `stackit-dev`/`stackit-stage`; `https://acme-v02.api.letsencrypt.org/directory` for `stackit-prod`; not applicable for local profiles), `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` (default: `public-endpoints-gateway-tls`). No existing vars removed or renamed.
- API contract: none (infra-only).
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: existing make targets unchanged; no new targets added.
- Docs contract: `docs/platform/modules/public-endpoints/README.md` updated for TLS + external-dns design; bootstrap template mirror synchronized.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: the rendered gateway manifest contains `kind: GatewayClass`, `kind: Gateway`, an HTTP listener on port 80, and an HTTPS listener on port 443 with `tls.mode: Terminate`.
- AC-002 MUST: the rendered Issuer manifest contains `kind: Issuer` and EXACTLY ONE OF: `spec.acme` (STACKIT profile), `spec.selfSigned` (local profile).
- AC-003 MUST: the rendered Certificate manifest contains `kind: Certificate`, a `dnsNames` entry matching `PUBLIC_ENDPOINTS_BASE_DOMAIN`, and `issuerRef.name` matching `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`.
- AC-004 MUST: the rendered gateway manifest contains the annotation `external-dns.alpha.kubernetes.io/hostname`.
- AC-005 MUST: `infra/local/helm/core/cert-manager.values.yaml` and its bootstrap template mirror both contain `ExperimentalGatewayAPISupport` under `featureGates`.
- AC-006 MUST: `public_endpoints_smoke.sh` validates that the rendered gateway manifest contains an HTTPS listener (port 443) and exits non-zero if absent.
- AC-007 MUST: `public_endpoints_smoke.sh` validates that `external-dns.alpha.kubernetes.io/hostname` annotation is present in the rendered gateway manifest and exits non-zero if absent.
- AC-008 MUST: `public_endpoints_smoke.sh` validates that both the Issuer and Certificate manifest files exist on disk and exits non-zero if the Issuer file is absent or the Certificate file is absent.
- AC-009 MUST: runtime state written by `public_endpoints_apply.sh` includes `cluster_issuer_name` and `tls_secret_name` keys with non-empty values.
- AC-010 MUST: `infra/gitops/argocd/overlays/*/appproject-edge.yaml` for all four environments includes `cert-manager.io/Issuer` and `cert-manager.io/Certificate` in `namespaceResourceWhitelist`.
- AC-011 MUST: `tests/infra/modules/public-endpoints/test_contract.py` is registered in `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope.
- AC-012 MUST: `tests/infra/modules/public-endpoints/test_contract.py` contains ≥10 assertions passing against the real file tree.
- AC-013 MUST: the rendered gateway manifest HTTPS listener contains a minimum TLS version configuration that excludes TLS 1.0 and TLS 1.1.
- AC-014 MUST: `public_endpoints_init_env` sets `PUBLIC_ENDPOINTS_ACME_SERVER` to the Let's Encrypt staging endpoint when `BLUEPRINT_PROFILE` is `stackit-dev` or `stackit-stage`, and to the production endpoint when `BLUEPRINT_PROFILE` is `stackit-prod`.
- AC-015 MUST: the rendered Certificate manifest contains a `renewBefore` field.
- AC-016 MUST: `blueprint/modules/public-endpoints/module.contract.yaml` declares `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_ACME_SERVER`, and `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` as optional env vars.
- AC-017 MUST: the rendered gateway listener policy manifest includes `Strict-Transport-Security` response header configuration for the HTTPS listener with `max-age` ≥ 31536000 and `includeSubDomains`.
- AC-018 MUST: the rendered `NetworkPolicy` manifests for `PUBLIC_ENDPOINTS_NAMESPACE` include a default-deny ingress policy and an explicit-allow ingress policy for Envoy proxy pods on ports 80 and 443.
- AC-019 MUST: `public_endpoints_apply.sh` emits a warning log when `BLUEPRINT_PROFILE=stackit-prod` and the KMS module is not enabled.

## Informative Notes (Non-Normative)
- Context: cert-manager is already installed as a core runtime component (`core_runtime_bootstrap.sh`, v1.20.1). The Gateway API feature gate (`ExperimentalGatewayAPISupport`) is the only missing configuration — without it, cert-manager silently ignores `gatewayHTTPRoute` solver configuration and no HTTP01 challenge is issued.
- Context: The STACKIT SKE DNS extension is already wired in `foundation/main.tf` (lines 8–17). When `DNS_ENABLED=true` and DNS zone FQDNs are provided, the SKE cluster's built-in external-dns controller manages A-records. The public-endpoints module only needs to annotate the Gateway manifest — no standalone external-dns Helm chart required.
- Context: `sbonoc/agentic-graphrag` uses namespace-scoped `Issuer` with `gatewayHTTPRoute` HTTP01 and production Let's Encrypt across all environments. This pattern is adopted here.
- Context: The Issuer and Gateway cert for the shared Gateway live in the `network` namespace alongside the Gateway. Consumer apps create their own Issuers + Certificates in their own namespaces, referencing the same ACME server.
- Tradeoffs: HTTP01 with `gatewayHTTPRoute` requires the Envoy Gateway controller CRDs to be established before cert-manager can place the challenge HTTPRoute. The existing `public_endpoints_wait_for_gateway_api_crds` call in `deploy` already handles this ordering.

## Explicit Exclusions
- Wildcard certificate provisioning via DNS01 ACME challenge — requires a cert-manager DNS01 webhook for STACKIT DNS; not available as of STACKIT provider v0.88.0. Parked in backlog on-scope: infra.
- Per-consumer `Certificate` management — consumer apps create their own Issuer + Certificate resources via ArgoCD; out of scope for the platform module.
- Standalone external-dns Helm chart deployment — the STACKIT SKE DNS extension already handles record management when `DNS_ENABLED=true`.
- HTTP-to-HTTPS redirect — consumer HTTPRoute concern; not part of the shared gateway contract. The security trade-off of leaving port 80 open is documented as NFR-SEC-005.
- BackendTLSPolicy (Gateway→Pod encryption) — requires per-service TLS provisioning by each consumer; not addressable at the platform module level. Parked in backlog `on-scope: infra`.
- ReferenceGrant per-namespace enforcement — replacing `allowedRoutes.namespaces.from: All` with explicit ReferenceGrant is an architectural change to the consumer onboarding model; parked in backlog `on-scope: blueprint`.
- OCSP stapling — no documented Envoy Gateway support path as of cert-manager v1.20.1; parked in backlog `on-scope: infra`.
- Service mesh / mTLS east-west / SPIFFE — requires a separate platform-level architectural decision (Istio, Linkerd, Cilium); parked in backlog `on-scope: platform`.
- cert-manager KMS signer plugin — unstable ecosystem, no production-ready STACKIT KMS integration; parked in backlog `on-scope: infra`.
