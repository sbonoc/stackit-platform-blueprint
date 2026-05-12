# Tasks

## Pre-Implementation Gate
- [ ] SPEC_READY: false — implementation tasks MUST remain unchecked until spec is approved.

## Slice 1 — Failing tests for #263 [RED]
- [ ] Write `tests/infra/test_upgrade_baseline_issue_263.py` with 4 failing tests.
- [ ] Confirm `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → 4 FAIL.

## Slice 2 — Fix #263: last_applied_version baseline resolution [GREEN]
- [ ] `contract_schema.py`: add `last_applied_version: str = ""` to `TemplateBootstrapContract`; parse from contract YAML.
- [ ] `upgrade_consumer.py`: update `_resolve_baseline_ref` signature + logic to prefer `last_applied_version`.
- [ ] `upgrade_version_pin_diff.py`: apply same `last_applied_version` preference to its `_resolve_baseline_ref`.
- [ ] `upgrade_consumer_postcheck.py`: write `last_applied_version` to `blueprint/contract.yaml` on postcheck success.
- [ ] `blueprint/contract.yaml`: add `last_applied_version: ""` under `template_bootstrap`.
- [ ] Gate: `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → 4 GREEN.
- [ ] Gate: `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` → no regressions.
- [ ] Gate: `make quality-hooks-fast`.

## Slice 3 — Failing tests for #264 + #266 [RED]
- [ ] Write `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py` with 5 failing tests (including `test_engine_exits_nonzero_on_merge_markers` for AC-005).
- [ ] Confirm `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → 5 FAIL.

## Slice 4 — Fix #264 + #266: exit code disambiguation + APPLY default [GREEN]
- [ ] `upgrade_consumer.py`: set `status = "conflicts"` and `return 0` when apply has conflicts (not merge markers).
- [ ] `upgrade_apply.schema.json`: add `"conflicts"` to `status` enum.
- [ ] `upgrade_consumer_pipeline.sh`: add `set_default_env BLUEPRINT_UPGRADE_APPLY true`.
- [ ] `upgrade_consumer_pipeline.sh`: propagate `BLUEPRINT_UPGRADE_APPLY` explicitly in Stage 2 env.
- [ ] `upgrade_consumer_pipeline.sh`: read `upgrade_apply.json` status; update Stage 2 abort condition.
- [ ] `upgrade_consumer_pipeline.sh`: add `[PIPELINE]` banner when `BLUEPRINT_UPGRADE_APPLY=false`.
- [ ] `upgrade_consumer_pipeline.sh`: update usage block to document the new default.
- [ ] `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: update apply-by-default documentation.
- [ ] Gate: `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → 4 GREEN.
- [ ] Gate: `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` → no regressions.
- [ ] Gate: `make quality-hooks-fast`.

## App Onboarding Minimum Targets (Normative — N/A for this work item)
- [ ] A-001 `apps-bootstrap` — no-impact (pre-existing, not modified)
- [ ] A-002 `apps-smoke` — no-impact (pre-existing, not modified)
- [ ] A-003 Backend lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — no-impact
- [ ] A-004 Frontend lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — no-impact
- [ ] A-005 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — no-impact
- [ ] A-006 Port-forward wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — no-impact

## Pre-PR Gates
- [ ] `make quality-hooks-run` → PASS.
- [ ] `make infra-validate` → PASS.
- [ ] `make quality-hardening-review` → complete; findings recorded in `hardening_review.md`.
- [ ] `make quality-sdd-check` → PASS (SPEC_READY=true required before this gate clears).
- [ ] Populate `pr_context.md` with full evidence.
- [ ] Populate `hardening_review.md` with full findings.
- [ ] Update `AGENTS.backlog.md` to mark work item Done.
- [ ] Update `AGENTS.decisions.md` if any scope or priority changes occurred.
