# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Each fix is minimal and targeted — no new abstractions, no speculative generalisations.
- Anti-abstraction gate: Context D (transitive resolver) composes on top of the existing depth-1 source primitive; no new wrapper classes or interfaces introduced.
- Integration-first testing gate: Each slice writes a failing pytest fixture-based regression test before the fix, then turns it green (red→green TDD order enforced per slice).
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic introduced in this work item.
- Finding-to-test translation gate: All five defects were reproduced in consumer upgrade runs; each became a failing automated test before the fix was applied.

## Delivery Slices

### Slice 1 — Contract coverage fix (FR-001, AC-001)
**Objective:** Add 4 missing file classifications to `blueprint/contract.yaml` so `audit_source_tree_coverage` reports `uncovered_source_files_count=0`.

**Red:** Write a pytest fixture that sets up a minimal fake source tree containing `pyproject.toml`, `uv.lock`, `infra/local/helm/opensearch/values.yaml`, and `infra/local/helm/kms/values.yaml` with a contract that lacks their classifications, calls `audit_source_tree_coverage`, and asserts `uncovered_source_files_count == 0`. Confirm it fails (count = 4).

**Green:** Add entries to `blueprint/contract.yaml`:
- `pyproject.toml` → `init_managed`
- `uv.lock` → `init_managed`
- `infra/local/helm/opensearch/values.yaml` → `conditional_scaffold`
- `infra/local/helm/kms/values.yaml` → `conditional_scaffold`

Confirm the regression test passes and `make infra-validate` passes.

**Slice gate:** `uv run python3 -m pytest tests/infra/test_upgrade_contract_coverage.py -k "issue_258" -v` → PASS.

### Slice 2 — Validate target filtering (FR-002, AC-002)
**Objective:** Filter `blueprint-template-smoke` from `VALIDATION_TARGETS` when `repo_mode=generated-consumer` in `upgrade_consumer_validate.py`.

**Red:** Write a pytest fixture that creates a minimal contract with `repo_mode=generated-consumer`, calls the validate target resolution logic, and asserts `blueprint-template-smoke` is NOT in the resolved target list. Confirm it fails (target present).

**Green:** In `scripts/lib/blueprint/upgrade_consumer_validate.py`, after loading the contract, filter `VALIDATION_TARGETS` to exclude `blueprint-template-smoke` when `contract.repository.repo_mode` equals the generated-consumer mode constant. Mirror the skip logic from `quality-hooks-strict`.

**Slice gate:** `uv run python3 -m pytest tests/infra/test_upgrade_consumer_validate.py -k "issue_260" -v` → PASS.

### Slice 3 — Volatile artifact names (FR-003, AC-003)
**Objective:** Add `upgrade_validate.json` and `required_files_status.json` to `_VOLATILE_ARTIFACT_NAMES` in `upgrade_fresh_env_gate.py`.

**Red:** Write a pytest fixture that creates two fake artifact directories — one with path `/tmp/worktree-abc/`, one with `/home/user/repo/` — containing `upgrade_validate.json` files whose only content difference is the embedded absolute path, calls `compute_artifact_checksum_divergences`, and asserts the returned divergences list is empty. Confirm it fails (divergence reported).

**Green:** Add `"upgrade_validate.json"` and `"required_files_status.json"` to the `_VOLATILE_ARTIFACT_NAMES` frozenset in `scripts/lib/blueprint/upgrade_fresh_env_gate.py`.

**Slice gate:** `uv run python3 -m pytest tests/infra/test_upgrade_fresh_env_gate.py -k "issue_261" -v` → PASS.

### Slice 4 — Transitive behavioral check (FR-004, AC-004)
**Objective:** Replace depth-1 source resolution with full transitive BFS (with cycle detection) and suppress bare command tokens in `upgrade_shell_behavioral_check.py`.

**Red (part A — transitive resolution):** Write a pytest fixture that creates a three-file source chain: `entry.sh` sources `lib_a.sh`, `lib_a.sh` sources `lib_b.sh`, `lib_b.sh` defines `transitive_fn()`. Call `run_behavioral_check` on a script that uses `transitive_fn`. Assert zero behavioral failures. Confirm it fails (transitive_fn flagged as unresolved).

**Red (part B — bare command suppression):** Write a fixture that includes bare command tokens `uv` and `validate` in a script that never defines them as shell functions. Assert zero behavioral failures. Confirm it fails (tokens flagged).

**Red (part C — cycle guard):** Write a fixture where `a.sh` sources `b.sh` and `b.sh` sources `a.sh`. Assert the check completes without recursion error. Confirm it would recurse without the guard.

**Green:** In `scripts/lib/blueprint/upgrade_shell_behavioral_check.py`:
1. Introduce `_collect_defined_functions_transitive(script_path, root_dir, visited=None)` using BFS: start with the direct sources of `script_path`, for each sourced file collect its function definitions and enqueue its own source directives, skip any path already in `visited`.
2. Replace the call to `collect_defined_functions_depth1` with `_collect_defined_functions_transitive` in `run_behavioral_check`.
3. Introduce `_is_bare_command_token(token, all_defined_symbols)` that returns `True` when a token is in an allow-listed set of known external commands (`uv`, `validate`, `make`, `python3`, etc.) OR appears nowhere in the full source chain as a function definition; suppress such tokens from the unresolved report.

**Slice gate:** `uv run python3 -m pytest tests/infra/test_upgrade_shell_behavioral_check.py -k "issue_259" -v` → PASS.

## Change Strategy
- Migration/rollout sequence: the four slices are independent and MUST be delivered in order 1→2→3→4 to maintain a green test suite at each slice boundary; however, none of the four fixes depends on another at runtime.
- Backward compatibility policy: all four changes are additive or restrictive only — they remove false positives; no existing passing check becomes failing.
- Rollback plan: each slice is a single-file change (or contract YAML change); revert the relevant file to restore prior behavior with no side effects.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/ -k "issue_258 or issue_259 or issue_260 or issue_261" -v` after each slice.
- Contract checks: `make infra-validate` after Slice 1 (contract.yaml change).
- Integration checks: none required — all four fixes are deterministic Python module changes testable with fixtures.
- E2E checks: none required — covered by the existing `blueprint-upgrade-consumer` CI e2e job on reference consumer.

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
- Notes: No app delivery workflow, Make-target contract, or port-forward wrappers affected. All targets listed for gate compliance; none are modified by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none required — no new behavior or contract surface added; existing pipeline documentation remains accurate.
- Consumer docs updates: none required — the fixes are transparent to consumers.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new observability signals; existing WARNING/ERROR output in affected modules preserved.
- Alerts/ownership: none — tooling fix, no runtime service.
- Runbook updates: none required; existing upgrade runbook steps are unchanged.

## Risks and Mitigations
- Risk 1 (cycle detection correctness) → mitigation: fixture in Slice 4 part C explicitly tests the circular-source-chain case before the fix is applied; the guard is proven green before moving to Publish.
- Risk 2 (bare-command allow-list completeness) → mitigation: the allow-list is derived from the 29 confirmed false-positive tokens in issue #259; any future new token can be added to the contract's `extra_excluded_tokens` as documented escape hatch.
