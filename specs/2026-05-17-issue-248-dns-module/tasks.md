# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions count = 0 (Q-1 nameservers, Q-2 DNSSEC resolved before implementation; scope expanded to multi-zone post-implementation)
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Terraform standalone module (red → green)
- [x] T-000 Add `tests/infra/modules/dns/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope (AC-008) — MUST be done before T-001 to avoid pre-commit hook failure
- [x] T-001 Write failing `test_contract.py` assertions for TF module structure (AC-001 through AC-004):
      - AC-001: `main.tf` declares `stackit_dns_zone.this` with `for_each`, `sha1` naming, `trimsuffix`, `required_version >= 1.13.0`, no `create_before_destroy`
      - AC-002: `variables.tf` declares five required variables (`stackit_project_id`, `stackit_region`, `dns_zone_fqdns`, `dns_naming_prefix`, `dns_record_ttl`)
      - AC-003: `outputs.tf` declares `zone_ids` (map), `dns_names` (list), `primary_name_servers` (map)
      - AC-004: `versions.tf` declares `stackitcloud/stackit = 0.88.0`
      Run pytest — confirm assertions fail (TF files are stubs)
- [x] T-002 Write `infra/cloud/stackit/terraform/modules/dns/main.tf` with `stackit_dns_zone.this` (multi-zone `for_each`)
- [x] T-003 Write `infra/cloud/stackit/terraform/modules/dns/variables.tf` with five variables (`dns_zone_fqdns` as list, `dns_naming_prefix`)
- [x] T-004 Write `infra/cloud/stackit/terraform/modules/dns/outputs.tf` with `zone_ids` (map), `dns_names` (list), `primary_name_servers` (map)
- [x] T-005 Write `infra/cloud/stackit/terraform/modules/dns/versions.tf` with `stackitcloud/stackit = 0.88.0`
- [x] T-006 Run pytest on slice 1 assertions — confirm AC-001 through AC-004 green

### Slice 2 — Shell layer, contract, smoke, and quality gate (red → green)
- [x] T-007 Write failing `test_contract.py` assertions for AC-005, AC-006, AC-009, AC-010, AC-011, AC-012:
      - AC-005: `dns_smoke.sh` validates `zone_count` is a positive integer
      - AC-006: `dns_smoke.sh` validates `zone_ids` is non-empty
      - AC-010: Mock runtime state fixture contains `zone_ids`, `zone_fqdns`, `zone_count`, `primary_name_servers` keys
      - AC-011: `module.contract.yaml` includes `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, `DNS_PRIMARY_NAME_SERVERS`; `dns.sh` declares `dns_zone_ids()`, `dns_zone_count()`, `dns_primary_name_servers()`; `dns_apply.sh` writes all three to state
      - AC-012: `dns_smoke.sh` validates `primary_name_servers` is non-empty; smoke state write includes `primary_name_servers`
      Run pytest — confirm AC-005, AC-006, AC-011, AC-012 fail
- [x] T-007b Implement FR-004b (green):
      - Add `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, `DNS_PRIMARY_NAME_SERVERS` to `blueprint/modules/dns/module.contract.yaml` under `outputs.produced`
      - Add `dns_zone_ids()`, `dns_zone_count()`, `dns_primary_name_servers()` helpers to `scripts/lib/infra/dns.sh`
      - Update `scripts/bin/infra/dns_apply.sh` to write `zone_ids`, `zone_count`, `primary_name_servers` to runtime state
- [x] T-008 Update `scripts/bin/infra/dns_smoke.sh` — add `zone_count`, `zone_ids`, and `primary_name_servers` non-empty checks; extend smoke state write to include all four contract keys
- [x] T-009 Run `uv run pytest tests/infra/modules/dns/test_contract.py -v` — all 26 assertions green (AC-009) — **26/26 passed**

## Test Automation
- [x] T-101 `tests/infra/modules/dns/test_contract.py` written (T-001, T-007) and passing (T-009) — 26 assertions (≥ 10)
- [x] T-102 N/A — no API contract or Pact test
- [x] T-103 N/A — no filter or payload-transform logic
- [x] T-104 N/A — no reproducible pre-PR smoke/curl finding; new capability, not bug fix
- [x] T-105 `tests/infra/test_optional_modules.py::OptionalModulesTests::test_dns_module_flow` — PASS (two-zone fixture: `marketplace-web-dev.runs.onstackit.local.` + `marketplace-auth-dev.runs.onstackit.local.`); verifies `zone_count=2` and multi-zone state keys

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [x] T-A02 N/A — no UI changes
- [x] T-A03 N/A — no UI changes
- [x] T-A04 N/A — no UI changes
- [x] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [x] T-201 Run `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/dns/test_contract.py -v` — 26/26 PASSED; `make quality-hooks-fast` — PASS
- [x] T-202 Traceability document updated post-implementation (multi-zone matrix, evidence manifest SHA256s refreshed); traceability keeper run twice (post single-zone + post multi-zone)
- [x] T-203 No stale TODOs/dead code/drift — all single-zone variable names (`dns_zone_fqdn`, `dns_zone_name`, `dns_zone_id`) replaced with multi-zone equivalents across TF, shell, contract, and test files
- [x] T-204 Documentation validation — `docs/platform/modules/dns/README.md` and template mirror updated with multi-zone content; `make quality-docs-check-changed` PASS
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`) — PASS

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section — complete
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes — complete
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`; use "Part of #248" (NOT "Closes #248") — complete

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change
