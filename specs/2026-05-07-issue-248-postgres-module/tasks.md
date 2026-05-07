# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Tests RED
- [x] T-001 Write `tests/infra/modules/postgres/test_contract.py` (contract fixture assertions — all RED)
- [x] T-002 Write `tests/infra/modules/postgres/test_postgres_module.py` (module unit assertions — all RED)
- [x] T-003 Add two tooling contract tests to `tests/infra/test_tooling_contracts.py`: `test_optional_module_execution_resolves_local_fallback_modes_for_postgres` and `test_optional_module_execution_resolves_stackit_provider_backed_postgres_modes`
- [x] T-004 Register both new test files in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope
- [x] T-005 Confirm all new tests fail (RED) before proceeding to implementation slices

## Implementation — Slice 2: Execution Class Fix + Secret-Backed Credentials
- [x] T-010 Update `scripts/lib/infra/module_execution.sh` — change local lane class from `provider_backed` to `fallback_runtime` for `postgres:plan|apply` and `postgres:destroy`
- [x] T-011 Add `postgres_credential_secret_name()`, `postgres_reconcile_runtime_secret()`, `postgres_delete_runtime_secret()` to `scripts/lib/infra/postgres.sh`
- [x] T-012 Update `postgres_render_values_file()` in `scripts/lib/infra/postgres.sh` — remove plaintext credential bindings, add `POSTGRES_CREDENTIAL_SECRET_NAME` binding
- [x] T-013 Update `infra/local/helm/postgres/values.yaml` — replace `auth.username`/`auth.password` with `auth.existingSecret: blueprint-postgres-auth`
- [x] T-014 Update `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml` — same change (use `{{POSTGRES_CREDENTIAL_SECRET_NAME}}`)
- [x] T-015 Update `scripts/bin/infra/postgres_apply.sh` — call `postgres_reconcile_runtime_secret` before `run_helm_upgrade_install` in `helm)` case
- [x] T-016 Update `scripts/bin/infra/postgres_destroy.sh` — call `postgres_delete_runtime_secret` after `run_helm_uninstall` in `helm)` case; add `--ignore-not-found`
- [x] T-017 Update `scripts/bin/infra/bootstrap.sh` — replace plaintext credential bindings with `POSTGRES_CREDENTIAL_SECRET_NAME` in `postgres)` case
- [x] T-018 Confirm class fix and Secret-backed credential tests GREEN

## Implementation — Slice 3: STACKIT Terraform Module
- [x] T-020 Implement `infra/cloud/stackit/terraform/modules/postgres/main.tf` (`stackit_postgresflex_instance`, `stackit_postgresflex_user`, `stackit_postgresflex_database`; ACL validation; `depends_on`)
- [x] T-021 Write `infra/cloud/stackit/terraform/modules/postgres/variables.tf` (all contract inputs with defaults)
- [x] T-022 Write `infra/cloud/stackit/terraform/modules/postgres/outputs.tf` (all contract output keys)
- [x] T-023 Write `infra/cloud/stackit/terraform/modules/postgres/versions.tf` (`stackitcloud/stackit` provider pin)
- [x] T-024 Confirm Terraform module tests GREEN

## Implementation — Slice 4: Smoke Hardening + Docs
- [x] T-030 Update `scripts/bin/infra/postgres_smoke.sh` — add `host`, `port`, `db_name` non-empty validation checks
- [x] T-031 Complete `docs/platform/modules/postgres/README.md` — Standalone STACKIT Terraform Module, Credentials, Smoke Checks, Destroy, Local vs STACKIT Differences, Env-Var Reference
- [x] T-032 Sync seed docs if needed (`python3 scripts/lib/docs/sync_platform_seed_docs.py`)
- [x] T-033 Confirm smoke + docs tests GREEN

## Test Automation
- [x] T-101 Confirm `pytest tests/infra/modules/postgres/ -v` — all green (≥ 20 assertions)
- [x] T-102 Confirm `pytest tests/infra/test_tooling_contracts.py -k postgres` — green (2/2)
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 N/A — no reproducible pre-PR deterministic failures
- [x] T-105 N/A — no boundary/integration tests beyond above

## Accessibility Testing
- [x] T-A01 Confirmed NFR-A11Y-001 is declared as "N/A — no UI component" in `spec.md`
- [x] T-A02 N/A — no UI
- [x] T-A03 N/A — no UI
- [x] T-A04 N/A — no UI
- [x] T-A05 N/A — no UI

## Validation and Release Readiness
- [x] T-201 Run `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` — all checks pass
- [x] T-202 Attach evidence to `traceability.md` — pending implementation
- [x] T-203 Confirm no stale TODOs/dead code/drift
- [x] T-204 Run `make quality-docs-check-changed`
- [x] T-205 Run `make quality-hardening-review` — covered by quality-hooks-fast

## Publish
- [x] P-001 Complete `hardening_review.md`
- [x] P-002 Complete `pr_context.md`
- [x] P-003 Ensure PR description follows repository template

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets
