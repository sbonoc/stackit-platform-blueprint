# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — cert-manager feature gate + test contract scaffold
- [ ] T-000 Register `tests/infra/modules/public-endpoints/test_contract.py` in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope (AC-011) — MUST be done before T-001 to avoid pre-commit hook failure
- [ ] T-001 Write failing assertions in `test_contract.py` for AC-005, AC-011, AC-012:
      - AC-005: `cert-manager.values.yaml` and its template mirror contain `ExperimentalGatewayAPISupport` under `featureGates`
      - AC-011: `test_contract.py` registered in `test_pyramid_contract.json`
      - AC-012: ≥10 assertions present
      Run pytest — confirm AC-005, AC-011 fail (gate not yet enabled)
- [ ] T-002 Enable cert-manager Gateway API feature gate in `infra/local/helm/core/cert-manager.values.yaml` and `scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml` (FR-005, AC-005)
- [ ] T-003 Run pytest on slice 1 assertions — confirm AC-005 green

### Slice 2 — HTTPS listener + external-dns annotation + Issuer + Certificate
- [ ] T-004 Write failing assertions in `test_contract.py` for AC-001, AC-002, AC-003, AC-004:
      - AC-001: rendered gateway manifest contains HTTPS listener (port 443) with `tls.mode: Terminate`
      - AC-002: rendered Issuer manifest contains `kind: Issuer` and `spec.acme` or `spec.selfSigned`
      - AC-003: rendered Certificate manifest contains `kind: Certificate`, `dnsNames`, `issuerRef.name`
      - AC-004: rendered gateway manifest contains `external-dns.alpha.kubernetes.io/hostname` annotation
      Run pytest — confirm assertions fail (template not yet updated)
- [ ] T-005 Update `scripts/templates/infra/bootstrap/infra/gateway/public-endpoints.yaml.tmpl`: add HTTPS listener (port 443, `tls.mode: Terminate`, `certificateRefs`) and `external-dns.alpha.kubernetes.io/hostname` annotation (FR-001, FR-004, AC-001, AC-004)
- [ ] T-006 Add to `scripts/lib/infra/public_endpoints.sh`:
      - New env var defaults: `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_ACME_SERVER`, `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME`
      - `public_endpoints_render_issuer_manifest()` — renders namespace-scoped `Issuer` (ACME/HTTP01 for STACKIT, selfSigned for local) to `artifacts/infra/rendered/public-endpoints.issuer.yaml` (FR-002, AC-002)
      - `public_endpoints_render_certificate_manifest()` — renders `Certificate` to `artifacts/infra/rendered/public-endpoints.certificate.yaml` (FR-003, AC-003)
      - `public_endpoints_issuer_manifest_file()` and `public_endpoints_certificate_manifest_file()` path helpers
- [ ] T-007 Update `scripts/bin/infra/public_endpoints_apply.sh`: apply Issuer + Certificate manifests in both `helm` and `argocd_application_chart` paths; extend `write_state_file` with `cluster_issuer_name`, `cluster_issuer_type`, `tls_secret_name` keys (NFR-OPS-001, AC-009)
- [ ] T-008 Update `scripts/bin/infra/public_endpoints_destroy.sh`: delete Certificate + Issuer resources before gateway baseline removal (NFR-REL-001)
- [ ] T-009 Run pytest — confirm AC-001, AC-002, AC-003, AC-004 green

### Slice 3 — AppProject edge + contract YAML + smoke validations
- [ ] T-010 Write failing assertions in `test_contract.py` for AC-006, AC-007, AC-008, AC-010:
      - AC-006: smoke script validates HTTPS listener presence
      - AC-007: smoke script validates external-dns annotation presence
      - AC-008: smoke script validates Issuer + Certificate manifest files exist
      - AC-010: all four appproject-edge.yaml files include cert-manager Issuer + Certificate in namespaceResourceWhitelist
      Run pytest — confirm assertions fail
- [ ] T-011 Update `infra/gitops/argocd/overlays/*/appproject-edge.yaml` for dev, stage, prod, local: add `cert-manager.io/Issuer` and `cert-manager.io/Certificate` to `namespaceResourceWhitelist` for the `network` namespace destination (FR-007, AC-010)
- [ ] T-012 Update `blueprint/modules/public-endpoints/module.contract.yaml`: add `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME`, `PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL`, `PUBLIC_ENDPOINTS_ACME_SERVER`, `PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME` as optional env vars (FR-006, AC-011 parity)
- [ ] T-013 Update `public_endpoints_smoke.sh`: add validation for (a) HTTPS listener in gateway manifest, (b) external-dns annotation, (c) Issuer manifest on disk, (d) Certificate manifest on disk (NFR-OBS-001, AC-006, AC-007, AC-008)
- [ ] T-014 Run `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/public-endpoints/test_contract.py -v` — all ≥10 assertions green (AC-012)

## Test Automation
- [ ] T-101 `tests/infra/modules/public-endpoints/test_contract.py` written (T-001, T-004, T-010) and passing (T-014) — ≥10 assertions
- [ ] T-102 N/A — no API contract or Pact test
- [ ] T-103 N/A — no filter or payload-transform logic
- [ ] T-104 N/A — no reproducible pre-PR smoke/curl finding; new capability, not bug fix
- [ ] T-105 `tests/infra/test_optional_modules.py::OptionalModulesTests::test_public_endpoints_module_flow` — existing integration test; confirm still passes after gateway template and script changes

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [ ] T-A02 N/A — no UI changes
- [ ] T-A03 N/A — no UI changes
- [ ] T-A04 N/A — no UI changes
- [ ] T-A05 N/A — no UI changes

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
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
