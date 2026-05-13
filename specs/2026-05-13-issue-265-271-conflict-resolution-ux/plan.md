# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - `_write_upgrade_triage` is a single function added to the existing engine; no new module for triage emission.
  - `upgrade_consumer_resolve.py` is a self-contained script following the pattern of existing upgrade scripts.
- Anti-abstraction gate:
  - No new base class or plugin system. `recommended_action` is computed by a plain dict mapping from `ownership_class`. The residual table is a formatted print loop.
- Integration-first testing gate:
  - Tests assert on real artifact output (triage JSON content and working-tree file state), not mock return values.
- Positive-path filter/transform test gate:
  - N/A — no HTTP filter/transform routes in scope.
- Finding-to-test translation gate:
  - No pre-existing smoke or curl findings; all tests are new regression tests derived from issue evidence.

## Delivery Slices

### Slice 1 (RED) — Failing tests: triage JSON schema and content
Write `tests/infra/test_conflict_triage_issue_265.py` with 5 tests that FAIL against current code (import of `_recommended_action` and `_write_upgrade_triage` fails; triage JSON does not exist):
- `test_recommended_action_blueprint_managed_root_is_take_source`: import `_recommended_action`; assert `_recommended_action("blueprint-managed-root") == "take_source"`.
- `test_recommended_action_blueprint_managed_catch_all_is_human_required`: assert `_recommended_action("blueprint-managed") == "human_required"`.
- `test_triage_excludes_contract_yaml`: simulate triage emission via `_write_upgrade_triage`; assert `blueprint/contract.yaml` is not present in triage entries.
- `test_triage_entries_contain_no_file_contents`: assert triage entries lack `source_content`, `target_content`, `baseline_content` keys.
- `test_triage_json_schema_valid`: assert emitted JSON validates against `upgrade_triage.schema.json`.

### Slice 2 (GREEN) — Engine triage emission
Implement in `upgrade_consumer.py`:
- New helper `_recommended_action(ownership_class: str) -> str` — deterministic dict lookup per FR-003 mapping table.
- New function `_write_upgrade_triage(repo_root, conflict_results, entries, source_ref, baseline_ref)` — builds triage manifest, reads diff summaries from `.conflict.json` files using `difflib`, excludes `blueprint/contract.yaml`, writes `artifacts/blueprint/upgrade_triage.json`.
- Call `_write_upgrade_triage` at the end of `_run_apply()` when `conflict_count > 0`.
- Add `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` (JSON Schema draft-07, versioned).

All Slice 1 tests now pass.

### Slice 3 (RED) — Failing tests: resolve script behaviour
Write `tests/infra/test_conflict_resolve_issue_265.py` with tests that FAIL against current code:
- `test_take_source_rows_applied_to_working_tree`: assert that after calling the resolve function on a triage with a `take_source` entry, the working-tree file contains the source content.
- `test_human_required_rows_not_touched`: assert that `human_required` entries leave the working-tree file unchanged.
- `test_upgrade_resolve_json_written`: assert `artifacts/blueprint/upgrade_resolve.json` exists and lists applied actions.
- `test_resolve_is_idempotent`: run resolve twice; assert second run produces no changes and exits 0.
- `test_resolve_exits_nonzero_if_triage_missing`: assert non-zero exit when triage JSON is absent.
- `test_residual_table_sorted_and_truncated_above_20`: assert >20 `human_required` rows produce a truncation footer.
- `test_dry_run_makes_no_file_changes`: assert `--dry-run` flag produces no working-tree writes and no `.conflict.json` deletions (FR-012).
- `test_accept_source_all_applies_human_required_rows`: assert `--accept-source ALL` applies all `human_required` rows with source content without prompting (FR-011).
- `test_resolve_prints_action_per_row`: assert stdout contains one `upgrade-resolve: <action> <path>` line per applied row (NFR-OBS-001).

### Slice 4 (GREEN) — Resolve script, make target, docs
Implement:
- `scripts/lib/blueprint/upgrade_consumer_resolve.py` — reads/validates triage JSON, applies actions, writes resolve JSON, prints residual table; supports `--dry-run`, `--interactive`, `--accept-source`, `--accept-target`.
- `scripts/bin/blueprint/upgrade_consumer_resolve.sh` — thin shell wrapper; passes env/flags; `source bootstrap.sh`.
- `blueprint.generated.mk` — new `blueprint-upgrade-consumer-resolve` target.
- `blueprint-consumer-upgrade/SKILL.md` — add resolve step between apply (Stage 2) and finalize in the Stage table.

All Slice 3 tests now pass.

## Change Strategy
- Migration/rollout sequence: triage emission (Slice 2) is purely additive — no existing behaviour changes, no artifact removed. Resolve script (Slice 4) is a new optional target; no existing consumer workflow is broken.
- Backward compatibility policy: `upgrade_triage.json` is a new artifact; consumers without the resolve target are unaffected. `.conflict.json` files continue to be written exactly as before; triage supplements them.
- Rollback plan: remove `_write_upgrade_triage` call and function from `upgrade_consumer.py`; delete `upgrade_consumer_resolve.py`, `upgrade_consumer_resolve.sh`, `upgrade_triage.schema.json`; remove `blueprint-upgrade-consumer-resolve` from `blueprint.generated.mk`. No state migration required.

## Validation Strategy (Shift-Left)
- Unit checks: `tests/infra/test_conflict_triage_issue_265.py` (5 tests — triage content and schema) and `tests/infra/test_conflict_resolve_issue_265.py` (9 tests — resolve behaviour).
- Contract checks: `jsonschema` validation of `upgrade_triage.json` against `upgrade_triage.schema.json` in test suite and at resolve-script startup.
- Integration checks: `make quality-hooks-fast` (shellcheck on new `.sh`, infra-validate, infra-contract-test-fast, quality-sdd-check-all).
- E2E checks: not required; pipeline e2e is covered by issue #169 CI job; resolve target operates on artifact files only.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: pure blueprint tooling scripts; no app delivery targets added or modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `blueprint-consumer-upgrade/SKILL.md` — resolve step added to stage table between Stage 2 and finalize.
- Consumer docs updates: `upgrade_consumer_pipeline.sh` usage block comment updated to reference resolve step.
- Mermaid diagrams updated: architecture.md flowchart above.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes changed.
- Publish checklist:
  - include FR-001 through FR-012 and AC-001 through AC-010 coverage
  - include key reviewer files: `upgrade_consumer.py` (`_write_upgrade_triage`), `upgrade_consumer_resolve.py`, `blueprint.generated.mk`
  - include test evidence (test file names, pass counts)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `upgrade-resolve: <action> <path>` stdout per applied row; `upgrade_resolve.json` machine audit trail.
- Alerts/ownership: not applicable (offline tooling).
- Runbook updates: `blueprint-consumer-upgrade/SKILL.md` updated in Slice 4.

## Risks and Mitigations
- Risk 1 — `.conflict.json` path encoding: conflict artifact paths use `display_repo_path` which may produce relative paths; triage must resolve against `repo_root` consistently → mitigation: always join with `repo_root` when reading `.conflict.json` in triage emission.
- Risk 2 — Large `source_content` in `.conflict.json`: reading all `.conflict.json` files at triage time for diff summaries may be slow for 88+ files → mitigation: use `difflib.unified_diff` with `n=0` (no context lines) and summarise as "+N -M lines"; content is never stored in triage.
