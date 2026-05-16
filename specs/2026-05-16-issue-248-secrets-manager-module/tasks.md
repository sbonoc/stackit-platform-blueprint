# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations — all approved in PR #305 comments)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Terraform standalone module (red → green)
- [ ] T-000 Add `tests/infra/modules/secrets-manager/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope (AC-015) — MUST be done before T-001 to avoid pre-commit hook failure
- [ ] T-001 Write failing `test_contract.py` assertions for TF module structure (AC-001, AC-002, AC-003, AC-004, AC-004b):
      - AC-001: `main.tf` declares `stackit_secretsmanager_instance.this` with required attributes and `lifecycle { create_before_destroy = true }`
      - AC-002: `main.tf` declares `stackit_secretsmanager_user.this` with required attributes
      - AC-003: `variables.tf` declares all six required variables
      - AC-004: `outputs.tf` declares `instance_id`, `username`, `password` (sensitive)
      - AC-004b: `versions.tf` exists and declares `stackitcloud/stackit` required provider with pinned version constraint
      Run pytest — confirm assertions fail (files not yet created).
- [ ] T-002 Write `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` with `stackit_secretsmanager_instance.this` and `stackit_secretsmanager_user.this`
- [ ] T-003 Write `infra/cloud/stackit/terraform/modules/secrets-manager/variables.tf` with six variables
- [ ] T-004 Write `infra/cloud/stackit/terraform/modules/secrets-manager/outputs.tf` with `instance_id`, `username`, `password`
- [ ] T-004b Write `infra/cloud/stackit/terraform/modules/secrets-manager/versions.tf` with `stackitcloud/stackit` required provider at pinned version (match all other module versions.tf files)
- [ ] T-005 Run pytest on slice 1 assertions — confirm AC-001 through AC-004b green

### Slice 2 — Shell layer and contract (red → green)
- [ ] T-006 Write failing `test_contract.py` assertions for AC-005 through AC-015 (contract outputs, namespace/auth helpers, reconcile+delete secret, state keys, security invariant, versions.tf, pyramid contract entry)
      Run pytest — confirm AC-005 through AC-013 fail (not yet implemented).
- [ ] T-007 Update `blueprint/modules/secrets-manager/module.contract.yaml` — add `SECRETS_MANAGER_NAMESPACE` and `SECRETS_MANAGER_AUTH_METHOD_DETAILS` to `outputs.produced`
- [ ] T-008 Add required `source` statements to `scripts/lib/infra/secrets_manager.sh` (for `stackit_foundation_outputs.sh`, `versions.sh`, `fallback_runtime.sh`); add `secrets_manager_namespace()`, `secrets_manager_auth_method_details()`, `secrets_manager_reconcile_runtime_secret()`, and `secrets_manager_delete_runtime_secret()` functions
- [ ] T-009 Update `scripts/bin/infra/secrets_manager_apply.sh` — call `secrets_manager_reconcile_runtime_secret()` and write `namespace` + `auth_method_details` to state file
- [ ] T-010 Update `scripts/bin/infra/secrets_manager_plan.sh` — write `namespace` to plan state output
- [ ] T-011 Update `scripts/bin/infra/secrets_manager_smoke.sh` — add non-empty checks for both `namespace` and `auth_method_details` keys
- [ ] T-011b Update `scripts/bin/infra/secrets_manager_destroy.sh` — call `secrets_manager_delete_runtime_secret()` before removing state files (AC-014)
- [ ] T-012 Update `tests/infra/test_optional_modules.py` `test_secrets_manager_module_flow` — add assertions for `namespace` and `auth_method_details` keys in runtime state
- [ ] T-013 Run `uv run pytest tests/infra/modules/secrets-manager/test_contract.py -v` — all ≥ 10 assertions green (AC-013)
- [ ] T-014 Run `uv run pytest tests/infra/test_optional_modules.py -v -k secrets_manager` — green

## Test Automation
- [ ] T-101 `tests/infra/modules/secrets-manager/test_contract.py` written (T-001, T-006) and passing (T-013) — ≥ 10 assertions
- [ ] T-102 N/A — no API contract or Pact test
- [ ] T-103 N/A — no filter or payload-transform logic
- [ ] T-104 N/A — no reproducible pre-PR smoke/curl finding; new capability, not bug fix
- [ ] T-105 `tests/infra/test_optional_modules.py` updated with new state key assertions (T-012, T-014)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [ ] T-A02 N/A — no UI changes
- [ ] T-A03 N/A — no UI changes
- [ ] T-A04 N/A — no UI changes
- [ ] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [ ] T-201 Run `uv run pytest tests/infra/modules/secrets-manager/test_contract.py tests/infra/test_optional_modules.py -v` — all pass; `make quality-hooks-fast` passes
- [ ] T-202 Attach evidence to traceability document — traceability.md updated post-implementation
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`; use "Part of #248" (NOT "Closes #248")

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling/infrastructure-only change, no app delivery workflow impact
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling/infrastructure-only change
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling/infrastructure-only change
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling/infrastructure-only change
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling/infrastructure-only change
