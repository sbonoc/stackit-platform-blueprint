# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- SPEC_READY: true — gate open.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: New gate is a thin shell wrapper + a single Python module for JSON report serialization. No abstraction layers beyond what is needed for testability. Divergence diff is file-set comparison only.
- Anti-abstraction gate: No new classes beyond a plain dataclass for the gate result. No registries or plugin patterns.
- Integration-first testing gate: Test contract (AC-001 through AC-005) is defined before implementation. Positive-path and negative-path fixtures are created in Slice 1.
- Positive-path filter/transform test gate: Not applicable — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: Any reproducible failure found during development MUST be captured as a failing test first. No exceptions without documentation in pr_context.md.

## Delivery Slices

### Slice 1 — Python report module + test fixtures (no upstream deps)
- **New file:** `scripts/lib/blueprint/upgrade_fresh_env_gate.py`
- Implements:
  - `FreshEnvGateResult` dataclass: `status` (pass|fail|error), `worktree_path` (str), `targets_run` (list[str]), `divergences` (list[dict{file, reason}]), `error` (str|None), `exit_code` (int)
  - `write_report(result: FreshEnvGateResult, output_path: str) -> None` — serializes to JSON
  - `compute_divergences(worktree_path: str, working_tree_path: str) -> list[dict]` — diffs file sets (relative paths) between worktree and working tree after target execution
- **New test fixtures:**
  - `tests/blueprint/fixtures/fresh_env_gate/pass_state/` — snapshot of a file set that matches between worktree and working tree
  - `tests/blueprint/fixtures/fresh_env_gate/fail_state/` — snapshot with a file absent in the worktree that is present in the working tree
- **Owner:** blueprint maintainer
- **Depends on:** nothing
- **Validation:** `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` (unit tests for report module in isolation)

### Slice 2 — Shell wrapper + EXIT trap (depends on Slice 1)
- **New file:** `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`
- Implements:
  - Read `BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH` (default: `artifacts/blueprint/fresh_env_gate.json`)
  - Require `git`, `python3`, `make` on PATH
  - `git worktree add <tmpdir> HEAD` — fails hard if non-zero (status=error, exit non-zero)
  - `trap "git worktree remove --force <tmpdir>" EXIT` — registered immediately after creation
  - Run `make infra-validate` inside worktree (via `make -C <tmpdir>`)
  - Run `make blueprint-upgrade-consumer-postcheck` inside worktree (via `make -C <tmpdir>`)
  - On any target failure: call Python module to compute divergences and write report with `status=fail`
  - On success: call Python module to write report with `status=pass`
  - Emit metric: `log_metric "blueprint_upgrade_fresh_env_gate_status_total" "1" "status=<pass|fail|error>"`
  - Inline stdout progress via `log_info` / `log_error` throughout
- **Owner:** blueprint maintainer
- **Depends on:** Slice 1
- **Validation:** `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` (integration tests via subprocess mocking)

