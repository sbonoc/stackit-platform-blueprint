# Hardening Review

## Repository-Wide Findings Fixed
- Added deterministic required-file reconciliation gate in upgrade validate with repo-mode filtering.
- Added coupled generated-reference contract checks to avoid partial generated-doc drift.
- Added preflight required-surface risk surfacing before apply.
- Hardened wrapper metrics emission with new required-file/generated-reference counters.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates:
  - `blueprint_upgrade_validate_required_files_expected_total`
  - `blueprint_upgrade_validate_required_files_missing_total`
  - `blueprint_upgrade_validate_generated_reference_missing_paths_total`
  - `blueprint_upgrade_validate_generated_reference_missing_targets_total`
  - `blueprint_upgrade_validate_generated_reference_failed_targets_total`
- Operational diagnostics updates:
  - validate stderr now reports missing required files with remediation action category
  - validate stderr now reports coupled generated-reference failures with missing path/target diagnostics
  - preflight payload now reports `required_surfaces_at_risk`

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks:
  - kept scope constrained to upgrade validation/preflight bounded contexts and report contracts
  - no cross-layer import boundary regressions introduced
- Test-automation and pyramid checks:
  - added fixture-backed unit/contract tests for missing required files and repo-mode gating
  - maintained schema assertions for validate report
- Documentation/diagram/CI/skill consistency checks:
  - completed work-item SDD artifacts and ADR linkage to satisfy SDD quality gates

## Proposals Only (Not Implemented)
- Build one shared `required_files_for_repo_mode` helper module consumed by all contract/upgrade validators to remove duplicate implementations.
