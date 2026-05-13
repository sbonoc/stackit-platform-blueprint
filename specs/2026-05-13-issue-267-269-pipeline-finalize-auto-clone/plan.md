# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: add exactly one new Bash script (`upgrade_consumer_finalize.sh`) and one new make target; minimize changes to the existing pipeline script to URL normalization + finalize invocation; no new abstractions.
- Anti-abstraction gate: finalize script directly invokes make targets via `$(MAKE)` or `make -C "$ROOT_DIR"`; no wrapper functions or dispatch tables; the two-pass structure is a simple sequential loop.
- Integration-first testing gate: tests exercise the make target and script boundaries (contract tests); internal sync/verify step sequencing is tested via mock make targets that simulate failure.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: both issues have deterministic pre-PR failures (Stage 5 fatal exit on URL form; `quality-hooks-run` cycle). Each is translated to a failing test in the red slice before the green implementation.

## Delivery Slices

### Slice 1 — red: failing tests for auto-clone URL normalization
Write a pytest test in `tests/infra/test_pipeline_auto_clone_issue_269.py` that:
- Asserts that calling `upgrade_version_pin_diff.py` with `upgrade_source` set to a non-directory path (simulating URL form) emits a warning and exits non-zero (current behaviour → the test documents the regression).
- Asserts that the pipeline shell function `normalize_upgrade_source` (to be implemented in Slice 2) returns a local path when given a URL-like value and a local path when given a local path (tested via a sourced-function unit test using `bats` or a subprocess mock; use a mock `git clone` that creates a tmp dir with a `.git` marker).
All tests MUST be red before proceeding to Slice 2.

### Slice 2 — green: implement auto-clone in pipeline
In `upgrade_consumer_pipeline.sh`:
- Add a `normalize_upgrade_source` block after `upgrade_source` is resolved and before Stage 1b. Block: if `! [[ -d "$upgrade_source/.git" ]]`, validate the URL prefix (allowlist: `https://`, `git@`, `ssh://`, `/`, `./`, `../`; abort on unknown prefix), then `git clone --quiet --depth 1 --branch "$upgrade_ref" "$upgrade_source" "$cloned_source_dir"` and `trap 'rm -rf "$cloned_source_dir"' EXIT`.
- Emit `[PIPELINE] cloned $upgrade_source@$upgrade_ref → $cloned_source_dir` via `log_info`.
In `scripts/lib/blueprint/upgrade_consumer.py`:
- In the `resolve_default_upgrade_source` / clone path: add a guard that skips the internal clone when `upgrade_source` is already a local `.git` directory.
All Slice 1 tests MUST turn green. Run `make infra-contract-test-fast` to confirm no regressions.

### Slice 3 — red: failing tests for finalize target
Write a pytest test in `tests/infra/test_pipeline_finalize_issue_267.py` that:
- Asserts `make blueprint-upgrade-consumer-finalize` is a registered make target (present in `make/blueprint.generated.mk`).
- Asserts that when all sync and verify mock targets succeed, finalize exits 0.
- Asserts that when a sync target fails, subsequent sync targets still run (no fail-fast) and finalize exits non-zero after all sync steps.
- Asserts that when a verify target fails, finalize exits non-zero immediately and emits a summary banner naming the failing target.
- Asserts idempotency: running finalize twice in a scenario where all steps are already converged exits 0 both times.
All tests MUST be red before proceeding to Slice 4.

### Slice 4 — green: implement finalize + pipeline integration + docs
1. Create `scripts/bin/blueprint/upgrade_consumer_finalize.sh`:
   - Usage block documenting the two-pass structure and required env vars.
   - Sync pass: `quality-docs-sync-all`, `quality-sdd-sync-consumer-init-assets`, `quality-sdd-sync-policy-snippets` — aggregated failures, no fail-fast.
   - Verify pass: `infra-validate`, `quality-hooks-run`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-postcheck`, `blueprint-upgrade-fresh-env-gate` — fail-fast with summary banner.
   - Per-step `[finalize] <step>: <status>` log lines via `log_info`/`log_error`.
2. Add `blueprint-upgrade-consumer-finalize` target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; regenerate `make/blueprint.generated.mk`.
3. In `upgrade_consumer_pipeline.sh`, replace the Stage 8 and Stage 9 blocks with a single `make -C "$ROOT_DIR" blueprint-upgrade-consumer-finalize || pipeline_exit=$?` call with appropriate log framing. Keep Stage 10 EXIT trap unchanged.
4. Update `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: replace the per-target post-apply list with the single `make blueprint-upgrade-consumer-finalize` command; update Stage 2b note to reference finalize.
5. Update pipeline usage block: document auto-clone behaviour and the finalize target.
All Slice 3 tests MUST turn green. Run `make infra-contract-test-fast` and `make quality-hooks-fast` to confirm no regressions.

## Change Strategy
- Migration/rollout sequence: purely additive for consumers — the new make target is available immediately on next blueprint upgrade; the pipeline replaces Stages 8+9 internally with no external API change; consumers who were previously running Stages 8+9 manually can switch to the single finalize target.
- Backward compatibility policy: existing `blueprint-upgrade-consumer-apply`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-postcheck`, and `blueprint-upgrade-fresh-env-gate` targets remain individually callable.
- Rollback plan: revert the two new files (`upgrade_consumer_finalize.sh`, test file) and the pipeline/template edits; no database or artifact migrations involved.

## Validation Strategy (Shift-Left)
- Unit checks: `tests/infra/test_pipeline_auto_clone_issue_269.py` — URL normalization logic (local vs. URL source detection); `tests/infra/test_pipeline_finalize_issue_267.py` — finalize two-pass structure (sync aggregation, verify fail-fast, idempotency).
- Contract checks: make target existence check in `test_pipeline_finalize_issue_267.py`; pipeline usage block presence in script header.
- Integration checks: `make infra-contract-test-fast` — full tooling contract suite must pass.
- E2E checks: `make quality-hooks-fast` — must pass after each slice.

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
- App onboarding impact: no-impact — blueprint-internal tooling scripts only; all targets above are pre-existing and unchanged by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — post-apply command updated to single finalize invocation; `upgrade_consumer_pipeline.sh` usage block — auto-clone and finalize documented.
- Consumer docs updates: none; finalize is a blueprint-managed target automatically available to all consumers via `blueprint.generated.mk`.
- Mermaid diagrams updated: architecture.md contains the URL normalization flow and the finalize two-pass flow diagrams; no separate docs/ diagrams required for this scope.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes or filter logic touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `[finalize] <step>: <status>` log lines per step; consistent with existing pipeline `[PIPELINE]` pattern; no new metrics endpoints required.
- Alerts/ownership: no new alerts; finalize exit code is the observable signal for CI consumers.
- Runbook updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated in Slice 4.

## Risks and Mitigations
- Risk 1: shallow clone may fail for tags with detached-HEAD semantics → `git clone --branch $ref` works for both branches and tags in Git; validated against both forms in the test suite.
- Risk 2: finalize's postcheck step requires `artifacts/blueprint/upgrade_apply.json` to exist → documented as a precondition in the script usage block; finalize is only meaningful after a pipeline apply run.
