# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

> **BLOCKED_MISSING_INPUTS** — 4 open questions (Q-1 through Q-4) must be resolved before slices can be finalised. Slice boundaries below are provisional and will be updated once Q-1 (apply_phase model) is confirmed.

## Delivery Slices (provisional, pending Q-1/Q-2 resolution)

### Slice 1 — Schema + engine skeleton (red → green)
**Goal:** Define `manifest.yaml` schema, implement `upgrade_workarounds.py` engine with load/evaluate/dispatch/write; unit tests for each public function.

Failing tests first:
- `test_load_manifest_returns_entries_for_target_version`
- `test_evaluate_applies_when_always_returns_true`
- `test_evaluate_applies_when_repo_mode_match`
- `test_evaluate_applies_when_repo_mode_mismatch_returns_false`
- `test_idempotency_check_skips_already_applied_entry`
- `test_should_revert_true_when_landed_in_satisfied_and_previously_applied`
- `test_should_revert_false_when_landed_in_null`
- `test_should_revert_false_when_not_previously_applied`

Files:
- `scripts/lib/blueprint/upgrade_workarounds.py` (new)
- `tests/blueprint/test_upgrade_workarounds.py` (new)

Gate: `make blueprint-test-unit` green.

### Slice 2 — `contract_merge` action kind (red → green)
**Goal:** Implement `contract_merge` apply and revert. Synthetic test: YAML fragment merged into `blueprint/contract.yaml`, applied artefact written, revert removes fragment cleanly.

Failing tests first:
- `test_contract_merge_apply_adds_yaml_entries`
- `test_contract_merge_apply_is_idempotent`
- `test_contract_merge_revert_removes_yaml_entries`
- `test_contract_merge_revert_is_noop_when_entries_absent`

Files:
- `scripts/lib/blueprint/upgrade_workarounds.py` (extend)
- `tests/blueprint/test_upgrade_workarounds.py` (extend)
- `tests/blueprint/fixtures/workarounds/` (new fixture directory)

Gate: `make blueprint-test-unit` green.

### Slice 3 — `patch` action kind (red → green, pending Q-1)
**Goal:** Implement `patch` apply (`git apply`) and revert (`git apply -R`). Introduce `apply_phase` field; split engine into `run_before_apply()` and `run_after_apply()` entry points.

Failing tests first:
- `test_patch_apply_applies_unified_diff`
- `test_patch_apply_is_idempotent`
- `test_patch_revert_reverses_unified_diff`
- `test_apply_phase_before_apply_filters_correctly`
- `test_apply_phase_after_apply_filters_correctly`

Files:
- `scripts/lib/blueprint/upgrade_workarounds.py` (extend)
- `tests/blueprint/test_upgrade_workarounds.py` (extend)
- `tests/blueprint/fixtures/workarounds/` (patch fixture)

Gate: `make blueprint-test-unit` green.

### Slice 4 — `python_script` action kind (red → green, pending Q-3)
**Goal:** Implement `python_script` dispatch — load module from `action_path`, call `apply()` / `revert()`. Apply security isolation per NFR-SEC-001.

Failing tests first:
- `test_python_script_apply_calls_apply_entrypoint`
- `test_python_script_revert_calls_revert_entrypoint`
- `test_python_script_isolation_env_allowlist`

Files:
- `scripts/lib/blueprint/upgrade_workarounds.py` (extend)
- `tests/blueprint/test_upgrade_workarounds.py` (extend)
- `tests/blueprint/fixtures/workarounds/` (stub script fixture)

Gate: `make blueprint-test-unit` green.

### Slice 5 — Pipeline Stage 1c + Stage 2c wiring
**Goal:** Add Stage 1c (before Stage 2) and Stage 2c (after Stage 2, conditional on `apply_phase: after_apply` entries existing) to `upgrade_consumer_pipeline.sh`. Log format per FR-004 / FR-007.

Files:
- `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (extend)
- `tests/blueprint/test_upgrade_pipeline.py` (extend: assert Stage 1c log presence)

Gate: `make blueprint-test-unit` green. Run pipeline smoke in local consumer clone.

### Slice 6 — Initial v1.10.0 catalogue entries (#258, #259, #260, #261)
**Goal:** Author and ship the 4 known v1.10.0 workaround entries (manifest + action files). `landed_in` values set per Q-4 resolution.

Files:
- `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` (new)
- `.agents/skills/blueprint-consumer-upgrade/workarounds/v1.10.0/` (new directory + 4 action files)

Gate: `make quality-hooks-fast` green. Manual smoke: run Stage 1c in isolation against a v1.10.0 consumer clone.

### Slice 7 — Documentation + skill update
**Goal:** Update `SKILL.md` with catalogue section (how to author a new entry, how to mark `landed_in`). Create ADR.

Files:
- `.agents/skills/blueprint-consumer-upgrade/SKILL.md` (extend)
- `docs/blueprint/architecture/decisions/ADR-issue-268-consumer-workarounds-catalogue.md` (finalise)

Gate: `make quality-docs-lint` green.

### Slice 8 — Publish artefacts
**Goal:** Complete `hardening_review.md`, `pr_context.md`, `traceability.md` validation summary, `tasks.md`.

Gate: `make quality-hooks-run QUALITY_HOOKS_FORCE_FULL=true` green.

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
- Notes: upgrade pipeline tooling only; no app delivery workflow targets are affected by this work item
