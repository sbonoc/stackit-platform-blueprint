# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- SPEC_READY: true — gate open.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: New module is minimal — `bash -n` subprocess + grep heuristic. No abstraction layers beyond what is needed for testability.
- Anti-abstraction gate: No new classes or registries. Gate logic is a single function returning a plain dataclass result.
- Integration-first testing gate: Test contract (AC-001 through AC-006) is defined before implementation.
- Positive-path filter/transform test gate: REQ-011 mandates positive-path fixture (all defs present → gate passes) AND negative-path fixture (dropped def → gate reports symbol). Both MUST be in test suite before merge.
- Finding-to-test translation gate: Any reproducible failure found during development MUST be captured as a failing test first. No exceptions without documentation in pr_context.md.

## Delivery Slices

### Slice 1 — Behavioral gate logic module (no upstream deps)
- **New file:** `scripts/lib/blueprint/upgrade_shell_behavioral_check.py`
- Implements:
  - `bash -n` syntax check per `.sh` file via `subprocess.run`
  - Grep/regex function-definition detection: patterns `^\s*function\s+(\w+)` and `^\s*(\w+)\s*\(\s*\)`
  - Grep/regex call-site detection: any line containing a known function name token, excluding its own definition line and comment lines (`^\s*#`)
  - Depth-1 `source`/`.` resolver: scan for `^\s*(?:source|\.)\s+(.+)` directives, resolve the path relative to the script's directory, load definitions from that file
  - Returns `ShellBehavioralCheckResult(files_checked, syntax_errors, unresolved_symbols, status, skipped)`
  - `syntax_errors`: list of `{"file": str, "error": str}`
  - `unresolved_symbols`: list of `{"file": str, "symbol": str, "line": int}`
  - `status`: `"pass"` | `"fail"` | `"skipped"`
- **Owner:** blueprint maintainer
- **Depends on:** nothing
- **Validation:** `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` (new file, see Slice 1 tests below)

### Slice 2 — Postcheck orchestrator integration (depends on Slice 1)
- **Modified file:** `scripts/lib/blueprint/upgrade_consumer_postcheck.py`
- Changes:
  - Add `--skip-behavioral-check` boolean CLI flag (default `False`)
  - After loading apply report, extract paths where `result == "merged"` and `path.endswith(".sh")`
  - Call `upgrade_shell_behavioral_check.run_behavioral_check(files, repo_root, skip=skip_behavioral_check)`
  - Append `behavioral_check` key to report payload: `{skipped, files_checked, syntax_errors, unresolved_symbols, status}`
  - Append `behavioral-check-failure` to `blocked_reasons` when `status == "fail"`
  - Add `behavioral_check_skipped` (bool) and `behavioral_check_failure_count` (int) to `summary`
  - Emit `log_warn` (print to stderr) when gate is skipped
- **Owner:** blueprint maintainer
- **Depends on:** Slice 1
- **Validation:** `pytest tests/blueprint/test_upgrade_postcheck.py` (extended, AC-001 through AC-005)

### Slice 3 — JSON schema update (depends on Slice 2)
- **Modified file:** `scripts/lib/blueprint/schemas/upgrade_postcheck.schema.json`
- Changes:
  - Add `behavioral_check` property (object, required): `{skipped: bool, files_checked: int, syntax_errors: array, unresolved_symbols: array, status: string}`
  - Add `behavioral_check_skipped` (bool) and `behavioral_check_failure_count` (int) to `summary` required fields
- **Owner:** blueprint maintainer
- **Depends on:** Slice 2
- **Validation:** existing postcheck schema tests must still pass; new test assertions verify schema with `behavioral_check` present

### Slice 4 — Shell wrapper + metrics (depends on Slice 2)
- **Modified file:** `scripts/bin/blueprint/upgrade_consumer_postcheck.sh`
- Changes:
  - Read `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` from env
  - When truthy, pass `--skip-behavioral-check` to Python module
  - Emit `log_warn "behavioral check skipped via BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK"` when skipped
  - Add `postcheck_behavioral_check_failures_total` case to `emit_postcheck_report_metrics` → `log_metric "blueprint_upgrade_postcheck_behavioral_check_failures_total" "$value"`
- **Modified file:** `scripts/lib/blueprint/upgrade_report_metrics.py`
- Changes:
  - In the `postcheck` sub-command handler, read `behavioral_check.syntax_errors` length + `behavioral_check.unresolved_symbols` length from the report and emit `postcheck_behavioral_check_failures_total=<total>`
- **Owner:** blueprint maintainer
- **Depends on:** Slice 2
- **Validation:** `pytest tests/blueprint/test_upgrade_consumer_wrapper.py` (extended, AC-006)

### Slice 5 — Blueprint docs update (depends on Slice 4)
- **Modified file(s):** `docs/blueprint/` — upgrade postcheck reference page
- Changes:
  - Document `behavioral_check` section in postcheck report
  - Document `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` opt-out flag with warning notice
  - Document failure message format (file, symbol, line)
  - Update ADR cross-reference if present in docs
- **Owner:** blueprint maintainer
- **Depends on:** Slice 4
- **Validation:** `make docs-build`, `make docs-smoke`

