# Tasks

## Spec Readiness Gate Checks
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Add `BehavioralCheckUpgradeContract` + `UpgradeContract` dataclasses to `contract_schema.py`; extend `BlueprintContract.upgrade`; update loader to handle optional `spec.upgrade` key
- [x] T-002 Add `extra_excluded_count: int` to `ShellBehavioralCheckResult`; add `extra_excluded_tokens` keyword-only param to `run_behavioral_check`; compute `effective_excluded = _EXCLUDED_TOKENS | extra_excluded_tokens`; validate tokens; emit NFR-OBS-001 log
- [x] T-003 Update `upgrade_consumer_postcheck.py` to read `contract.upgrade.behavioral_check.extra_excluded_tokens` and pass as frozenset to `run_behavioral_check`
- [x] T-004 Add commented example field to `blueprint/contract.yaml`
- [x] T-005 Add callout to `blueprint-consumer-upgrade` SKILL.md postcheck step

## Test Automation
- [x] T-101 Add `TestExtraExcludedTokens` class to `tests/blueprint/test_upgrade_shell_behavioral_check.py` (AC-001 through AC-007)
- [x] T-102 Add `TestPostcheckReadsExtraTokensFromContract` class with: `test_extra_tokens_loaded_from_contract_yaml` (FR-001, FR-006) and `test_absent_key_yields_empty_frozenset` (NFR-REL-001)
- [x] T-103 Positive-path assertion: token in `extra_excluded_tokens` → zero unresolved symbols (AC-001, non-empty fixture)

## Validation and Release Readiness
- [x] T-201 Run `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — all green (27 tests pass, 7 new)
- [x] T-202 Run `make quality-sdd-check` — all gates pass
- [x] T-203 Run `make quality-hooks-run` — all hooks pass
- [x] T-204 Confirm `test_pyramid_contract.json` — `test_upgrade_shell_behavioral_check.py` already classified as unit (no change needed)

## Publish
- [x] P-001 Update `hardening_review.md`
- [x] P-002 Update `pr_context.md` with coverage, key files, evidence, rollback notes
- [x] P-003 Open Draft PR; mark ready after quality gates pass

## App Onboarding Minimum Targets (Normative)
- App onboarding impact: no-impact — Python/YAML-only changes to upgrade pipeline tooling; no app onboarding surface modified.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — not applicable (no-impact)
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not applicable (no-impact)
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not applicable (no-impact)
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not applicable (no-impact)
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not applicable (no-impact)
