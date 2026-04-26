# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- `SPEC_READY=true` — gate is open.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Adding one keyword-only parameter and two dataclasses. No wrapper layers or abstractions beyond what the requirement demands.
- Anti-abstraction gate: Direct frozenset union (`_EXCLUDED_TOKENS | extra_excluded_tokens`) — no intermediate class.
- Integration-first testing gate: Red tests written first (Slice 1) covering AC-001 through AC-007 before any implementation.
- Positive-path filter/transform test gate: AC-001 tests that a token in `extra_excluded_tokens` produces zero unresolved symbols (positive path, non-empty fixture value).
- Finding-to-test translation gate: No pre-PR smoke finding applicable (no HTTP routes touched).

## Delivery Slices

### Slice 1 (RED) — Test scaffolding for `run_behavioral_check` extension
Write failing tests in `tests/blueprint/test_upgrade_shell_behavioral_check.py`:
- `TestExtraExcludedTokens.test_extra_token_suppresses_unresolved_symbol` (AC-001, AC-004)
- `TestExtraExcludedTokens.test_absent_extra_tokens_preserves_baseline_behaviour` (AC-002, AC-003)
- `TestExtraExcludedTokens.test_invalid_token_skipped_gracefully` (AC-005)
- `TestExtraExcludedTokens.test_extra_excluded_count_in_result` (AC-006)
- `TestExtraExcludedTokens.test_obs_log_emitted_when_tokens_applied` (AC-007 / NFR-OBS-001)

### Slice 2 (GREEN) — Implement `upgrade_shell_behavioral_check.py` changes
- Add `extra_excluded_count: int = 0` field to `ShellBehavioralCheckResult`.
- Add `extra_excluded_tokens: frozenset[str] = frozenset()` keyword-only param to `run_behavioral_check`.
- Validate tokens: skip non-string/empty, log count to stderr.
- Compute `effective_excluded = _EXCLUDED_TOKENS | extra_excluded_tokens` locally.
- Pass `effective_excluded` into `_find_unresolved_call_sites`.
- Set `extra_excluded_count` in returned result.
- All Slice 1 tests turn green.

### Slice 3 (RED) — Test scaffolding for contract reading
Write failing tests in `tests/blueprint/test_upgrade_shell_behavioral_check.py` (or a separate test for postcheck):
- `TestPostcheckReadsExtraTokensFromContract.test_extra_tokens_loaded_from_contract_yaml` — mock contract loader, verify tokens passed to `run_behavioral_check`.

### Slice 4 (GREEN) — Implement `contract_schema.py` and `upgrade_consumer_postcheck.py` changes
- Add `BehavioralCheckUpgradeContract(extra_excluded_tokens: list[str])` dataclass.
- Add `UpgradeContract(behavioral_check: BehavioralCheckUpgradeContract)` dataclass.
- Extend `BlueprintContract` with `upgrade: UpgradeContract` field; loader reads optional `spec.upgrade` key.
- In `upgrade_consumer_postcheck.py`: read `contract.upgrade.behavioral_check.extra_excluded_tokens`, filter to valid strings, pass as `frozenset` to `run_behavioral_check`.
- All Slice 3 tests turn green.

### Slice 5 — Blueprint contract.yaml example + skills doc update
- Add commented-out example `spec.upgrade.behavioral_check.extra_excluded_tokens: []` to `blueprint/contract.yaml`.
- Add callout in `blueprint-consumer-upgrade` SKILL.md postcheck step.

### Slice 6 — Quality gates
- Run `make quality-sdd-check` and fix any violations.
- Run `make quality-hooks-run`.
- Run `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — all green.

## Change Strategy
- Migration/rollout sequence: additive only; all callers of `run_behavioral_check` continue to work with default `frozenset()`.
- Backward compatibility policy: keyword-only default ensures zero breaking changes.
- Rollback plan: revert `upgrade_consumer_postcheck.py` to not read the field; the `run_behavioral_check` signature change is backward compatible so no callers break.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — all existing + new tests green.
- Contract checks: `make quality-sdd-check` — pyramid and SDD gates.
- Integration checks: none required (no external services).
- E2E checks: none required.

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
- Notes: upgrade pipeline internal change only.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `blueprint-consumer-upgrade` SKILL.md — add callout in postcheck step.
- Consumer docs updates: `blueprint/contract.yaml` example field.
- Mermaid diagrams updated: none — no pipeline stage added.
- Docs validation commands: `make docs-build`, `make docs-smoke`.

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP routes touched).
- Publish checklist: requirement/contract coverage, key reviewer files, validation evidence, rollback notes.

## Operational Readiness
- Logging/metrics/traces: `[BEHAVIORAL-CHECK] applying N consumer extra excluded tokens` to stderr.
- Alerts/ownership: none required.
- Runbook updates: `blueprint-consumer-upgrade` SKILL.md step update.

## Risks and Mitigations
- Risk 1: `contract_schema.py` hand-rolled YAML parser must handle optional new `spec.upgrade` key → mitigation: make key optional with graceful default; test with contract missing the key.
- Risk 2: `_find_unresolved_call_sites` currently reads `_EXCLUDED_TOKENS` implicitly (module-level) rather than as a parameter — must verify the actual call path accepts the merged set correctly.
