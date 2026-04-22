# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Wrap `run_kustomize_apply` in `if !` guard in `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` (Issue #105)
- [x] T-002 Replace `record_reconcile_issue` with `log_info` for `gho_` token in `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` (Issue #110)
- [x] T-003 Create ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-105-110-runtime-auth-best-effort-fix.md`

## Test Automation
- [x] T-101 Add `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` in `tests/infra/test_tooling_contracts.py`
- [x] T-102 Add `RuntimeAuthBestEffortTests::test_argocd_repo_credentials_accepts_gho_token` in `tests/infra/test_tooling_contracts.py`
- [x] T-103 N/A — no filter/payload-transform logic
- [x] T-104 Issues #105 and #110 translated into `RuntimeAuthBestEffortTests` structural assertions
- [x] T-105 `make infra-contract-test-fast` passes (99 tests)

## Validation and Release Readiness
- [x] T-201 `make quality-hooks-fast` passes
- [x] T-202 Traceability document updated
- [x] T-203 No stale TODOs, dead code, or drift
- [x] T-204 `make docs-build` and `make docs-smoke` pass (no doc changes)
- [x] T-205 `make quality-hardening-review` passes

## Publish
- [x] P-001 `hardening_review.md` updated
- [x] P-002 `pr_context.md` updated
- [x] P-003 PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected
