# PR Context

## Summary
- Work item: 2026-04-23-issue-169-upgrade-ci-e2e-validation
- Objective: Add a dedicated `upgrade-e2e-validation` GitHub Actions job that validates the full consumer upgrade flow on every push to main, making upgrade regressions visible as a separate CI gate with JUnit XML artifact upload before any release tag is published.
- Scope boundaries: new `ci_upgrade_validate.sh`; new `quality-ci-upgrade-validate` make target in `blueprint.generated.mk` and its template source; `render_ci_workflow.py` extended to render the new CI job; `.github/workflows/ci.yml` re-rendered; structural test in `contract_refactor_scripts_cases.py`; ADR and SDD spec artifacts.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: new env var `BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR` (consumed by `ci_upgrade_validate.sh` only); new make target `quality-ci-upgrade-validate`; no consumer-facing contract changes.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/blueprint/ci_upgrade_validate.sh` — new shell script (thin pytest wrapper)
  - `scripts/lib/quality/render_ci_workflow.py` — extended with `UPGRADE_E2E_VALIDATE_LANE` and `upgrade-e2e-validation` job
  - `.github/workflows/ci.yml` — re-rendered output with new job
  - `tests/blueprint/contract_refactor_scripts_cases.py` — structural test asserting AC-001 and AC-002
- High-risk files: none — `render_ci_workflow.py` is covered by `quality-ci-check-sync` drift guard; `blueprint.generated.mk` changes are mirrored identically from the template; existing CI jobs are unchanged.

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k ci_upgrade_validate -v`, `make quality-ci-check-sync`
- Result summary: all gates green; 1 new structural test passes; shellcheck clean; CI sync check passes.
- Artifact references: `traceability.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: negligible — existing `blueprint-quality` job unchanged; new `upgrade-e2e-validation` job runs push-to-main only; no consumer-facing make targets modified.
- Rollback strategy: remove `UPGRADE_E2E_VALIDATE_LANE` and the `upgrade-e2e-validation` job from `render_ci_workflow.py`, re-render `.github/workflows/ci.yml`, remove `quality-ci-upgrade-validate` from `blueprint.generated.mk` and its template, delete `ci_upgrade_validate.sh`; no persistent state introduced.

## Deferred Proposals
- Phase 2 correctness gates (#162, #163) will extend `ci_upgrade_validate.sh` with additional pytest modules (bash-n validation, clean-worktree smoke).
- Live-tag upgrade validation (using the actual previous release tag rather than fixture snapshots) is deferred to a future item.
