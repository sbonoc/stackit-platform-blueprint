# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: conflicts_unresolved tracked plan/apply metadata instead of active <<<<<<< markers; corrected in build_upgrade_reconcile_report to scan working tree at report-build time (#179)
- Finding 2: _find_unresolved_call_sites emitted false positives for case-label alternation lines and array initializer body tokens; both now suppressed (#180)
- Finding 3: _EXCLUDED_TOKENS missing tar, pnpm, and 13 blueprint bootstrap-chain runtime functions; all added (#181)
- Finding 4: Upgrade planner silently produced plans with uncovered source files; hard-fail audit gate added via audit_source_tree_coverage using git ls-files (#185)
- Finding 5: Fresh-env gate detected only file-set divergence, not content divergence; SHA-256 checksum comparison of artifacts/blueprint/ added with fail-on-divergence even when make targets exit 0 (#186)
- Finding 6: Generated ci.yml lacked a workflow-level permissions block; contents: read block inserted between on: and jobs: in _render_ci (#187)

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: upgrade planner emits WARNING to stderr per uncovered source file; gate log emits FAIL with reference to divergences in fresh_env_gate.json
- Operational diagnostics updates: fresh_env_gate.json now includes checksum-keyed divergence entries enabling targeted artifact diff diagnostics

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: each fix is confined to the module responsible for the behavior; no cross-cutting behavioral entanglement introduced; new helpers (_platform_owned_roots, compute_artifact_checksum_divergences) are pure functions with clear single responsibility
- Test-automation and pyramid checks: 7 new unit tests for reconcile-report marker tracking, 5 for checksum divergence detection, 2 for ci.yml permissions; test_upgrade_reconcile_report.py added to test_pyramid_contract.json unit scope; 392 tests pass
- Documentation/diagram/CI/skill consistency checks: blueprint/contract.yaml and bootstrap template kept in sync (diff empty); ci.yml regenerated from updated renderer; hardening_review and pr_context completed

## Proposals Only (Not Implemented)
- none
