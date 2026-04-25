# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: each fix is a minimal, targeted correction to an existing function; no new abstractions beyond what the bug fix requires
- Anti-abstraction gate: all corrections use direct Python/bash primitives (frozenset extension, regex guards, checksum comparison, permissions string insertion); no wrapper layers
- Integration-first testing gate: each fix starts with a failing regression test that exercises the exact bug scenario, then turns green with the implementation
- Positive-path filter/transform test gate: not applicable — no filter/payload-transform routes in this work item
- Finding-to-test translation gate: each bug has a documented reproduction path; every reproduction scenario captured as a failing test before the fix is applied

## Delivery Slices

### Slice 1 — #180: Fix behavioral_check false positives (case-label | alternation + array literals)
1. Add failing unit tests in `tests/blueprint/test_upgrade_shell_behavioral_check.py`:
   - Case-label `|` alternation produces zero unresolved_symbols entries.
   - Multi-line array initializer bare-words produce zero unresolved_symbols entries.
2. Implement fix in `scripts/lib/blueprint/upgrade_shell_behavioral_check.py`:
   - Extend `_find_unresolved_call_sites` to skip tokens when `rest_lstripped.startswith("|")`.
   - Add `array_depth` tracking with `_ARRAY_OPEN_RE` pattern; skip lines inside array blocks.
3. Verify all existing behavioral_check tests still pass.

### Slice 2 — #181: Extend _EXCLUDED_TOKENS
1. Add failing unit tests in `tests/blueprint/test_upgrade_shell_behavioral_check.py`:
   - Shell file calling `tar` produces zero unresolved_symbols.
   - Shell file calling `pnpm` produces zero unresolved_symbols.
   - Shell file calling each of the thirteen blueprint runtime functions listed in FR-008 produces zero unresolved_symbols.
2. Extend `_EXCLUDED_TOKENS` in `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` with all fourteen tokens.
3. Verify no regression in existing exclusion tests.

### Slice 3 — #179: Fix reconcile_report conflict state tracking
1. Add failing unit tests in `tests/blueprint/test_upgrade_reconcile_report.py` (new file):
   - Auto-merged file (apply result == `merged`) is NOT in conflicts_unresolved.
   - Manually resolved file (conflict in plan/apply, no markers in tree) is NOT in conflicts_unresolved.
   - Same file path from plan entry and apply result is counted only once.
   - File with active markers IS in conflicts_unresolved.
2. Implement fix in `scripts/lib/blueprint/upgrade_reconcile_report.py`:
   - Add `find_merge_markers(repo_root)` function that scans working tree for active `<<<<<<<` markers.
   - Compute `resolved_conflict_paths` (auto-merged + manually cleared) and pass into classify functions.
   - Filter `conflicts_unresolved` to only paths still in `current_marker_paths`.
3. Verify postcheck unblocks when all markers are cleared.

### Slice 4 — #185: Add upgrade planner source tree completeness audit
1. Add failing unit tests in `tests/blueprint/test_upgrade_consumer.py`:
   - Blueprint source file not in required_files or managed_roots triggers WARNING and sets uncovered_source_files_count > 0.
   - Validate gate fails when uncovered_source_files_count > 0.
   - Blueprint source file added to required_files clears the warning.
2. Implement fix in `scripts/lib/blueprint/upgrade_consumer.py`:
   - After `_collect_candidate_paths` returns `source_files`, collect all files in blueprint source tree (excluding source_only paths).
   - Compute `uncovered = all_source_files - source_files`.
   - Emit `WARNING` to stderr for each uncovered file.
   - Record `uncovered_source_files_count` in plan report JSON.
3. Implement validate gate enforcement of `uncovered_source_files_count == 0` in `scripts/lib/blueprint/upgrade_consumer_validate.py` (or existing validate logic).
4. Run the audit against the current blueprint source tree; add any newly discovered uncovered files to `required_files` or `source_only` in `blueprint/contract.yaml` as part of this slice.

