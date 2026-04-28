# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Failing test + parse fix

- [x] T-001 Write two failing regression tests in `tests/infra/test_runtime_credentials_eso.py`: (a) newline-separated `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` with comma-in-value (data URI) — confirm fails against current parser; (b) comma-separated input rejected with non-zero exit + `log_warn` — confirm current parser does NOT reject (SDD-C-024)
- [x] T-001a Migrate existing test `test_dry_run_reconcile_writes_success_state_and_renders_source_secret`: update `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` from comma-separated to newline-separated format (line 42 in test file)
- [x] T-002 Update `parse_literal_pairs()` in `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh`: remove `IFS=',' read -r -a raw_pairs` + for-loop entirely; replace with `while IFS= read -r pair` newline-only loop; add `log_warn` on missing `=`, empty key, or empty value
- [x] T-003 Update `record_reconcile_issue` error message to reference newline-separated as the sole accepted format (`key=value` one per line)

## Implementation — Slice 2: Documentation

- [ ] T-004 Update `docs/platform/consumer/runtime_credentials_eso.md`: declare newline-separated as the ONLY accepted format; state comma-separated is no longer accepted; update usage example with `$'...'` quoting; add migration note for consumers on comma-separated format
- [ ] T-005 Update bootstrap template copy `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` with the same changes as T-004

## Test Automation

- [x] T-101 Confirm new test (T-001) is green after T-002 fix; confirm it is a positive-path assertion: newline-separated input with comma-in-value returns a correctly parsed pair (SDD-C-023)
- [x] T-102 Confirm `test_dry_run_reconcile_writes_success_state_and_renders_source_secret` passes after T-001a migration to newline-separated format
- [x] T-103 Confirm `test_required_mode_fails_on_invalid_literal_contract` (missing `=` separator) continues to return non-zero (no regression in error-path behavior)

## Validation and Release Readiness

- [ ] T-201 Run `make quality-hooks-run` — all checks pass
- [ ] T-202 Run `python3 -m pytest tests/infra/test_runtime_credentials_eso.py -v` — all tests pass
- [ ] T-203 Confirm no stale TODOs or dead code introduced
- [ ] T-204 Run `make docs-build && make docs-smoke` — passes
- [ ] T-205 Run `make quality-hardening-review` — passes

## Publish

- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md`
- [ ] P-003 Ensure PR description references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` verified — no-impact (auth reconciliation only)
- [ ] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` verified — no-impact
- [ ] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` verified — no-impact
- [ ] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` verified — no-impact
- [ ] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` verified — no-impact