### Slice 6 — Hardening review + publish artifacts (depends on all)
- `make quality-hardening-review`
- `make quality-hooks-run`
- `make infra-validate`
- Fill `hardening_review.md`, `pr_context.md`, `evidence_manifest.json`
- **Depends on:** Slices 1–5

## Test File Plan

### New: `tests/blueprint/test_upgrade_shell_behavioral_check.py`
Covers Slice 1 logic in isolation (no postcheck orchestration needed):

| Test | AC | Path |
|------|----|------|
| `test_syntax_ok_all_defs_present` | AC-003 | positive-path: function defined and called in same file → status=pass |
| `test_syntax_error_detected` | AC-001 | syntax error in merged script → status=fail, syntax_errors populated |
| `test_unresolved_symbol_detected` | AC-002 | call site with no def in same file or sourced file → status=fail, unresolved_symbols populated |
| `test_sourced_file_def_resolves` | AC-003 | function defined in depth-1 sourced file → call site resolves → status=pass |
| `test_skip_flag_returns_skipped` | AC-004 | skip=True → status=skipped, no subprocess calls |
| `test_only_merged_files_checked` | REQ-001 | gate is called only for result=merged .sh files; other results ignored |

### Extended: `tests/blueprint/test_upgrade_postcheck.py`
Adds cases that exercise gate via full postcheck orchestrator:

| Test | AC |
|------|----|
| `test_behavioral_check_blocks_on_syntax_error` | AC-001, AC-005 |
| `test_behavioral_check_blocks_on_unresolved_symbol` | AC-002, AC-005 |
| `test_behavioral_check_passes_clean_merged_scripts` | AC-003 |
| `test_behavioral_check_skipped_via_flag` | AC-004 |
| `test_behavioral_check_section_present_in_report` | REQ-006 |

### Extended: `tests/blueprint/test_upgrade_consumer_wrapper.py`
Adds metric emission coverage (AC-006).

### Fixtures: `tests/blueprint/fixtures/shell_behavioral_check/`
- `clean_script.sh` — function defined and called in same file (positive-path)
- `syntax_error_script.sh` — script with intentional bash syntax error
- `missing_def_script.sh` — call site with function definition dropped (negative-path)
- `sourced_helper.sh` — defines a helper function (for depth-1 source test)
- `calls_sourced_helper.sh` — sources `sourced_helper.sh` and calls its function

## Change Strategy
- Migration/rollout sequence: Slices 1 → 2 → 3+4 (parallel) → 5 → 6.
- Backward compatibility policy: The `behavioral_check` key is additive to the postcheck JSON. The shell wrapper only passes `--skip-behavioral-check` when the env var is set; default behavior (env var absent) proceeds with gate active.
- Rollback plan: Revert this work item entirely. No schema migration, no persistent state, no consumer repo impact.

## Validation Strategy (Shift-Left)

| Layer | Command | Scope |
|-------|---------|-------|
| Unit | `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` | Gate logic module (Slice 1) |
| Unit/integration | `pytest tests/blueprint/test_upgrade_postcheck.py` | Orchestrator integration (Slice 2+3) |
| Integration | `pytest tests/blueprint/test_upgrade_consumer_wrapper.py` | Shell wrapper + metrics (Slice 4) |
| Contract/governance | `make quality-sdd-check` | SDD artifact correctness |
| Contract/governance | `make infra-validate` | Full contract validation |
| Quality | `make quality-hooks-run` | Pre-commit hook suite |
| Docs | `make docs-build && make docs-smoke` | Docs correctness (Slice 5) |
| Hardening | `make quality-hardening-review` | Repository-wide hardening (Slice 6) |

No local smoke (no HTTP routes, no K8s, no filter/transform logic in scope).

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
- Notes: This work item is confined to blueprint upgrade tooling. No app delivery paths, no new Make targets, no consumer onboarding surface affected. All listed targets are pre-existing and unaffected by this change.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/` upgrade postcheck reference — document `behavioral_check` section, `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK`, failure format
- Consumer docs updates: none (transparent to consumers; gate runs in blueprint tooling context)
- Mermaid diagrams updated: ADR diagram already created; docs page may add a flow if present
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP routes, no K8s, no filter/transform logic)
- Publish checklist:
  - include REQ-001 through REQ-011 and AC-001 through AC-006 coverage mapping
  - include key reviewer files: `upgrade_shell_behavioral_check.py`, `upgrade_consumer_postcheck.py`, schema, shell wrapper, test files
  - include pytest output as validation evidence
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `blueprint_upgrade_postcheck_behavioral_check_failures_total` metric; per-file findings in postcheck JSON; `log_warn` on skip
- Alerts/ownership: Existing postcheck CI gate already surfaces failures; new metric available for dashboards
- Runbook updates: Blueprint upgrade postcheck docs updated (Slice 5)

## Risks and Mitigations
- Risk 1: Grep heuristic generates false positives for function names that are common shell words → mitigation: require the call site to be on a non-comment, non-definition line and check that the token is an isolated word (word-boundary match).
- Risk 2: Schema change breaks existing schema-validated tests → mitigation: schema change is additive; existing required fields preserved; add `behavioral_check` as required in Slice 3 after Slice 2 tests pass.
- Risk 3: `bash` not on PATH in CI environment → mitigation: `bash -n` is already used by existing scripts in the repo; requirement on `bash` is pre-existing.
