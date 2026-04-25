# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Pre-flight validation helper (Stage 1)
- [x] T-001 Write `scripts/lib/blueprint/upgrade_preflight.py` with pre-flight logic (FR-001: dirty-tree abort, FR-002: unresolved-ref abort, FR-003: bad-contract abort); write stub `scripts/bin/blueprint/upgrade_consumer.sh` that calls the helper
- [x] T-002 Add unit tests for each pre-flight abort condition in `tests/blueprint/test_upgrade_pipeline.py` using pytest (no bash test runner required)

## Implementation — Slice 2: Contract resolver (Stage 3)
- [x] T-003 Write `scripts/lib/blueprint/resolve_contract_upgrade.py` implementing FR-005 (preserve identity), FR-006 (merge required_files), FR-007 (drop prune globs), FR-008 (emit decision JSON)
- [x] T-004 Write fixture conflict JSON files for resolver unit tests in `tests/blueprint/fixtures/contract_resolver/`
- [x] T-005 Add unit tests for contract resolver: identity preservation (AC-002), required_files merge, prune glob drop, decision JSON contents

## Implementation — Slice 3: Coverage gap detection and file fetch (Stage 5)
- [x] T-006 Write `scripts/lib/blueprint/upgrade_coverage_fetch.py` implementing FR-009 (compare contract refs vs disk) and FR-010 (fetch via local git; no HTTP)
- [x] T-007 Write fixture minimal consumer directory and source repo for coverage gap tests
- [x] T-008 Add unit tests for coverage gap detection and file fetch; assert no HTTP subprocess calls (NFR-SEC-001); AC-003 satisfied

## Implementation — Slice 4: Bootstrap template mirror sync (Stage 6)
- [x] T-009 Write `scripts/lib/blueprint/upgrade_mirror_sync.py` implementing FR-011
- [x] T-010 Add unit tests: mirror overwritten when modified workspace path has mirror; no-op when mirror absent

## Implementation — Slice 5: Make target validation for new/changed docs (Stage 7)
- [x] T-011 Write `scripts/lib/blueprint/upgrade_doc_target_check.py` implementing FR-012 (scan markdown, verify .PHONY, emit warnings, no abort)
- [x] T-012 Add unit tests: known target not warned, missing target warned, stage exits 0 regardless

## Implementation — Slice 6: Residual report (Stage 10)
- [x] T-013 Write `scripts/lib/blueprint/upgrade_residual_report.py` implementing FR-015–FR-018
- [x] T-014 Add unit tests: every output item has a prescribed action; consumer-owned files listed (FR-017); pyramid gaps listed (FR-018); dropped required_files listed (FR-016); dropped prune globs listed (FR-016)
- [x] T-015 Verify existing individual targets remain independently callable without modification (FR-019)

## Implementation — Slice 7: Pipeline wiring + Makefile target
- [x] T-016 Complete `scripts/bin/blueprint/upgrade_consumer.sh`: wire all 10 stages; emit stage-labeled progress lines (NFR-OBS-001); guarantee Stage 10 even on partial failure; propagate `BLUEPRINT_UPGRADE_ALLOW_DELETE` (FR-004)
- [x] T-017 Add `blueprint-upgrade-consumer` target to `make/blueprint.mk` with `make help` entry; document `BLUEPRINT_UPGRADE_ALLOW_DELETE` env var
- [x] T-018 Update `.agents/skills/blueprint-consumer-upgrade/SKILL.md` to 6-step flow
- [x] T-019 Add idempotency test: run pipeline twice on clean fixture, assert no changes and exit 0 on second run (NFR-REL-001)
- [x] T-020 Verify no consumer-specific logic (name, module list, skill directory names) in pipeline scripts (NFR-OPS-001)

## Implementation — Slice 8: Docs sync + validation
- [x] T-021 Run `make quality-docs-sync-generated-reference` and verify generated reference docs are current
- [x] T-022 Update `references/manual_merge_checklist.md` to reference new residual report format
- [x] T-023 Update ADR status from `proposed` to `accepted` after sign-offs

## Test Automation
- [x] T-101 Add or update unit tests covering FR-001–FR-019 (all stages) in `tests/blueprint/test_upgrade_pipeline.py`
- [x] T-102 No new contract tests required (no HTTP API or event contracts)
- [x] T-103 Not applicable — no filter/payload-transform HTTP route changes
- [x] T-104 Translate each observed failure mode (F-001–F-010) addressed by a new script stage into a failing test first, then implement the fix (finding-to-test translation gate)
- [x] T-105 Add integration test for coverage gap detection + file fetch against minimal fixture source repo (AC-003)

## Validation and Release Readiness
- [x] T-201 Run `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py` — all new tests pass
- [x] T-202 Run `python3 -m pytest tests/blueprint/test_upgrade_consumer.py tests/blueprint/test_upgrade_consumer_wrapper.py tests/blueprint/test_upgrade_preflight.py tests/blueprint/test_upgrade_postcheck.py` — no regressions (AC-006)
- [x] T-203 Run `make quality-hooks-fast` — passes
- [x] T-204 Run `make docs-build` and `make docs-smoke` — passes
- [x] T-205 Run `make quality-hardening-review` — passes
- [x] T-206 Run `make infra-contract-test-fast` — passes

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (pytest output, make quality-hooks-fast), and rollback notes (additive; rollback = remove new target + scripts)
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` remain available for affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) remain available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) remain available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) remain available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) remain available
