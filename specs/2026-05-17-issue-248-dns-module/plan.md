# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- Q-1 (nameservers attribute) and Q-2 (DNSSEC) MUST be resolved before SPEC_READY=true.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Minimal scope — 4 TF files, smoke strengthening, test file. No new shell functions or Make targets.
- Anti-abstraction gate: Direct `stackit_dns_zone` resource; no wrapper. Mirror the foundation pattern exactly.
- Integration-first testing gate: `test_pyramid_contract.json` entry added before test file creation (T-000). TF module structural tests before TF files created.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: N/A — no pre-PR smoke findings.

## Delivery Slices

### Slice 1 — Terraform standalone module (red → green)

**Red phase:**
- T-000: Add `tests/infra/modules/dns/test_contract.py` to `test_pyramid_contract.json` (unit scope) — MUST be done before T-001 to avoid pre-commit hook failure.
- T-001: Write failing test assertions for TF module structure (AC-001 through AC-004, AC-007):
  - AC-001: `main.tf` declares `stackit_dns_zone.this` with `project_id`, `name`, `dns_name = trimsuffix(...)`.
  - AC-002: `variables.tf` declares five required variables.
  - AC-003: `outputs.tf` declares `zone_id` and `dns_name`.
  - AC-004: `versions.tf` declares `stackitcloud/stackit = 0.88.0`.
  - AC-007: `terraform validate` passes (tested via subprocess or static grep).
  Run pytest — confirm assertions fail (TF files are stubs).

**Green phase:**
- T-002: Write `infra/cloud/stackit/terraform/modules/dns/main.tf` with `stackit_dns_zone.this`.
- T-003: Write `infra/cloud/stackit/terraform/modules/dns/variables.tf` with five variables.
- T-004: Write `infra/cloud/stackit/terraform/modules/dns/outputs.tf` with `zone_id` and `dns_name`.
- T-005: Write `infra/cloud/stackit/terraform/modules/dns/versions.tf` with `stackitcloud/stackit = 0.88.0`.
- T-006: Run pytest on slice 1 assertions — confirm AC-001 through AC-004, AC-007 green.

### Slice 2 — Smoke strengthening and test coverage (red → green)

**Red phase:**
- T-007: Write failing test assertions for smoke script (AC-005, AC-006) and state contract (AC-008, AC-009, AC-010):
  - AC-005: `dns_smoke.sh` contains a non-empty check for `zone_id`.
  - AC-006: `dns_smoke.sh` contains a non-empty check for `zone_fqdn`.
  - AC-008: `test_pyramid_contract.json` entry exists for the dns test file.
  - AC-009: `test_contract.py` passes with ≥ 10 assertions.
  - AC-010: Mock runtime state fixture contains `zone_id`, `zone_name`, `zone_fqdn` keys.
  Run pytest — confirm AC-005 and AC-006 fail (smoke only checks `zone_name` currently).

**Green phase:**
- T-008: Update `scripts/bin/infra/dns_smoke.sh` to add `zone_id` and `zone_fqdn` non-empty checks.
- T-009: Run `uv run pytest tests/infra/modules/dns/test_contract.py -v` — all ≥ 10 assertions green (AC-009).

## Change Strategy
- Migration/rollout sequence: TF module files are new; no consumer migration required. Smoke strengthening is additive (adds checks to existing script).
- Backward compatibility policy: Fully backward compatible. The apply.sh already writes `zone_id` and `zone_fqdn` to state; smoke strengthening catches missing keys that were previously unchecked.
- Rollback plan: Revert TF module files (they are new; no existing resource). Revert smoke script change (removes the new checks). No state file migration needed.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run pytest tests/infra/modules/dns/test_contract.py -v` (≥ 10 assertions).
- Contract checks: `make infra-contract-test-fast` (includes dns module after pyramid contract entry added).
- Integration checks: `uv run pytest tests/infra/test_optional_modules.py -v -k dns` — confirm existing dns flow test passes with strengthened smoke.
- E2E checks: N/A — no live infrastructure test in this work item.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: Tooling/infrastructure-only change. No app delivery workflow affected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/dns/README.md` — expand with standalone TF module section, runtime state contract table, smoke check documentation, and destroy warning.
- Consumer docs updates: Mirror sync to `scripts/templates/blueprint/bootstrap/docs/platform/modules/dns/README.md` via `sync_module_contract_summaries.py`.
- Mermaid diagrams updated: None required — architecture.md diagram is in the spec artifact, not the module doc.
- Docs validation commands: `make docs-build`, `make docs-smoke`.

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP route handlers or filter/payload-transform logic.
- Publish checklist: requirement/contract coverage, key reviewer files, validation evidence, rollback notes.

## Operational Readiness
- Logging/metrics/traces: Script output prefixed `[dns]` (already enforced by the existing scripts). No new metrics or traces.
- Alerts/ownership: No alerting additions. Smoke exit code is the health signal.
- Runbook updates: Module README documents the destroy warning (risk of live DNS record disruption).

## Risks and Mitigations
- Risk 1 (provider schema) → mitigation: Q-1/Q-2 must be answered before implementation. If nameservers attribute exists, add it as an additional output in T-004. If DNSSEC attribute exists, add it as a variable and resource attribute in T-002/T-003.
- Risk 2 (DNS zone deletion) → mitigation: Document in module README that destroying a live DNS zone disrupts resolution for all records in the zone. Add a destroy warning to the smoke script output.
