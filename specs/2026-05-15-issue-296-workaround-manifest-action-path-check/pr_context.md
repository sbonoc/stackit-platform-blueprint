# PR Context

## Summary
- Work item: 2026-05-15-issue-296-workaround-manifest-action-path-check
- Objective: Add `quality-workaround-manifest-check` CI gate to validate all `action_path` entries in the workaround catalogue manifest resolve to existing files. Blueprint maintainers now get a fast-gate failure at commit time rather than a silent error at consumer upgrade time.
- Scope boundaries: Checker script, Make target, hooks_fast.sh wiring, pytest coverage. No runtime service changes; no changes to existing quality checks.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-PERF-001, NFR-MAINT-001, NFR-ADDITIVE-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- Contract surfaces changed: `quality-workaround-manifest-check` added to `make/blueprint.generated.mk` and `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; wired into `quality-hooks-fast`

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_workaround_manifest.py` — checker implementation
  - `tests/blueprint/test_workaround_manifest_check.py` — pytest coverage
  - `make/blueprint.generated.mk` — Make target + .PHONY registration
  - `scripts/bin/quality/hooks_fast.sh` — unconditional run_check wiring
- High-risk files: `scripts/bin/quality/hooks_fast.sh` (existing checks must remain unaltered — NFR-ADDITIVE-001)

## Validation Evidence
- Required commands executed: `uv run pytest tests/blueprint/test_workaround_manifest_check.py -v`, `make quality-workaround-manifest-check`, `make quality-hooks-fast`
- Result summary: 6 pytest tests pass; `make quality-workaround-manifest-check` exits 0; `quality-workaround-manifest-check PASS` confirmed in `quality-hooks-fast` summary
- Artifact references: `evidence_manifest.json`, `traceability.md`

## Risk and Rollback
- Main risks: None identified — checker is read-only (file existence checks only), standalone script with no shared state, and the fast gate already runs as keep-going so a new FAIL does not block other checks.
- Rollback strategy: Remove the `run_check` line from `hooks_fast.sh` and the Make target from `blueprint.generated.mk` to disable the gate without touching any other quality check.

## Deferred Proposals
- None.
