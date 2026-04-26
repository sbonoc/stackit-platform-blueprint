# Tasks

## Spec Readiness Gate Checks
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Add `BehavioralCheckUpgradeContract` + `UpgradeContract` dataclasses to `contract_schema.py`; extend `BlueprintContract.upgrade`; update loader to handle optional `spec.upgrade` key
- [ ] T-002 Add `extra_excluded_count: int` to `ShellBehavioralCheckResult`; add `extra_excluded_tokens` keyword-only param to `run_behavioral_check`; compute `effective_excluded = _EXCLUDED_TOKENS | extra_excluded_tokens`; validate tokens; emit NFR-OBS-001 log
- [ ] T-003 Update `upgrade_consumer_postcheck.py` to read `contract.upgrade.behavioral_check.extra_excluded_tokens` and pass as frozenset to `run_behavioral_check`
- [ ] T-004 Add commented example field to `blueprint/contract.yaml`
- [ ] T-005 Add callout to `blueprint-consumer-upgrade` SKILL.md postcheck step

## Test Automation
- [ ] T-101 Add `TestExtraExcludedTokens` class to `tests/blueprint/test_upgrade_shell_behavioral_check.py` (AC-001 through AC-007)
- [ ] T-102 Add `TestPostcheckReadsExtraTokensFromContract` test to verify postcheck reads and passes contract field
- [ ] T-103 Positive-path assertion: token in `extra_excluded_tokens` → zero unresolved symbols (AC-001, non-empty fixture)

## Validation and Release Readiness
- [ ] T-201 Run `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — all green
- [ ] T-202 Run `make quality-sdd-check` — all gates pass
- [ ] T-203 Run `make quality-hooks-run` — all hooks pass
- [ ] T-204 Confirm `test_pyramid_contract.json` — `test_upgrade_shell_behavioral_check.py` already classified as unit (no change needed)

## Publish
- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md` with coverage, key files, evidence, rollback notes
- [ ] P-003 Open Draft PR; mark ready after quality gates pass

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
