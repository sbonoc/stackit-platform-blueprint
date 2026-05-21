# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (architecture)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Live README hardening
- [ ] T-101 Add **Environment Variables** table to `docs/platform/modules/identity-aware-proxy/README.md` (5 required + 7 optional vars with defaults and descriptions)
- [ ] T-102 Add **Make Targets** table documenting all 5 lifecycle targets with one-line descriptions and state file key summary
- [ ] T-103 Add **Provisioning Lifecycle** section with Keycloak client prerequisite, env var exports, and plan→apply→deploy→smoke command sequence
- [ ] T-104 Add **Security** section documenting `IAP_COOKIE_SECRET` byte-length constraint, credential non-persistence in state files, and K8s Secret lifecycle per lane
- [ ] T-105 Add **Teardown** section with `make infra-identity-aware-proxy-destroy` and enumeration of removed resources

## Implementation — Slice 2: Bootstrap template mirror
- [ ] T-201 Mirror all Slice 1 additions to `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md`

## Accessibility Testing (Non-UI spec)
- [ ] T-A01 Confirm NFR-A11Y-001 is declared as "N/A — no UI surfaces" in `spec.md` ✓

## Validation and Release Readiness
- [ ] T-301 Run `make quality-hooks-fast` — exits 0 (docs lint + shellcheck + bootstrap drift check + SDD check)
- [ ] T-302 Run `make quality-docs-check-changed` — exits 0 (bootstrap template in sync with live README)
- [ ] T-303 Verify `make infra-identity-aware-proxy-plan` with `IDENTITY_AWARE_PROXY_ENABLED=false` exits 0 (skip path)
- [ ] T-304 Verify `make infra-identity-aware-proxy-smoke` with `IDENTITY_AWARE_PROXY_ENABLED=false` exits 0 (skip path)
- [ ] T-305 Run `make quality-hardening-review`
- [ ] T-306 Attach evidence to `traceability.md`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified — pre-existing, no-impact
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — pre-existing, no-impact
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — pre-existing, no-impact
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — pre-existing, no-impact
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — pre-existing, no-impact
