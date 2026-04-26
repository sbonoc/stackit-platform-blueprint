# ADR: Issue #164 — Version Pin Changes in Upgrade Residual Report

- **Status**: approved
- **Date**: 2026-04-26
- **Issue**: #164
- **Work item**: `specs/2026-04-26-issue-164-upgrade-version-pin-report/`
- **ADR technical decision sign-off**: approved

## Context

The 10-stage deterministic upgrade pipeline (`make blueprint-upgrade-consumer`, PR #193)
applies all blueprint file changes, resolves the contract, syncs bootstrap template mirrors,
and runs gate checks. It does not surface version pin changes in
`scripts/lib/infra/versions.sh` between the baseline and target blueprint tags.

Consumers discover version-driven template drift reactively: run `make infra-bootstrap`,
then `make infra-validate`, observe drift errors, manually identify which pin changed, and
manually sync the affected templates under `scripts/templates/infra/bootstrap/`. This
sequence is not documented in the upgrade report and is not part of the upgrade pipeline's
guided flow. The problem was identified during the v1.5.0 upgrade of
sbonoc/dhe-marketplace (the same upgrade cycle that produced Issue #189).

## Decision

Add a non-blocking "Stage 1b" to the upgrade pipeline that:

1. Reads `scripts/lib/infra/versions.sh` from both the baseline and target blueprint refs
   via local git operations against the already-cloned source repository.
2. Parses all `VARIABLE="value"` and `VARIABLE=value` assignments and classifies each
   variable as changed, new, removed, or unchanged.
3. For each changed or new variable, scans `scripts/templates/infra/bootstrap/` in the
   consumer working tree for files that contain a reference to the variable name.
4. Emits `artifacts/blueprint/version_pin_diff.json`.

Stage 10 (residual report) reads this artifact and renders a new "Version Pin Changes"
section with prescribed action: "After running `make infra-bootstrap`, verify and sync
affected templates, then re-run `make infra-validate`."

Any error in Stage 1b is logged and the pipeline continues. The residual report degrades
gracefully to a manual fallback instruction.

The upgrade consumer skill runbook is updated to document this section and the expected
operator workflow.

## Alternatives Considered

**Option B — compute diff inline in `upgrade_residual_report.py` (Stage 10)**:
Simpler integration — no new pipeline stage, no intermediate JSON artifact. Rejected
because: (a) Stage 10 runs in an EXIT trap and should consume pre-computed artifacts
rather than do analysis; (b) the JSON artifact enables future pipeline stages (e.g., a
Stage 6 extension that proactively syncs affected templates) to reference the diff without
re-parsing; (c) OPTION_A is consistent with how all other residual report sections are
sourced (from pre-computed JSON artifacts).

**Automated template sync (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`)**:
The issue proposed an optional automated sync step. Deferred — reporting scope only in
this work item. Automated sync introduces write risk to consumer-customized templates and
requires an explicit opt-in flag and rollback protocol.

## Consequences

- `scripts/lib/blueprint/upgrade_version_pin_diff.py` (new): domain functions
  `parse_versions_sh`, `diff_pins`, `scan_template_references`; orchestrator
  `run_version_pin_diff`; CLI `main` with argparse.
- `scripts/bin/blueprint/upgrade_consumer_pipeline.sh`: new Stage 1b invocation with
  `|| true` guard.
- `scripts/lib/blueprint/upgrade_residual_report.py`: new `_render_version_pin_section`
  function; new section in `generate_residual_report`.
- `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: new operator guidance step for
  reviewing the version pin diff section before running `make infra-bootstrap`.
- New artifact: `artifacts/blueprint/version_pin_diff.json` (written to existing
  gitignored `artifacts/blueprint/` directory).
- No new environment variables. No `blueprint/contract.yaml` schema changes.
  No breaking changes to existing residual report sections.
- Tests: unit tests for parse/diff/scan functions; positive-path fixture (changed pin +
  template reference → correct JSON and correct residual section); error-path fixture
  (mocked git failure → error artifact + graceful residual section).
