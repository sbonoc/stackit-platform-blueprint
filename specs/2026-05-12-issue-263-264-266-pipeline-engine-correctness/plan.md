# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: three targeted fixes; each touches the narrowest possible scope per issue.
- Anti-abstraction gate: no new helpers or wrapper layers; direct edits to existing functions only.
- Integration-first testing gate: regression tests import engine functions and pipeline helpers directly; no mocks for the contract schema or artifact reads.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: all three bugs are reproducible (confirmed in real upgrade run); each MUST have a failing test before the fix is applied.

## Delivery Slices

### Slice 1 — Failing tests for #263 (last_applied_version) [RED]
Write `tests/infra/test_upgrade_baseline_issue_263.py` with:
- `BaselineResolutionLastAppliedVersionTests.test_prefers_last_applied_version_over_template_version` — RED (function doesn't accept `last_applied_version` yet)
- `BaselineResolutionLastAppliedVersionTests.test_falls_back_to_template_version_when_field_absent` — RED
- `PostcheckLastAppliedVersionBumpTests.test_writes_last_applied_version_on_success` — RED (postcheck doesn't write field yet)
- `PostcheckLastAppliedVersionBumpTests.test_does_not_write_last_applied_version_on_failure` — RED

Gate: `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → all 4 FAIL.

### Slice 2 — Fix #263 [GREEN]
1. `scripts/lib/blueprint/contract_schema.py`: add `last_applied_version: str = ""` to `TemplateBootstrapContract` dataclass (optional, defaults to empty string); add parsing in `load_blueprint_contract` from `template_raw.get("last_applied_version", "")`.
2. `scripts/lib/blueprint/upgrade_consumer.py`: update `_resolve_baseline_ref(source_repo, template_version, last_applied_version="")` — try `last_applied_version` candidates first when non-empty, then fall back to `template_version`; update call site to pass `contract.repository.template_bootstrap.last_applied_version`.
3. `scripts/lib/blueprint/upgrade_version_pin_diff.py`: apply same preference — read `last_applied_version` from contract and pass to `_resolve_baseline_ref`; fall back to `template_version` when absent.
4. `scripts/lib/blueprint/upgrade_consumer_postcheck.py`: after `status == "success"`, read `upgrade_ref` from `apply_payload`; write `last_applied_version: <upgrade_ref>` into `blueprint/contract.yaml` using `ruamel.yaml` (preserve comments) or PyYAML; emit a log line confirming the write.
5. `blueprint/contract.yaml`: add `last_applied_version: ""` under `template_bootstrap` with a comment marking it as engine-managed.

Gate: `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → all 4 GREEN; `uv run python3 -m pytest tests/infra/ -q` → no regressions.

### Slice 3 — Failing tests for #264 + #266 [RED]
Write `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py` with:
- `EngineExitCodeIssue264Tests.test_engine_exits_zero_on_conflicts` — RED (engine currently exits 1)
- `EngineExitCodeIssue264Tests.test_apply_artifact_status_is_conflicts_when_conflicts_present` — RED (status currently "failure")
- `EngineExitCodeIssue264Tests.test_engine_exits_nonzero_on_merge_markers` — RED (engine must retain exit 1 for merge-marker true failures, covering AC-005 abort path)
- `PipelineApplyDefaultIssue266Tests.test_pipeline_apply_default_is_true` — RED (default is false)
- `PipelineApplyDefaultIssue266Tests.test_pipeline_emits_banner_when_apply_false` — RED

Gate: `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → all 5 FAIL.

### Slice 4 — Fix #264 + #266 [GREEN]
1. `scripts/lib/blueprint/upgrade_consumer.py`: when `args.apply and conflict_count > 0`: set `apply_payload["status"] = "conflicts"` (not "failure"); change `return 1` to `return 0`. Keep `return 1` for merge-markers path (that is a true failure — malformed apply state).
2. `scripts/lib/blueprint/schemas/upgrade_apply.schema.json`: add `"conflicts"` to the `status` enum.
3. `scripts/bin/blueprint/upgrade_consumer_pipeline.sh`: Stage 2 changes:
   - Add `set_default_env BLUEPRINT_UPGRADE_APPLY true` after existing defaults.
   - After Stage 2 make invocation: read `upgrade_apply.json` status into `_apply_status`; change abort condition from `rc > 1` to `rc != 0 AND _apply_status != "conflicts"`; include `status=<_apply_status>` in the Stage 2 completion log line.
   - Add `[PIPELINE]` banner before Stage 2 when `BLUEPRINT_UPGRADE_APPLY` resolves to `false`.
   - Propagate `BLUEPRINT_UPGRADE_APPLY="$BLUEPRINT_UPGRADE_APPLY"` explicitly in the Stage 2 make invocation env prefix.
   - Update usage block to document the new default.
4. `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: update apply-mode documentation.

Gate: `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → all 4 GREEN; `uv run python3 -m pytest tests/infra/ -q` → no regressions; `make quality-hooks-fast`.

## Change Strategy
- Migration/rollout sequence: Slices apply in order 1→2→3→4. Slices 1+2 are independent of Slices 3+4 and can be developed in sequence without coordination gaps.
- Backward compatibility policy: `upgrade_consumer.sh` (standalone) retains `BLUEPRINT_UPGRADE_APPLY=false` default. Only `upgrade_consumer_pipeline.sh` changes its default. Existing consumers that call `make blueprint-upgrade-consumer` with `BLUEPRINT_UPGRADE_APPLY=false` explicitly will see the banner but no behavioral change. Consumers with no `last_applied_version` in their contract will continue using `template_version` as baseline until their first successful postcheck.
- Rollback plan: single-file revert per component; no database or schema migration needed. Removing `last_applied_version` from `blueprint/contract.yaml` reverts to old baseline resolution. Setting `BLUEPRINT_UPGRADE_APPLY` env var before pipeline invocation bypasses the new default.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` — 9 tests covering all 7 acceptance criteria.
- Contract checks: `make infra-validate` — verifies `blueprint/contract.yaml` schema; `make quality-sdd-check` — spec artifact validation.
- Integration checks: `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` — full infra suite; no regressions.
- E2E checks: deferred — `make blueprint-upgrade-consumer` against a real consumer requires live clone; deferred to CI pipeline.

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
- App onboarding impact: no-impact — no app delivery scope is affected; all make targets above are pre-existing and unchanged by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — reflect apply-by-default; note BLUEPRINT_UPGRADE_APPLY=false for plan-only.
- Consumer docs updates: `docs/platform/consumer/troubleshooting.md` — add note about `last_applied_version` migration and the APPLY default change.
- Mermaid diagrams updated: `architecture.md` in this work item (already written).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP route handlers or query/filter endpoints touched.
- Publish checklist:
  - include requirement/contract coverage (FR-001 through FR-004, AC-001 through AC-007)
  - include key reviewer files (upgrade_consumer.py, upgrade_consumer_postcheck.py, contract_schema.py, upgrade_consumer_pipeline.sh, blueprint/contract.yaml)
  - include validation evidence (8 new tests GREEN, full infra suite pass)
  - include rollback notes (single-file reverts, env-var override)

## Operational Readiness
- Logging/metrics/traces: Stage 2 log gains `status=` field; engine emits `blueprint_upgrade_apply_status_total status=conflicts` metric via existing metric emission path.
- Alerts/ownership: no new alerts; existing `blueprint_upgrade_apply_status_total` dimension extended.
- Runbook updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — apply default; `last_applied_version` migration note.

## Risks and Mitigations
- Risk: engine exit 0 for conflicts changes callers that check make exit code directly → mitigation: banner + docs; the `upgrade_apply.json` artifact was always the canonical result carrier.
- Risk: postcheck writes to `blueprint/contract.yaml` using YAML write path — if YAML parser re-formats the file, diff noise is introduced → mitigation: use `ruamel.yaml` round-trip mode to preserve formatting; or update only the specific scalar value via sed-equivalent if the field already exists.
