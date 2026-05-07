# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two surgical function patches; no new abstractions, no new modules.
- Anti-abstraction gate: Use `fnmatch.fnmatch` directly against pre-enumerated file lists; do not introduce a new glob-resolution utility.
- Integration-first testing gate: Write the failing regression test (reproducing the issue) first; fix the function second.
- Positive-path filter/transform test gate: AC-001 and AC-004 are positive-path assertions — a glob entry with NO matching file MUST produce no error; prune-glob matches MUST be counted as covered.
- Finding-to-test translation gate: Both issues have deterministic reproduction commands (see issue bodies); translate each into a pytest fixture before coding the fix.

## Delivery Slices

### Slice 1 (red) — Failing regression tests
- Write `test_audit_source_tree_coverage_prune_glob_coverage` in existing test suite for `upgrade_consumer.py`: set up a temp source repo with ADR files matching a prune-glob; assert `audit_source_tree_coverage` reports them as uncovered (reproduces #214).
- Write `test_validate_absent_files_directory_entry` in existing test suite for `validate_contract.py`: set up a temp consumer repo where `source_only` has a directory entry; assert `_validate_absent_files` currently returns an error (reproduces #215).
- Write `test_validate_absent_files_glob_entry_matching` and `test_validate_absent_files_glob_entry_no_match` to cover AC-003 and AC-004.
- All new tests MUST fail before the fix is applied.

### Slice 2 (green) — Implementation fixes
1. `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage`: after building `all_coverage_roots`, resolve each glob in the `source_artifact_prune_globs_on_init` parameter against `candidate_rels` using `fnmatch.fnmatch`; add all matching paths to `all_coverage_roots`. Caller site (`_protected_roots` / plan step) MUST pass the prune-glob list to the function.
2. `scripts/bin/blueprint/validate_contract.py::_validate_absent_files`: classify entries — glob/prefix entries (contain `*` or end with `/`) use `fnmatch` against consumer file list; path entries use `is_file()` instead of `exists()`. Return errors for matched files (glob case) or present files (file case).
3. Confirm all 5 regression tests pass green.

### Slice 3 — Docs and quality
- Update `docs/blueprint/consumer/contract_reference.md` (if it documents `source_only` behavior) to note directory-prefix and glob support.
- Run `make quality-sdd-check`, `make quality-hooks-run`, `make infra-validate`.

## Change Strategy
- Migration/rollout sequence: no migration needed; changes are pure defect fixes with backward-compatible behavior.
- Backward compatibility policy: exact-file `source_only` entries behave identically; glob/directory entries become valid (were previously errors or false positives).
- Rollback plan: revert the PR; consumers re-apply their per-ADR `source_only` workarounds.

## Validation Strategy (Shift-Left)
- Unit checks: pytest tests for `_validate_absent_files` (file, directory, glob, no-match cases) and `audit_source_tree_coverage` (prune-glob-as-covered, exact-match-uncovered).
- Contract checks: `make quality-contract-test-fast` or `make infra-validate` in a synthetic consumer.
- Integration checks: none required (function-level tests are sufficient; no service boundary crossed).
- E2E checks: `make blueprint-template-smoke` to confirm no regression in the smoke scenario.

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
- App onboarding impact: no-impact — changes are confined to Python tooling scripts with no effect on app delivery Make targets or runtime infrastructure.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/consumer/contract_reference.md` — document that `source_only` now accepts directory-prefix (trailing `/`) and glob (`*`) entries.
- Consumer docs updates: none (behavior improvement only; consumers with existing per-file workarounds will continue to work).
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP routes or API endpoints.
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-004, AC-001–AC-005)
  - include key reviewer files (`scripts/lib/blueprint/upgrade_consumer.py`, `scripts/bin/blueprint/validate_contract.py`, test files)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: stderr WARNING output in `audit_source_tree_coverage` is preserved for genuinely uncovered files.
- Alerts/ownership: none (CLI tooling).
- Runbook updates: none.

## Risks and Mitigations
- Risk 1 (`fnmatch` vs shell glob semantics): `fnmatch` does not support `**` recursive patterns. The existing prune-glob `docs/blueprint/architecture/decisions/ADR-*.md` uses only `*` and is fully supported. Mitigation: document that `**` is not supported in prune-globs; add a validator warning if `**` appears.
