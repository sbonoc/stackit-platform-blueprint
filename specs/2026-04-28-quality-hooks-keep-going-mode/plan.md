# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Single new helper file (`keep_going.sh`) with a small functional surface (`keep_going_active`, `keep_going_init`, `run_check`, `keep_going_finalize`).
  - No new make targets; recipes remain as-is and inherit the env var via the calling environment.
  - Default code path is preserved verbatim — the keep-going branch is additive guarded by `if keep_going_active`.
- Anti-abstraction gate:
  - No wrapper layer over `pre-commit`, `make`, or `run_cmd`. The helper composes with the existing `run_cmd`/`log_*`/metric primitives in `scripts/lib/shell/`.
  - No registry / plugin model; check lists live inline in each entry script as before.
- Integration-first testing gate:
  - Helper-level tests use synthetic check commands (e.g. `bash -c 'exit 0'`, `bash -c 'echo X >&2; exit 1'`) and assert on the summary block format and exit codes — no dependency on the real check suite.
  - End-to-end test exercises `bash hooks_fast.sh --keep-going` against a deliberately-broken fixture to assert the multi-failure path.
- Positive-path filter/transform test gate: not applicable (no filter/payload-transform logic in scope).
- Finding-to-test translation gate:
  - If a reproducible failure is observed during local development of this feature, it MUST be encoded as a failing automated test before the fix lands.

## Delivery Slices

1. **Slice 1 — Keep-going helper + unit contract (red→green):** Add `tests/blueprint/test_quality_hooks_keep_going.py` (or a `.bats` / `.shellspec` equivalent if shell-native testing is the existing convention; resolved during Slice 1 — see Q-2) covering: (a) `keep_going_active` reads `QUALITY_HOOKS_KEEP_GOING` correctly; (b) `run_check` records pass/fail and duration; (c) `keep_going_finalize` prints the summary block in the exact contracted format and exits 0 vs 1 by aggregate; (d) `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` controls tail length; (e) cleanup trap removes temp files. Implement `scripts/lib/shell/keep_going.sh` to make the tests pass. Bound: helper file + tests; no entry-script changes yet.

2. **Slice 2 — Gating helpers + unit contract (red→green):** Add `tests/blueprint/test_quality_gating.py` covering: (a) `quality_changed_paths` returns the union of merge-base and working-tree diffs (fixture: temp git repo with controlled history); (b) `quality_paths_match_infra_gate` matches paths under each entry of the gating set and returns false for non-matching sets; (c) `quality_spec_is_ready` returns true when `- SPEC_READY: true` is present in the target `spec.md` and false otherwise; (d) `QUALITY_HOOKS_FORCE_FULL=true` causes `quality_paths_match_infra_gate` to return true regardless of input. Implement `scripts/lib/shell/quality_gating.sh`. Bound: helper file + tests; no entry-script changes yet.

3. **Slice 3 — `hooks_fast.sh` keep-going integration (red→green):** Add `tests/blueprint/test_quality_hooks_fast_keep_going.py` that runs `bash scripts/bin/quality/hooks_fast.sh --keep-going` against a fixture tree with two known-broken independent checks (e.g. a fixture shellcheck-failing script under a temporary search root) and asserts the summary block lists both failures. Modify `hooks_fast.sh` to source `keep_going.sh`, add the `--keep-going` arg parser, run pre-commit fail-fast first (FR-004), then dispatch every downstream check via `run_check` when keep-going is active and via the existing `run_cmd` when not. Update `--help` text to mention `--keep-going` and `QUALITY_HOOKS_KEEP_GOING`. Bound: only `hooks_fast.sh` keep-going wiring (no gating yet).

4. **Slice 4 — `hooks_strict.sh` keep-going integration (red→green):** Mirror Slice 3 for `hooks_strict.sh`. Test asserts that the strict-phase summary block lists each strict check with status. Update `--help`. Bound: only `hooks_strict.sh`.

5. **Slice 5 — `hooks_run.sh` cross-phase integration (red→green):** Add `tests/blueprint/test_quality_hooks_run_keep_going.py` that `bash hooks_run.sh --keep-going` invokes both phases when pre-commit passes (even if downstream fast checks fail) and that the combined exit code reflects both phases. Modify `hooks_run.sh` to parse `--keep-going`, propagate it to both child invocations, and gate the strict-phase invocation on the fast-phase pre-commit-passed signal (introduced via an exit-code convention or a sentinel file written by `hooks_fast.sh` before downstream checks start; chosen mechanism documented in the slice). Update `--help`. Bound: only `hooks_run.sh` and the small fast-phase signal added to support it.

