# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes applicable `SDD-C-###` IDs with exception rationale for excluded controls
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated with non-placeholder values

## Implementation — Slice 1: Failing tests for pin diff logic
- [x] T-001 Write `tests/blueprint/test_upgrade_version_pin_diff.py` with failing tests for `parse_versions_sh`, `diff_pins`, `scan_template_references`, full pipeline boundary (mocked git), and git error recovery path

## Implementation — Slice 2: `upgrade_version_pin_diff.py`
- [x] T-002 Create `scripts/lib/blueprint/upgrade_version_pin_diff.py` with `parse_versions_sh`, `diff_pins`, `scan_template_references`, `run_version_pin_diff`, and `main` (argparse CLI)
- [x] T-003 Confirm all Slice 1 unit tests pass after T-002

## Implementation — Slice 3: Failing tests for residual report section
- [x] T-004 Add unit tests for the "Version Pin Changes" residual report section covering: changed pin table, new-pins subsection, removed-pins subsection, zero-changes message, and absent/malformed artifact fallback

## Implementation — Slice 4: Residual report section
- [x] T-005 Add `_render_version_pin_section(repo_root: Path) -> str` to `upgrade_residual_report.py` and wire into `generate_residual_report`
- [x] T-006 Confirm all Slice 3 unit tests pass after T-005

## Implementation — Slice 5: Pipeline wiring
- [x] T-007 Add Stage 1b invocation of `upgrade_version_pin_diff.py` in `upgrade_consumer_pipeline.sh` between Stage 1 and Stage 2; use `|| true` guard; confirm `baseline_ref` is available at that point in the script

## Implementation — Slice 6: Skill runbook
- [x] T-008 Add version pin diff review step to `.agents/skills/blueprint-consumer-upgrade/SKILL.md`

## Test Automation
- [x] T-101 All unit tests for `upgrade_version_pin_diff.py` pass: `pytest tests/blueprint/test_upgrade_version_pin_diff.py`
- [x] T-102 All unit tests for residual report version pin section pass: `pytest tests/blueprint/ -k "version_pin"`
- [x] T-103 Positive-path unit test (AC-001/AC-006): fixture with changed pin + template reference → `changed_pins` list non-empty, `template_references` contains expected path, residual report section contains the pin line and prescribed action (captures evidence in `pr_context.md`)
- [x] T-104 Error-path unit test (AC-005): mocked `subprocess.run` raises `CalledProcessError` → JSON artifact contains `error` field, `run_version_pin_diff` returns without propagating exception
- [x] T-105 No regression in existing blueprint test suite: `pytest tests/blueprint/`

## Validation and Release Readiness
- [x] T-201 Run `make quality-sdd-check` and fix all violations
- [x] T-202 Run `make infra-validate` and confirm pass
- [x] T-203 Run `make quality-hooks-run` and confirm pass
- [x] T-204 Confirm no stale TODOs, dead code, or placeholder text in touched scope
- [x] T-205 Run `make docs-build` and `make docs-smoke` and confirm pass

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (including T-103 positive-path evidence), and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
- Note: app onboarding impact is no-impact; A-001 through A-005 are pre-existing in the consumer repo and are not modified by this work item.
