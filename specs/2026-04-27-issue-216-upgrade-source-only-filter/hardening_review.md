# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Bug #216 — `resolve_contract_upgrade.py` Stage 3 copied `source_only` wholesale from source contract, overwriting consumer additions and failing to drop entries whose paths existed in the consumer; restored v1.7.0 `_filter_source_only` semantics (Phase 1 drop + Phase 2 carry-forward).

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: Added two `[PIPELINE] Stage 3` stdout log lines when `dropped_source_only` or `kept_consumer_source_only` are non-empty.
- Operational diagnostics updates: `contract_resolve_decisions.json` now includes `dropped_source_only` and `kept_consumer_source_only` arrays for post-run inspection.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: New `_filter_source_only` helper follows the same single-responsibility pattern as existing `_merge_required_files` and `_filter_prune_globs`; frozen dataclass extended without breaking existing callers via default factory fields.
- Test-automation and pyramid checks: 4 unit regression tests added covering Phase 1 drop (specs/, CLAUDE.md), Phase 2 carry-forward, and no-conflict regression guard; 3 confirmed red before fix, 1 was green (regression guard); all 4 green after fix; `test_resolve_contract_upgrade.py` classified as `unit` in `test_pyramid_contract.json`.
- Documentation/diagram/CI/skill consistency checks: Module-level docstring updated to document FR-009; no diagram or CI changes needed (Python script fix only).

## Proposals Only (Not Implemented)
- none