6. **Slice 6 — Path-gating `infra-validate` + `infra-contract-test-fast` (red→green):** Add `tests/blueprint/test_quality_hooks_fast_path_gating.py` covering AC-009 (docs/spec-only commit skips both checks), AC-010 (infra-touching commit runs both), AC-011 (`QUALITY_HOOKS_FORCE_FULL=true` forces both regardless of paths). Modify `hooks_fast.sh` to source `quality_gating.sh`, compute the changed-path set once near script start, and wrap each of `infra-validate` / `infra-contract-test-fast` in a gating dispatch that emits the skip log + metric on no-match. Update `--help` to mention `QUALITY_HOOKS_FORCE_FULL` and the gating set. Bound: only `hooks_fast.sh` + the gating helper consumption.

7. **Slice 7 — Phase-gating `quality-spec-pr-ready` (red→green):** Add `tests/blueprint/test_quality_hooks_fast_spec_ready_gating.py` covering AC-012 (`SPEC_READY: false` skips), AC-013 (`SPEC_READY: true` runs), and the `QUALITY_HOOKS_FORCE_FULL=true` override path. Modify the existing `quality-spec-pr-ready` invocation block in `hooks_fast.sh` to consult `quality_spec_is_ready` and emit the skip log + metric when not ready. Bound: the small block in `hooks_fast.sh` that today contains `if [[ "$_current_branch" =~ ^codex/...]]`.

8. **Slice 8 — Dedup `quality-docs-lint` + `quality-test-pyramid` (red→green):** Add `tests/blueprint/test_quality_hooks_fast_dedup.py` covering AC-014 (no separate `run_cmd` lines for the two checks; no double execution observed in log output). Delete the two redundant `run_cmd make ... quality-docs-lint` and `run_cmd make ... quality-test-pyramid` lines in `hooks_fast.sh`. Reframe the existing `command -v pre-commit` fallback to emit a `log_warn` directing the user to install pre-commit (FR-013). Bound: 4–6 lines in `hooks_fast.sh`.

9. **Slice 9 — Step 5 skill clarification (red→green):** Add `tests/blueprint/test_step05_skill_per_slice_gate.py` covering AC-015 (presence of normative directive that the per-slice gate is `make test-unit-all`; presence of normative statement that `quality-hooks-fast` is the slice-batch / pre-PR gate; absence of `quality-hooks-fast` references in the per-slice loop section). Edit `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` to add the directive and reframe the `Reproducible pre-commit failures` subsection. Bound: text-only edits in `SKILL.md`.

10. **Slice 10 — Documentation + ADR finalization:** Update the make-target doc-comments in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (and re-render `make/blueprint.generated.mk` via the existing render path) to mention `QUALITY_HOOKS_KEEP_GOING` and `QUALITY_HOOKS_FORCE_FULL`. Add a short section to the closest existing operations doc under `docs/blueprint/operations/` (path confirmed during this slice) describing the flag and env vars, the failure-cascade caveat, the path-gating set, the phase-gating rationale, the dedup rationale, and the recommended agent inner-loop usage. Move ADR `Status: proposed → approved` once Architecture sign-off is recorded.

## Change Strategy
- Migration/rollout sequence: ship as a single PR; no consumer-side rollout because the helper lives in blueprint-managed `scripts/lib/shell/` and the entry scripts are blueprint-owned. Generated consumers receive the change on their next blueprint upgrade.
- Backward compatibility policy: default behavior MUST be byte-identical (FR-009). Existing CI invocations, pre-commit invocations, and ad-hoc `make quality-hooks-*` calls remain fail-fast. Only consumers that pass `--keep-going` or set `QUALITY_HOOKS_KEEP_GOING=true` see the new behavior.
- Rollback plan: revert the patch. The helper file can be deleted or left in place; the entry-script `if keep_going_active` guards become dead code that does nothing without the env var. There is no state to migrate, no data to recover.

