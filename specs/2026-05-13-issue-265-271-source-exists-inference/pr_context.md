# PR Context

## Summary
- Work item: issue-265-271-source-exists-inference — source_exists inference for blueprint-managed catch-all conflicts
- Objective: Promote `blueprint-managed` catch-all conflicts where `source_exists=True` from `human_required` to `take_source` in `upgrade_triage.json`, enabling auto-resolution by `blueprint-upgrade-consumer-resolve`. Safe since issue #270 (PR #290) eliminated consumer-created files in blueprint-tracked directories.
- Scope boundaries: Two files only — `scripts/lib/blueprint/upgrade_consumer.py` (2 functions: `_recommended_action`, `_write_upgrade_triage`) and `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` (1 optional boolean property). No CLI flags, no make targets, no pipeline stages, no consumer-visible schema breaking changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-REL-001, NFR-REL-002, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: `upgrade_triage.schema.json` — `source_exists` added as optional (non-required) boolean on conflict entry; schema version remains 1.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_recommended_action()` (line ~1708) and `_write_upgrade_triage()` (line ~1721): inference logic and source_exists field addition
  - `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` — optional `source_exists` boolean property
  - `tests/blueprint/test_upgrade_consumer.py` — `SourceExistsInferenceTests` class (end of file): 3 new tests covering FR-001/FR-002/FR-003
- High-risk files: `upgrade_consumer.py` — existing call to `_recommended_action(ownership_class)` updated; default `source_exists=False` preserves all pre-existing behavior for non-blueprint-managed classes and for blueprint-managed entries without `source_exists`.

## Validation Evidence
- Required commands executed: `uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v` (3 PASS), `uv run python3 -m pytest tests/infra/test_conflict_triage_issue_265.py -v` (5 PASS), `make infra-validate` (PASS), `make docs-build` (PASS), `make docs-smoke` (PASS), `make infra-contract-test-fast` (PASS)
- Result summary: 3/3 new source_exists tests GREEN; 5/5 existing triage tests GREEN; 20 pre-existing failures in full blueprint suite unchanged (plan/apply/reconcile classification regressions; confirmed pre-existing via git stash diff: 23 failures before including 3 RED, 20 failures after); zero new regressions.
- Artifact references: `evidence_manifest.json`, `hardening_review.md`

## Risk and Rollback
- Main risks: A consumer who creates a file under a `blueprint_managed_roots` path with the same relative path as a blueprint source file will have that file auto-overwritten. Governed by the existing `blueprint_managed_roots` exclusivity contract; no new risk surface introduced (documented in ADR Consequences).
- Rollback strategy: Revert `_recommended_action` to single-parameter form; revert `_write_upgrade_triage` to exclude `source_exists` field; revert schema. No persisted state (triage JSON is regenerated each upgrade run).

## Deferred Proposals
- Proposal 1 (not implemented): Active cleanup of stale consumer-created files in `blueprint_managed_roots` paths that coincidentally match blueprint source paths — out of scope; `blueprint_managed_roots` exclusivity contract governs this; no new risk introduced.
