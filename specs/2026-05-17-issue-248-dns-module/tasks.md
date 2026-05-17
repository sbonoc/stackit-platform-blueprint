# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions count = 0 (Q-1 nameservers, Q-2 DNSSEC must be resolved)
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Terraform standalone module (red → green)
- [x] T-000 Add `tests/infra/modules/dns/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope (AC-008) — MUST be done before T-001 to avoid pre-commit hook failure
- [x] T-001 Write failing `test_contract.py` assertions for TF module structure (AC-001 through AC-004, AC-007):
      - AC-001: `main.tf` declares `stackit_dns_zone.this` with `project_id`, `name`, `dns_name = trimsuffix(...)`; includes `required_version = ">= 1.13.0"`; does NOT include `create_before_destroy`
      - AC-002: `variables.tf` declares five required variables
      - AC-003: `outputs.tf` declares `zone_id`, `dns_name`, and `primary_name_server`
      - AC-004: `versions.tf` declares `stackitcloud/stackit = 0.88.0`
      Run pytest — confirm assertions fail (TF files are stubs)
- [x] T-002 Write `infra/cloud/stackit/terraform/modules/dns/main.tf` with `stackit_dns_zone.this`
- [x] T-003 Write `infra/cloud/stackit/terraform/modules/dns/variables.tf` with five variables
- [x] T-004 Write `infra/cloud/stackit/terraform/modules/dns/outputs.tf` with `zone_id`, `dns_name`, and `primary_name_server`
- [x] T-005 Write `infra/cloud/stackit/terraform/modules/dns/versions.tf` with `stackitcloud/stackit = 0.88.0`
- [x] T-006 Run pytest on slice 1 assertions — confirm AC-001 through AC-004 green

### Slice 2 — Smoke strengthening and test coverage (red → green)
- [x] T-007 Write failing `test_contract.py` assertions for AC-005, AC-006, AC-009, AC-010, AC-011, AC-012:
      - AC-005: `dns_smoke.sh` contains non-empty check for `zone_id`
      - AC-006: `dns_smoke.sh` contains non-empty check for `zone_fqdn`
      - AC-009: `test_contract.py` passes with ≥ 10 assertions
      - AC-010: Mock runtime state fixture contains `zone_id`, `zone_name`, `zone_fqdn`, `primary_name_server` keys
      - AC-011: `module.contract.yaml` includes `DNS_PRIMARY_NAME_SERVER`; `dns_apply.sh` writes `primary_name_server` to state; `dns.sh` declares `dns_primary_name_server()`
      - AC-012: `dns_smoke.sh` contains non-empty check for `primary_name_server`; smoke state write includes `primary_name_server`
      Run pytest — confirm AC-005, AC-006, AC-011, AC-012 fail
- [x] T-007b Implement FR-004b (green):
      - Add `DNS_PRIMARY_NAME_SERVER` to `blueprint/modules/dns/module.contract.yaml` under `outputs.produced`
      - Add `dns_primary_name_server()` helper to `scripts/lib/infra/dns.sh` (reads foundation output or falls back to local placeholder)
      - Update `scripts/bin/infra/dns_apply.sh` to write `primary_name_server=$(dns_primary_name_server)` to the runtime state file
- [x] T-008 Update `scripts/bin/infra/dns_smoke.sh` — add `zone_id`, `zone_fqdn`, and `primary_name_server` non-empty checks; extend smoke state write to include `zone_fqdn` and `primary_name_server` (matching KMS pattern)
- [x] T-009 Run `uv run pytest tests/infra/modules/dns/test_contract.py -v` — all ≥ 10 assertions green (AC-009) — **18/18 passed**

## Test Automation
- [x] T-101 `tests/infra/modules/dns/test_contract.py` written (T-001, T-007) and passing (T-009) — 18 assertions (≥ 10)
- [x] T-102 N/A — no API contract or Pact test
- [x] T-103 N/A — no filter or payload-transform logic
- [x] T-104 N/A — no reproducible pre-PR smoke/curl finding; new capability, not bug fix
- [ ] T-105 `tests/infra/test_optional_modules.py` — verify existing dns flow test passes with strengthened smoke

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [ ] T-201 Run `uv run pytest tests/infra/modules/dns/test_contract.py -v` and `make quality-hooks-fast` — all pass
- [ ] T-202 Attach evidence to traceability document — traceability.md updated post-implementation
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`) — document-sync step
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`; use "Part of #248" (NOT "Closes #248")

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change