## Validation Strategy (Shift-Left)
- Unit checks: `tests/blueprint/test_quality_hooks_keep_going.py` covers the keep-going helper contract end-to-end; `tests/blueprint/test_quality_gating.py` covers the changed-path / path-gate / spec-readiness predicates against fixture trees.
- Contract checks: end-to-end tests for each entry script under `tests/blueprint/test_quality_hooks_*.py` assert the summary marker line, per-check status format, exit codes, pre-commit fail-fast invariant, cross-phase ordering in `hooks_run.sh`, path-gate skip behavior, phase-gate skip behavior, dedup compliance (no duplicate `run_cmd` lines), and `QUALITY_HOOKS_FORCE_FULL` override semantics. `tests/blueprint/test_step05_skill_per_slice_gate.py` asserts the SKILL.md content invariants from FR-014.
- Integration checks: `make quality-hooks-fast QUALITY_HOOKS_KEEP_GOING=true` and `make quality-hooks-run QUALITY_HOOKS_KEEP_GOING=true` are run locally on this repo with no deliberate breakage to confirm zero-failure path emits the `===== all checks passed =====` line and exits 0; `make quality-hooks-fast` on a docs/spec-only working tree confirms the skip metric for both infra checks; `make quality-hooks-fast QUALITY_HOOKS_FORCE_FULL=true` confirms forced execution.
- E2E checks: not required — this is local developer + agent inner-loop tooling with no production runtime path.

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
- Notes: this work item modifies developer/agent quality tooling only; it does not affect app delivery workflows, port-forwarding, or the app onboarding contract.

## Documentation Plan (Document Phase)
- Blueprint docs updates: add `--keep-going`, `QUALITY_HOOKS_KEEP_GOING`, `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES`, and `QUALITY_HOOKS_FORCE_FULL` to the closest existing operations / quality-gates doc under `docs/blueprint/operations/` (confirm exact path during Document phase); document the path-gating set, the phase-gating rationale, and the dedup rationale; cross-reference the ADR.
- Skill docs updates: `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` updated per FR-014 (per-slice gate is `make test-unit-all`; `quality-hooks-fast` is the slice-batch / pre-PR gate).
- Consumer docs updates: none required in v1; if consumer docs document the quality hooks (verify during Document phase), add a one-line mirror.
- Mermaid diagrams updated: ADR includes a flowchart of default vs keep-going dispatch and a flowchart of the gating decision tree; no other diagrams require updates.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — this work item touches no HTTP routes, query/filter logic, or API endpoints.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: keep-going mode emits `quality_hooks_keep_going_total` with `status`, `phase`, and `failed_checks` labels at script end; per-check `log_info` start lines and per-failure stderr tail re-emission are present in keep-going mode only. Default mode telemetry is unchanged.
- Alerts/ownership: none — local developer / agent tooling.
- Runbook updates: a one-paragraph note in the operations doc instructs agents and humans to fix the earliest-reported failure first and re-run, rather than mass-applying fixes for every line in the summary block.

## Risks and Mitigations
- Risk 1 (default-path regression) -> mitigation: preserve `run_cmd` lines verbatim under `if keep_going_active; then run_check ...; else run_cmd ...; fi`; add a contract test that exercises default invocation against a two-failure fixture and asserts that only the first failure is observed.
- Risk 2 (cascading false positives) -> mitigation: documentation in the operations doc and ADR makes the failure-ordering policy explicit; the summary block lists checks in execution order so the earliest failure is the first reported.
- Risk 3 (signal handling under aggregation) -> mitigation: EXIT trap composes with the existing metric trap; per-check capture files are removed even on signal-induced exit; subsequent checks do not execute after a fatal signal.
- Risk 4 (path-gating false-skip) -> mitigation: deliberately conservative gating set; CI runs the full bundle unconditionally; `QUALITY_HOOKS_FORCE_FULL=true` provides explicit override; gating set is centralized as a single newline-delimited list in `hooks_fast.sh` so additions are one-line edits; tests assert each entry of the gating set triggers the gate.
- Risk 5 (phase-gate timing) -> mitigation: the skip log + metric makes "why this was skipped" auditable; Step 7 explicitly invokes `make quality-spec-pr-ready` so the publish-gate check still runs at the right time; the `QUALITY_HOOKS_FORCE_FULL=true` override lets a user run it on demand.
- Risk 6 (dedup regression when pre-commit is missing) -> mitigation: FR-013 pre-commit-missing branch emits a `log_warn` rather than silently skipping; the operations doc documents pre-commit as a prerequisite.
- Risk 7 (skill-edit drift) -> mitigation: `tests/blueprint/test_step05_skill_per_slice_gate.py` asserts the FR-014 directive remains present in `SKILL.md`; accidental removal trips the gate.
