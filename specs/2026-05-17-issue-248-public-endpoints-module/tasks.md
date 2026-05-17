# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — cert-manager feature gate + test contract scaffold (red → green)
Dependencies: none
Owner: bonos
- [x] T-000 Register `tests/infra/modules/public-endpoints/test_contract.py` in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope (AC-011) — MUST be done before T-001 to avoid pre-commit hook failure
- [x] T-001 Write failing assertions in `test_contract.py` for AC-005, AC-011, AC-012, AC-020:
      - AC-005: `cert-manager.values.yaml` and its bootstrap template mirror both contain `ExperimentalGatewayAPISupport` under `featureGates`
      - AC-011: `test_contract.py` is registered in `test_pyramid_contract.json` under `unit` scope
      - AC-012: ≥10 assertions are present in `test_contract.py`
      - AC-020 (scaffold): in `public_endpoints_destroy.sh`, the Certificate delete appears before the Issuer delete, and the Issuer delete appears before gateway baseline removal — verified by static analysis of script content
      Run pytest — confirm AC-005, AC-020 fail (gate not yet enabled, destroy not yet updated)
- [x] T-002 Enable cert-manager Gateway API feature gate in `infra/local/helm/core/cert-manager.values.yaml` and `scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml` (FR-005, AC-005)
- [x] T-003 Run pytest on slice 1 assertions — confirm AC-005 green; AC-020 still fails (expected — destroy updated in slice 2)

### Slice 2 — HTTPS listener + external-dns + Issuer + Certificate + security policies (red → green)
Dependencies: Slice 1 complete
Owner: bonos
- [x] T-004 Write failing assertions in `test_contract.py` for AC-001, AC-002, AC-003, AC-004, AC-013, AC-015, AC-017, AC-018, AC-019:
      - AC-001: rendered gateway manifest contains `kind: GatewayClass`, `kind: Gateway`, HTTP listener port 80, HTTPS listener port 443 with `tls.mode: Terminate`
      - AC-002: rendered Issuer manifest contains `kind: Issuer` and EXACTLY ONE OF: `spec.acme` (STACKIT profile) or `spec.selfSigned` (local profile)
      - AC-003: rendered Certificate manifest contains `kind: Certificate`, `dnsNames`, `issuerRef.name`
      - AC-004: rendered gateway manifest contains annotation `external-dns.alpha.kubernetes.io/hostname`
      - AC-013: rendered gateway manifest HTTPS listener contains minimum TLS version configuration excluding TLS 1.0 and TLS 1.1
      - AC-015: rendered Certificate manifest contains a `renewBefore` field
      - AC-017: rendered gateway listener policy manifest includes `Strict-Transport-Security` with `max-age` ≥ 31536000 and `includeSubDomains`
      - AC-018: rendered NetworkPolicy manifests include default-deny ingress policy and explicit-allow ingress on ports 80 and 443 for Envoy proxy pods
      - AC-019: `public_endpoints_apply.sh` source contains KMS warning logic for `stackit-stage` or `stackit-prod` profiles
      Run pytest — confirm all fail (templates and scripts not yet updated)
- [x] T-005 Update `scripts/templates/infra/bootstrap/infra/gateway/public-endpoints.yaml.tmpl`:
      - Add HTTPS listener (port 443, `tls.mode: Terminate`, `certificateRefs` pointing to `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME`) (FR-001, AC-001)
      - Add minimum TLS version configuration (TLS 1.2 minimum, TLS 1.0/1.1 prohibited) to HTTPS listener (NFR-SEC-002, AC-013)
      - Add `external-dns.alpha.kubernetes.io/hostname` annotation (FR-004, AC-004)
