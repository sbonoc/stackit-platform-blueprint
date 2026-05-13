# ADR: Issue #265/#271 Follow-on — Source-Exists Inference for Blueprint-Managed Catch-All Conflicts

- **Status**: approved
- **Date**: 2026-05-13
- **Work item**: `specs/2026-05-13-issue-265-271-source-exists-inference/`
- **Prerequisite**: Issue #270 (PR #290) — test ownership contract, shipped 2026-05-13

## Context

The conflict triage manifest (`upgrade_triage.json`) introduced in issues #265/#271 maps `ownership_class` to `recommended_action`. The conservative mapping for the catch-all `blueprint-managed` class was `human_required`, explicitly documented in ADR-issue-265-271-conflict-resolution-ux as Option A:

> "The catch-all `blueprint-managed` → `human_required` is a conservative choice (Option A) that prevents auto-overwriting consumer-modified files not yet in any explicit blueprint ownership category. This will be revisited when Issue #270 ships explicit consumer test ownership markers."

Issue #270 shipped 2026-05-13. It relocated all blueprint-author test files from `tests/infra/` to `tests/blueprint/` (source_only — never delivered to consumers), added the FR-005 contract assertion, and removed 4 entries from `spec.repository.required_files`. The case that made Option B unsafe — a consumer-created file in a blueprint-tracked directory (e.g. `tests/infra/test_my_custom.py`) appearing with `source_exists=True` yet being consumer-owned — is now eliminated.

`UpgradeEntry.source_exists=True` for a `blueprint-managed` file now reliably indicates that the file originates from the blueprint source tree, not from consumer creation.

## Decision

### Inference rule

Amend `_recommended_action(ownership_class, source_exists)` in `upgrade_consumer.py`:

- `blueprint-managed` + `source_exists=True` → `take_source`
- `blueprint-managed` + `source_exists=False` → `human_required` (unchanged — file is consumer-only)

All other `ownership_class` values retain their existing mapping.

### Schema amendment

Add `source_exists` as an optional boolean property to the conflict entry in `upgrade_triage.schema.json`. Schema version remains `1` (non-breaking addition).

### Audit trail

The `reason` field for inferred `take_source` entries is set to:
`"source_exists=True; blueprint-managed ownership inferred (issue #270 consumer ownership markers shipped)"`

## Consequences

- **Positive**: `blueprint-managed` catch-all conflicts with `source_exists=True` are auto-resolved by `blueprint-upgrade-consumer-resolve` without user interaction. Based on the real upgrade evidence (88 conflicts, dhe-marketplace v1.7.0 → v1.10.0), this eliminates the remaining `human_required` rows that were not already covered by explicit ownership classes.
- **Positive**: `upgrade_triage.json` now includes `source_exists` per entry, providing a complete audit trail for every auto-resolution decision.
- **Backward compatible**: schema version stays at 1; the `source_exists` field is optional; existing triage files without the field remain valid.
- **Residual risk**: a consumer who intentionally creates a file under a `blueprint_managed_roots` path that coincidentally has the same relative path as a blueprint source file will have it auto-overwritten. This is governed by the existing `blueprint_managed_roots` exclusivity contract; no new risk surface is introduced.
- **ADR technical decision sign-off**: approved