### Slice 3 — Make target + contract wiring (depends on Slice 2)
- **Modified file:** `make/blueprint.generated.mk` — add `blueprint-upgrade-fresh-env-gate` target invoking `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`
- **Modified file:** `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk` (template counterpart) — same target added
- **Modified file:** `blueprint/contract.yaml` — declare `blueprint-upgrade-fresh-env-gate` as a required make target
- **Modified file:** `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — add step 6 to command sequence: `make blueprint-upgrade-fresh-env-gate` after `make blueprint-upgrade-consumer-postcheck`
- **Owner:** blueprint maintainer
- **Depends on:** Slice 2
- **Validation:** `make infra-validate`

### Slice 4 — Blueprint docs update (depends on Slice 3)
- **Modified file(s):** `docs/blueprint/` — upgrade skill reference docs
- Documents:
  - New `blueprint-upgrade-fresh-env-gate` gate step and its position after `blueprint-upgrade-consumer-postcheck`
  - JSON artifact schema for `artifacts/blueprint/fresh_env_gate.json`
  - What a gate failure means and how to diagnose it (divergences field)
  - Metric `blueprint_upgrade_fresh_env_gate_status_total`
- **Owner:** blueprint maintainer
- **Depends on:** Slice 3
- **Validation:** `make docs-build`, `make docs-smoke`

### Slice 5 — Hardening review + publish artifacts (depends on all)
- `make quality-hardening-review`
- `make quality-hooks-run`
- `make infra-validate`
- Fill `hardening_review.md`, `pr_context.md`, `evidence_manifest.json`
- **Depends on:** Slices 1–4

## Test File Plan

### New: `tests/blueprint/test_upgrade_fresh_env_gate.py`

| Test | AC | Path |
|------|----|------|
| `test_pass_both_targets_succeed` | AC-002, AC-005 | Both targets exit 0 in worktree → status=pass, report written, worktree removed |
| `test_fail_infra_validate_nonzero` | AC-001 | `make infra-validate` exits non-zero → status=fail, divergences populated |
| `test_fail_postcheck_nonzero` | AC-001 | `make blueprint-upgrade-consumer-postcheck` exits non-zero → status=fail |
| `test_error_worktree_creation_fails` | AC-003 | `git worktree add` exits non-zero → status=error, gate exits non-zero |
| `test_exit_trap_removes_worktree_on_pass` | AC-005 | Worktree path absent from `git worktree list` after successful gate exit |
| `test_exit_trap_removes_worktree_on_fail` | AC-004 | Worktree path absent after gate failure |
| `test_json_report_schema` | FR-006, NFR-OBS-001 | Report file exists with all required fields (status, worktree_path, targets_run, divergences, error, exit_code) |
| `test_divergence_diff_on_failure` | FR-003 | Divergences list is non-empty and identifies the absent file when a target fails due to missing bootstrap file |

### Fixtures: `tests/blueprint/fixtures/fresh_env_gate/`
- `pass_state/` — matched file set snapshot for positive-path divergence diff test
- `fail_state/` — mismatched file set (absent bootstrap file) for negative-path divergence diff test

## Change Strategy
- Migration/rollout sequence: Slices 1 → 2 → 3 → 4 → 5. Slice 3 is the only step visible to consumers (new make target in template + contract.yaml).
- Backward compatibility policy: Additive only. Existing `blueprint-upgrade-consumer-postcheck` target is unchanged. The new `blueprint-upgrade-fresh-env-gate` target is appended to the end of the upgrade sequence; existing upgrade runs that stop before the new step are unaffected.
- Rollback plan: Revert this work item entirely. Remove the new make target, script, Python module, and contract.yaml entry. No persistent state, no consumer repo data migration.

## Validation Strategy (Shift-Left)

| Layer | Command | Scope |
|-------|---------|-------|
| Unit | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | Report module + shell wrapper behavior (Slices 1–2) |
| Contract/governance | `make infra-validate` | contract.yaml + make target declarations (Slice 3) |
| Contract/governance | `make quality-sdd-check` | SDD artifact correctness |
| Quality | `make quality-hooks-run` | Pre-commit hook suite |
| Docs | `make docs-build && make docs-smoke` | Docs correctness (Slice 4) |
| Hardening | `make quality-hardening-review` | Repository-wide hardening (Slice 5) |

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
- Notes: This work item is confined to blueprint upgrade tooling. No app delivery paths, no consumer onboarding surface, no port-forward wrappers affected. All listed targets are pre-existing and unaffected by this change.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/` upgrade skill reference — document new gate step, artifact schema, metric, and failure diagnostics
- Consumer docs updates: none (transparent to consumers; gate runs inside the upgrade skill before PR is opened)
- Mermaid diagrams updated: ADR diagram already present; docs page updated with gate position in upgrade flow
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP routes, no K8s, no filter/transform logic)
- Publish checklist:
  - include FR-001 through FR-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, AC-001 through AC-005 coverage mapping
  - include key reviewer files: `upgrade_fresh_env_gate.sh`, `upgrade_fresh_env_gate.py`, `make/blueprint.generated.mk`, `blueprint/contract.yaml`, `blueprint-consumer-upgrade/SKILL.md`, test file
  - include pytest output as validation evidence
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `blueprint_upgrade_fresh_env_gate_status_total{status=pass|fail|error}` metric; JSON artifact `artifacts/blueprint/fresh_env_gate.json` with all required fields; inline stdout progress via `log_info`/`log_error`
- Alerts/ownership: Upgrade skill gate failure is surfaced inline during the upgrade run; metric available for CI dashboards; owned by blueprint maintainer (sbonoc)
- Runbook updates: Blueprint upgrade skill reference docs updated in Slice 4; SKILL.md command sequence updated in Slice 3

## Risks and Mitigations
- Risk 1: Worktree overhead makes the upgrade sequence noticeably slower on large repos or slow machines → mitigation: no time budget enforced for MVP; a configurable timeout can be added as a separate follow-up if users report friction.
- Risk 2: `git worktree remove --force` in the EXIT trap fails (e.g., signal 9, NFS mount), leaving orphaned worktree metadata on disk → mitigation: `git worktree prune` cleans up orphaned metadata; no code data is lost since the worktree was created from a committed HEAD.
- Risk 3: `make -C <worktree>` requires the consumer repo's make targets to work without the working-tree's artifact files → mitigation: this is the intended behavior; any failure here is the correct CI-equivalent signal the gate is designed to surface.