- [x] T-006 Add to `scripts/lib/infra/public_endpoints.sh`:
      - New env var defaults: `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME`
      - Profile-aware `PUBLIC_ENDPOINTS_ACME_SERVER` default in `public_endpoints_init_env`: staging endpoint for `stackit-dev`/`stackit-stage`, production endpoint for `stackit-prod`, not applicable for local (NFR-SEC-004, AC-014)
      - `public_endpoints_render_issuer_manifest()` — renders namespace-scoped `Issuer` (ACME/HTTP01 `gatewayHTTPRoute` for STACKIT, `selfSigned` for local) to `artifacts/infra/rendered/public-endpoints.issuer.yaml` (FR-002, AC-002)
      - `public_endpoints_render_certificate_manifest()` — renders `Certificate` with `dnsNames`, `issuerRef`, `renewBefore` field (FR-003, NFR-OBS-002, AC-003, AC-015)
      - `public_endpoints_render_gateway_tls_policy_manifest()` — renders gateway listener policy manifest with `Strict-Transport-Security: max-age=31536000; includeSubDomains` (NFR-SEC-006, AC-017)
      - `public_endpoints_render_network_policy_manifests()` — renders NetworkPolicy resources: (a) default-deny ingress, (b) explicit allow ports 80/443 for Envoy proxy pods, (c) explicit allow from `cert-manager` namespace for ACME challenge traffic (NFR-SEC-007, AC-018)
      - `public_endpoints_issuer_manifest_file()` and `public_endpoints_certificate_manifest_file()` path helpers
- [x] T-007 Update `scripts/bin/infra/public_endpoints_apply.sh`:
      - Apply Issuer + Certificate + gateway TLS policy + NetworkPolicy manifests in both `helm` and `argocd_application_chart` paths
      - Extend `write_state_file` with `cluster_issuer_name`, `cluster_issuer_type` (`acme` for STACKIT, `selfsigned` for local), and `tls_secret_name` keys (NFR-OPS-001, AC-009)
      - Emit warning log when `BLUEPRINT_PROFILE` is `stackit-stage` or `stackit-prod` and KMS module is not enabled (NFR-SEC-008, AC-019)
- [x] T-008 Update `scripts/bin/infra/public_endpoints_destroy.sh`:
      - Delete Certificate resource before Issuer resource before gateway baseline removal (NFR-REL-001, AC-020)
- [x] T-009 Run pytest — confirm AC-001, AC-002, AC-003, AC-004, AC-013, AC-015, AC-017, AC-018, AC-019, AC-020 green

### Slice 3 — AppProject edge + contract YAML + smoke validations + profile-aware ACME (red → green)
Dependencies: Slice 2 complete
Owner: bonos
- [x] T-010 Write failing assertions in `test_contract.py` for AC-006, AC-007, AC-008, AC-009, AC-010, AC-014, AC-016:
      - AC-006: `public_endpoints_smoke.sh` validates HTTPS listener presence in rendered gateway manifest and exits non-zero if absent
      - AC-007: `public_endpoints_smoke.sh` validates `external-dns.alpha.kubernetes.io/hostname` annotation and exits non-zero if absent
      - AC-008: `public_endpoints_smoke.sh` validates Issuer and Certificate manifest files exist on disk and exits non-zero if the Issuer file is absent or the Certificate file is absent
      - AC-009: runtime state written by `public_endpoints_apply.sh` includes `cluster_issuer_name`, `cluster_issuer_type`, and `tls_secret_name` keys with non-empty values
      - AC-010: all four `appproject-edge.yaml` files include `cert-manager.io/Issuer` and `cert-manager.io/Certificate` in `namespaceResourceWhitelist`
      - AC-014: `public_endpoints_init_env` sets staging ACME server for `stackit-dev`/`stackit-stage` and production ACME server for `stackit-prod`
      - AC-016: `module.contract.yaml` declares all four new optional TLS env vars
      Run pytest — confirm assertions fail
- [x] T-011 Update `infra/gitops/argocd/overlays/*/appproject-edge.yaml` for dev, stage, prod, local:
      - Add `cert-manager.io/Issuer` and `cert-manager.io/Certificate` to `namespaceResourceWhitelist` for the `network` namespace destination (FR-007, AC-010)
- [x] T-012 Update `blueprint/modules/public-endpoints/module.contract.yaml`:
      - Declare `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_ACME_SERVER`, `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` as optional env vars (FR-006, AC-016)
