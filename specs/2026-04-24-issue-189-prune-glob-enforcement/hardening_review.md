# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Blueprint-source files (`specs/YYYY-MM-DD-*` and `docs/blueprint/architecture/decisions/ADR-*.md`) could be silently carried over by the upgrade apply phase into a generated-consumer repo without any detection. The upgrade validate and postcheck tooling did not check for these prune-glob-matched files, leaving the consumer repo in a state that would diverge from what `blueprint-init-repo` would have produced. This work adds `prune_glob_check` to the validate report and `prune-glob-violations` to the postcheck blocked reasons to close this detection gap.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: Validate script now emits one stderr line per violation in the format `prune-glob violation: <path> (matches: <glob>)`, providing actionable output in CI and terminal runs.
- Operational diagnostics updates: `artifacts/blueprint/upgrade_validate.json` now includes a `prune_glob_check` section (`status`, `globs_checked`, `violations`, `violation_count`, `remediation_hint`). `artifacts/blueprint/upgrade_postcheck.json` now includes a `prune_glob_violations` section and propagates `violation_count` to its `summary`.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: `_scan_prune_glob_violations()` is a single-responsibility pure function with no side effects (returns data; caller emits stderr). No new abstractions were introduced. Existing module boundaries (validate owns scanning, postcheck owns reporting) are preserved.
- Test-automation and pyramid checks: 5 new tests added (3 unit, 1 integration for validate, 1 integration for postcheck). Blueprint test pyramid ratios remain inside all bounds: unit=90.89% (min>60%), integration=7.13% (max≤30%), e2e=1.98% (max≤10%). 365 tests pass; 6 pre-existing failures (unrelated `test_bootstrap_templates`, `test_contract_bootstrap_surface`, `test_contract_init_governance` due to a missing `.spec-kit/policy-mapping.md.tmpl` template) remain unchanged.
- Documentation/diagram/CI/skill consistency checks: `docs/blueprint/architecture/execution_model.md` updated; bootstrap template synced (1 file updated). `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated with step 7a. JSON schema for both validate and postcheck reports updated (additive-only; backward compatible).

## Proposals Only (Not Implemented)
- Proposal 1: Consider a makefile target `make blueprint-check-prune-globs` that operators could run at any point in the consumer lifecycle, not only as part of the upgrade flow. Low priority; the current integration in validate+postcheck covers the critical upgrade gate.
- Proposal 2: Consider surfacing `prune_glob_check` violations in `upgrade_summary.md` alongside merge-required entries, for human-readable upgrade reports. Low priority; violations are already visible in stderr and in the JSON report.