### Slice 5 — #186: Implement fresh_env_gate file-state divergence detection
1. Add failing unit tests in `tests/blueprint/test_upgrade_fresh_env_gate.py`:
   - Gate fails when make target produces different output file checksums in clean worktree vs working tree (both exit 0).
   - Gate passes when output files match.
   - `fresh_env_gate.json` divergences array is populated with path + checksum entries on mismatch.
2. Implement fix in `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`:
   - After both make targets complete, collect MD5/SHA256 checksums of all files under `artifacts/blueprint/` in both the clean worktree and working tree.
   - Compare checksums; emit divergence entries.
   - Update `_write_report` call to include divergences list.
   - Set `gate_exit_code=1` when divergences are non-empty.
3. Verify gate passes on a clean run (no divergences).

### Slice 6 — #187: Add permissions block to generated ci.yml
1. Add failing unit test in `tests/blueprint/test_quality_contracts.py` (or new dedicated test):
   - Generated `ci.yml` from `_render_ci` contains `permissions:` block with `contents: read`.
   - Permissions block appears after `on:` block and before `jobs:`.
2. Implement fix in `scripts/lib/quality/render_ci_workflow.py`:
   - Add `"permissions:\n  contents: read\n\n"` to `_render_ci` output after the `on:` trigger block.
3. Audit each job in the generated workflow for any step that requires additional scopes; add explicit per-job grants if needed.

## Change Strategy
- Migration/rollout sequence: fixes ship together in one PR. Consumer repos regenerate `ci.yml` on next upgrade run to receive the permissions block. No coordinated deployment required.
- Backward compatibility policy: all changes are additive corrections or string additions; no existing caller interface changes. The two JSON artifact schema extensions (`divergences` array, `uncovered_source_files_count` field) are additive.
- Rollback plan: `git revert <merge-commit>` on the blueprint main branch. Consumer repos that have already regenerated `ci.yml` would need a follow-up upgrade run to revert the permissions block, but the permissions block is benign/beneficial, so revert is unlikely.

## Validation Strategy (Shift-Left)
- Unit checks: pytest regression tests for each of the six bug scenarios (Slices 1–6 above). All tests pass before implementation PR is opened.
- Contract checks: `make quality-hooks-fast` passes; `make quality-sdd-check` passes.
- Integration checks: `make infra-contract-test-fast` passes (confirms no regressions in contract validation paths).
- E2E checks: `make blueprint-upgrade-ci-e2e-validate` (or equivalent e2e job from #169) exercises the corrected gate chain in a clean environment.

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
- Notes: no app delivery, bootstrap, or port-forward targets are affected by this work item; all listed targets are pre-existing and unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/` — update upgrade flow documentation to reflect corrected gate behavior (fresh-env divergence check, planner completeness audit); update CI template documentation to note permissions block.
- Consumer docs updates: none (no consumer-facing interface changes).
- Mermaid diagrams updated: ADR diagram (already authored in architecture.md).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or filter logic.
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-016, NFR-*, AC-001–AC-009)
  - include key reviewer files (six affected source files + five test files)
  - include validation evidence (`make quality-hooks-fast` + pytest suite pass counts)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: no new telemetry; existing gate artifact JSON files gain structured fields.
- Alerts/ownership: no new alerts; the upgrade CI e2e job (#169) will catch regressions automatically on future releases.
- Runbook updates: blueprint upgrade runbook — add note that `fresh_env_gate.json` now includes `divergences` array and that `uncovered_source_files_count > 0` is a hard gate failure.

## Risks and Mitigations
- Risk 1: Completeness audit (Slice 4) may discover currently uncovered blueprint source files → gate fails immediately after deploy. Mitigation: run audit as part of this work item and resolve all coverage gaps before merging.
- Risk 2: Divergence detection in fresh_env_gate (Slice 5) may flag timestamp-embedded or non-deterministic artifacts → false gate failures. Mitigation: scope the comparison to the stable output paths under `artifacts/blueprint/`; exclude known-nondeterministic fields if necessary.
