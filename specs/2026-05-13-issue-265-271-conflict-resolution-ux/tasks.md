# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — RED: Triage JSON failing tests
- [x] T-001 Write `tests/infra/test_conflict_triage_issue_265.py` with 5 failing tests:
  - `test_recommended_action_blueprint_managed_root_is_take_source`
  - `test_recommended_action_blueprint_managed_catch_all_is_human_required`
  - `test_triage_excludes_contract_yaml`
  - `test_triage_entries_contain_no_file_contents`
  - `test_triage_json_schema_valid`

## Slice 2 — GREEN: Engine triage emission
- [x] T-002 Implement `_recommended_action(ownership_class: str) -> str` in `upgrade_consumer.py`
- [x] T-003 Implement `_write_upgrade_triage(...)` in `upgrade_consumer.py` (reads diff summaries from `.conflict.json` via difflib; excludes `blueprint/contract.yaml`; writes `artifacts/blueprint/upgrade_triage.json`)
- [x] T-004 Call `_write_upgrade_triage` at end of `_run_apply()` when `conflict_count > 0`
- [x] T-005 Add `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` (JSON Schema draft-07; `schema_version`, `conflicts[]` with required fields, `recommended_action` enum, `ownership_class` enum)
- [x] T-006 Confirm all Slice 1 tests GREEN

## Slice 3 — RED: Resolve script failing tests
- [x] T-007 Write `tests/infra/test_conflict_resolve_issue_265.py` with 9 failing tests:
  - `test_take_source_rows_applied_to_working_tree`
  - `test_human_required_rows_not_touched`
  - `test_upgrade_resolve_json_written`
  - `test_resolve_is_idempotent`
  - `test_resolve_exits_nonzero_if_triage_missing`
  - `test_residual_table_sorted_and_truncated_above_20`
  - `test_dry_run_makes_no_file_changes`
  - `test_accept_source_all_applies_human_required_rows`
  - `test_resolve_prints_action_per_row`

## Slice 4 — GREEN: Resolve script, make target, docs
- [x] T-008 Implement `scripts/lib/blueprint/upgrade_consumer_resolve.py`:
  - reads + validates `upgrade_triage.json` against schema
  - applies `take_source`, `take_target`, `delete` rows
  - clears resolved `.conflict.json` files
  - writes `artifacts/blueprint/upgrade_resolve.json`
  - prints residual table (sorted; >20 truncated with footer)
  - supports `--dry-run`, `--interactive` / `INTERACTIVE=true`, `--accept-source ALL`, `--accept-target ALL`
- [x] T-009 Implement `scripts/bin/blueprint/upgrade_consumer_resolve.sh` (thin wrapper; sources `bootstrap.sh`; passes flags)
- [x] T-010 Add `blueprint-upgrade-consumer-resolve` target to `blueprint.generated.mk`
- [x] T-011 Update `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — add resolve step to stage table between Stage 2 and finalize
- [x] T-012 Confirm all Slice 3 tests GREEN

## Test Automation
- [x] T-101 `test_conflict_triage_issue_265.py` — 5 tests (Slice 1 RED, Slice 2 GREEN)
- [x] T-102 `test_conflict_resolve_issue_265.py` — 9 tests (Slice 3 RED, Slice 4 GREEN)
- [x] T-103 N/A — no HTTP filter/transform routes
- [x] T-104 N/A — all tests are new regression tests derived from issue evidence; no pre-PR smoke findings to translate
- [x] T-105 Schema validation: `jsonschema` validation of `upgrade_triage.json` against `upgrade_triage.schema.json` in test suite and at resolve-script startup

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — CLI tool with no browser-rendered UI surface"
- [x] T-A02 N/A — no browser UI
- [x] T-A03 N/A — no browser UI
- [x] T-A04 N/A — no browser UI
- [x] T-A05 N/A — no browser UI

## Validation and Release Readiness
- [x] T-201 Run `make quality-hooks-fast` — shellcheck, infra-validate, infra-contract-test-fast, quality-sdd-check-all all pass
- [x] T-202 Run `uv run python3 -m pytest tests/infra/test_conflict_triage_issue_265.py tests/infra/test_conflict_resolve_issue_265.py -v` — 14/14 GREEN
- [x] T-203 Confirm no stale TODOs, dead code, or unreferenced schema fields
- [x] T-204 Run `make docs-build` and `make docs-smoke`
- [x] T-205 Run `make quality-hardening-review`

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` — N/A (no app delivery targets modified)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A (no backend app in scope)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A (no frontend in scope)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A (no app delivery impact)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A (no runtime provisioning in scope)
