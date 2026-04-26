# PR Context

## Summary
- Work item: 2026-04-26-issue-164-upgrade-version-pin-report
- Objective: Surface version pin changes and downstream template impact in the upgrade residual report so operators know what manual template sync is required before discovering drift reactively via `make infra-validate`.
- Scope boundaries: New Python script `upgrade_version_pin_diff.py` (Stage 1b, non-blocking); new `_render_version_pin_section` in `upgrade_residual_report.py`; pipeline wiring in `upgrade_consumer_pipeline.sh`; skill runbook update. No API, HTTP route, or managed-service changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-PERF-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: none — no new env vars, no new make targets, no API changes; `BLUEPRINT_UPGRADE_SOURCE` and `BLUEPRINT_UPGRADE_REF` already declared by the pipeline

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_version_pin_diff.py` — new Stage 1b script
  - `scripts/lib/blueprint/upgrade_residual_report.py` — `_render_version_pin_section` addition
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — Stage 1b wiring
  - `tests/blueprint/test_upgrade_version_pin_diff.py` — 27 unit tests (all green)
- High-risk files:
  - `upgrade_consumer_pipeline.sh` — Stage 1b added with `|| true` guard; non-blocking by design

## Validation Evidence
- Required commands executed: `make quality-sdd-check`, `make quality-hooks-run`, `pytest tests/blueprint/test_upgrade_version_pin_diff.py tests/blueprint/test_upgrade_pipeline.py`
- Result summary: 95 tests pass (27 new + 68 existing); `make quality-sdd-check` passes; `make quality-hooks-run` passes
- Artifact references: `artifacts/blueprint/version_pin_diff.json` (new, emitted by Stage 1b); `artifacts/blueprint/upgrade-residual.md` (extended with Version Pin Changes section)

## Risk and Rollback
- Main risks: Baseline ref unavailable in cloned source → script exits zero with error artifact; residual report emits manual fallback command. Variable-name grep may produce false positives for short variable names — mitigated by substring match of full variable name string.
- Rollback strategy: Remove the Stage 1b block from `upgrade_consumer_pipeline.sh` and remove `_render_version_pin_section` call from `upgrade_residual_report.py`; no persistent state changes required.

## Deferred Proposals
- Automated template sync (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`) — detection and reporting only in this work item; sync deferred.
- Value-based template scanning (matching hardcoded version strings, not just variable names) — deferred; variable-name grep covers the common case.
