# PR Context

## Summary
- Work item: issue-165 — Semantic annotations on merge-required upgrade plan entries
- Objective: Enrich every `merge-required` upgrade plan entry with a `semantic` annotation (`kind`, `description`, `verification_hints`) auto-generated from the baseline-to-source static diff, surfaced in `upgrade_plan.json`, `upgrade_summary.md`, and `upgrade_apply.json`.
- Scope boundaries: static analysis only (no file execution); shell scripts only; additive files get `structural-change` by design; no new CLI flags, no new artifacts, no schema breaking changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001 (function-added detected), AC-002 (variable-changed detected), AC-003 (structural-change fallback), AC-004 (per-entry error fallback), AC-005 (plan JSON carries semantic on both creation sites), AC-006 (summary renders annotations), AC-007 (apply result carries semantic)
- Contract surfaces changed: `upgrade_plan.schema.json` — optional `semantic` property on entry items; `upgrade_apply.schema.json` — optional `semantic` property on result items. Both changes are backward-compatible (field is optional, existing consumers unaffected).

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_semantic_annotator.py` — new annotator module (detection logic)
  - `scripts/lib/blueprint/upgrade_consumer.py` — UpgradeEntry/ApplyResult extension + both creation sites + summary renderer
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py` — both `merge-required` creation sites and `_write_summary` touched; regressions caught by 35 existing + 4 new integration tests

## Validation Evidence
- Required commands executed: `make quality-sdd-check`, `make quality-hooks-run`, `make docs-build`, `make docs-smoke`, `pytest tests/blueprint/test_upgrade_semantic_annotator.py tests/blueprint/test_upgrade_consumer.py`
- Result summary: all gates green — quality-sdd-check clean, quality-hooks-run clean, docs-build/smoke clean, 58/58 tests pass (19 annotator unit + 4 consumer integration + 35 existing consumer)
- Artifact references: `artifacts/docs/docs_build.env` (status=success), `artifacts/docs/docs_smoke.env` (status=success)

## Risk and Rollback
- Main risks: regex heuristics produce `structural-change` fallback for complex diffs (accepted MVP scope; always actionable). Missed creation site would produce `semantic=null` entries — covered by integration tests on both paths.
- Rollback strategy: revert commits `185f02b` (docs) and `995b1de` (implementation); schema changes are optional fields so no consumer JSON migration required.

## Deferred Proposals
- none