- [x] T-013 Update `scripts/bin/infra/public_endpoints_smoke.sh`:
      - Validate HTTPS listener (port 443) is present in rendered gateway manifest; exit non-zero if absent (AC-006)
      - Validate `external-dns.alpha.kubernetes.io/hostname` annotation is present; exit non-zero if absent (AC-007)
      - Validate Issuer manifest file exists on disk; exit non-zero if absent (AC-008)
      - Validate Certificate manifest file exists on disk; exit non-zero if absent (AC-008)
      - Validate `cluster_issuer_name` key is non-empty in runtime state (NFR-OBS-001)
- [x] T-014 Update `docs/platform/modules/public-endpoints/README.md` with all required TLS sections (GAP-018, NFR-SEC-001, NFR-SEC-003, NFR-SEC-005, NFR-REL-001, NFR-SEC-008):
      - TLS Stack Execution Model (how the HTTPS listener, Issuer, Certificate, and TLS Secret fit together)
      - TLS Secret RBAC constraint (NFR-SEC-003 — Secret accessible only by Envoy Gateway controller SA)
      - Profile-aware ACME server table: staging for stackit-dev/stackit-stage, production for stackit-prod (NFR-SEC-004)
      - HTTP plain-text security trade-off (NFR-SEC-005 — port 80 remains open; consumer HTTPRoute authors must restrict to HTTPS listener)
      - HSTS policy note: HSTS pinning risk on prod, safe to ignore on dev/stage due to staging CA (NFR-SEC-006)
      - Network isolation section: default-deny + allow 80/443 for Envoy pods + cert-manager ACME challenge (NFR-SEC-007)
      - KMS dependency section: KMS must be enabled for stackit-stage and stackit-prod to protect TLS Secret at rest (NFR-SEC-008)
      - Certificate renewBefore field and expiry monitoring deferral note (NFR-OBS-002)
      - Destroy warning: Certificate deleted before Issuer before gateway baseline; TLS session impact (NFR-REL-001)
- [x] T-015 Run `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/public-endpoints/test_contract.py -v` — all ≥20 assertions green (confirms AC-012 threshold met)

## Test Automation
- [x] T-101 `tests/infra/modules/public-endpoints/test_contract.py` written (T-001, T-004, T-010) and passing (T-014) — ≥20 assertions covering AC-001 through AC-020
- [ ] T-102 N/A — no API contract or Pact test
- [ ] T-103 N/A — no filter or payload-transform logic
- [ ] T-104 N/A — no reproducible pre-PR smoke/curl finding; new capability, not bug fix
- [ ] T-105 `tests/infra/test_optional_modules.py::OptionalModulesTests::test_public_endpoints_module_flow` — existing integration test; confirm still passes after gateway template and script changes

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` — N/A; infra/tooling-only change
- [ ] A-002 `apps-smoke` — N/A; infra/tooling-only change
- [ ] A-003 `backend-test-unit` — N/A; infra/tooling-only change
- [ ] A-004 `backend-test-integration` — N/A; infra/tooling-only change
- [ ] A-005 `backend-test-contracts` — N/A; infra/tooling-only change
- [ ] A-006 `backend-test-e2e` — N/A; infra/tooling-only change
- [ ] A-007 `touchpoints-test-unit` — N/A; infra/tooling-only change
- [ ] A-008 `touchpoints-test-integration` — N/A; infra/tooling-only change
- [ ] A-009 `touchpoints-test-contracts` — N/A; infra/tooling-only change
- [ ] A-010 `touchpoints-test-e2e` — N/A; infra/tooling-only change
- [ ] A-011 `test-unit-all` — N/A; infra/tooling-only change
- [ ] A-012 `test-integration-all` — N/A; infra/tooling-only change
- [ ] A-013 `test-contracts-all` — N/A; infra/tooling-only change
- [ ] A-014 `test-e2e-all-local` — N/A; infra/tooling-only change
- [ ] A-015 `infra-port-forward-start` — N/A; infra/tooling-only change
- [ ] A-016 `infra-port-forward-stop` — N/A; infra/tooling-only change
- [ ] A-017 `infra-port-forward-cleanup` — N/A; infra/tooling-only change
