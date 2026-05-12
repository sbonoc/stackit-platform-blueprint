# Tasks

## Pre-Implementation Gate
- [x] SPEC_READY: true — spec approved; implementation slices complete.

## Slice 1 — Failing tests for #263 [RED] ✓
- [x] Write `tests/infra/test_upgrade_baseline_issue_263.py` with 4 failing tests.
- [x] Confirm `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → 4 FAIL.

## Slice 2 — Fix #263: last_applied_version baseline resolution [GREEN] ✓
- [x] `contract_schema.py`: add `last_applied_version: str = ""` to `TemplateBootstrapContract`; parse from contract YAML.
- [x] `upgrade_consumer.py`: update `_resolve_baseline_ref` signature + logic to prefer `last_applied_version`.
- [x] `upgrade_version_pin_diff.py`: apply same `last_applied_version` preference to its `_resolve_baseline_ref`.
- [x] `upgrade_consumer_postcheck.py`: write `last_applied_version` to `blueprint/contract.yaml` on postcheck success.
- [x] `blueprint/contract.yaml`: add `last_applied_version: ""` under `template_bootstrap`.
- [x] Gate: `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → 4 GREEN.
- [x] Gate: `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` → no regressions.
- [x] Gate: `make quality-hooks-fast`.

## Slice 3 — Failing tests for #264 + #266 [RED] ✓
- [x] Write `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py` with 5 failing tests (including `test_engine_exits_nonzero_on_merge_markers` for AC-005).
- [x] Confirm gate: 4 RED, 1 stable GREEN (`test_engine_exits_nonzero_on_merge_markers` — regression guard).

## Slice 4 — Fix #264 + #266: exit code disambiguation + APPLY default [GREEN] ✓
- [x] `upgrade_consumer.py`: set `status = "conflicts"` and `return 0` when apply has conflicts (not merge markers).
- [x] `upgrade_apply.schema.json`: add `"conflicts"` to `status` enum.
- [x] `upgrade_consumer_pipeline.sh`: add `set_default_env BLUEPRINT_UPGRADE_APPLY true`.
- [x] `upgrade_consumer_pipeline.sh`: propagate `BLUEPRINT_UPGRADE_APPLY` explicitly in Stage 2 env.
- [x] `upgrade_consumer_pipeline.sh`: read `upgrade_apply.json` status; update Stage 2 abort condition.
- [x] `upgrade_consumer_pipeline.sh`: add `[PIPELINE] PLAN-ONLY mode` banner when `BLUEPRINT_UPGRADE_APPLY=false`.
- [x] `upgrade_consumer_pipeline.sh`: update usage block to document the new default.
- [x] `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: update apply-by-default documentation.
- [x] Gate: `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → 5 GREEN.
- [x] Gate: `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` → 9 GREEN.
- [x] Gate: `make quality-hooks-fast`.

## App Onboarding Minimum Targets (Normative — N/A for this work item)
- [x] A-001 `apps-bootstrap` — no-impact (pre-existing, not modified)
- [x] A-002 `apps-smoke` — no-impact (pre-existing, not modified)
- [x] A-003 Backend lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [x] A-004 Frontend lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [x] A-005 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [x] A-006 Port-forward wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact

## Pre-PR Gates
- [x] `make quality-hooks-fast` → PASS (shellcheck, infra-validate, infra-contract-test-fast, quality-sdd-check-all all GREEN).
- [x] Populate `pr_context.md` with full evidence.
- [x] Populate `hardening_review.md` with full findings.
- [x] Update `AGENTS.backlog.md` to mark work item Done.
- [x] Update `AGENTS.decisions.md` if any scope or priority changes occurred. N/A — no scope or priority changes.

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (9 regression tests GREEN, make quality-hooks-fast PASS), and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
