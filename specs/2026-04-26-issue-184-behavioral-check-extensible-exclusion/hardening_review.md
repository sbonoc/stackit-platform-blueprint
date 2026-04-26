# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: The behavioral check symbol exclusion set in `upgrade_shell_behavioral_check.py` was hardcoded as a module-level frozenset with no consumer-visible extension point. Consumers whose runtime helpers are injected via deep source chains had no supported workaround for false-positive unresolved-symbol failures, forcing them to patch blueprint-managed code. This work adds `extra_excluded_tokens` to `blueprint/contract.yaml`, the `extra_excluded_count` diagnostic field to `ShellBehavioralCheckResult`, and the NFR-OBS-001 stderr log to close the false-positive suppression gap without mutating the base set.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `[BEHAVIORAL-CHECK] applying N consumer extra excluded tokens` emitted to stderr when extra tokens are applied (NFR-OBS-001). `extra_excluded_count` field added to `ShellBehavioralCheckResult` and included in `as_dict()` output surfaced in `artifacts/blueprint/upgrade_postcheck.json` (NFR-OPS-001).
- Operational diagnostics updates: operators can inspect `extra_excluded_count` in the postcheck JSON artifact to confirm consumer tokens were applied.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: `_EXCLUDED_TOKENS` base set remains immutable (module-level frozenset constant, never mutated). `effective_excluded = _EXCLUDED_TOKENS | valid_extra` is computed locally per invocation (DD-001). `extra_excluded_tokens` is keyword-only with frozenset default — backward-compatible (DD-002). `_find_unresolved_call_sites` receives the merged set via an `excluded` keyword-only parameter rather than reading module state — clean dependency injection.
- Test-automation and pyramid checks: 7 new unit tests added to `test_upgrade_shell_behavioral_check.py` (classified as unit in `test_pyramid_contract.json`). 516 blueprint suite tests pass with zero regressions. Pyramid ratios unchanged.
- Documentation/diagram/CI/skill consistency checks: `blueprint-consumer-upgrade` SKILL.md updated with consumer false-positive callout. `blueprint/contract.yaml` updated with commented example field. ADR approved.

## Proposals Only (Not Implemented)
- none
