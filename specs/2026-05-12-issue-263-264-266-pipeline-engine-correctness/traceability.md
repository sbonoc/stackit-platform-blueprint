# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § Baseline resolution logic | `scripts/lib/blueprint/upgrade_consumer.py` — `_resolve_baseline_ref`; `scripts/lib/blueprint/upgrade_version_pin_diff.py` — `_resolve_baseline_ref`; `scripts/lib/blueprint/contract_schema.py` — `TemplateBootstrapContract.last_applied_version`; `blueprint/contract.yaml` — `last_applied_version` field | `tests/infra/test_upgrade_baseline_issue_263.py::BaselineResolutionLastAppliedVersionTests` | `docs/platform/consumer/troubleshooting.md` — last_applied_version migration note | deferred to CI |
| FR-002 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § After fixes component design | `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — `last_applied_version` write on success | `tests/infra/test_upgrade_baseline_issue_263.py::PostcheckLastAppliedVersionBumpTests` | `docs/platform/consumer/troubleshooting.md` | deferred to CI |
| FR-003 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § After fixes pipeline flowchart | `scripts/lib/blueprint/upgrade_consumer.py` — `status = "conflicts"` + `return 0`; `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — "conflicts" enum; `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — Stage 2 artifact-driven check | `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py::EngineExitCodeIssue264Tests` | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `make quality-hooks-run` PASS |
| FR-004 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § Pipeline wrapper bounded context | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — `set_default_env BLUEPRINT_UPGRADE_APPLY true`; banner; propagation; usage block | `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py::PipelineApplyDefaultIssue266Tests` | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `make quality-hooks-run` PASS |
| NFR-SEC-001 | SDD-C-009 | N/A | `architecture.md` § Non-Functional Architecture Notes — Security | N/A — `last_applied_version` is a semver string; no credential written | N/A | N/A | N/A |
| NFR-OBS-001 | SDD-C-010 | N/A | `architecture.md` § Non-Functional Architecture Notes — Observability | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — Stage 2 log line gains `status=`; `scripts/lib/blueprint/upgrade_consumer.py` — metric emission for conflicts | `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py` — `test_apply_artifact_status_is_conflicts_when_conflicts_present` | N/A | `make quality-hooks-run` PASS |
| NFR-REL-001 | SDD-C-012 | N/A | `plan.md` § Change Strategy | `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — write only on success; `scripts/lib/blueprint/contract_schema.py` — optional field with empty default | `tests/infra/test_upgrade_baseline_issue_263.py::PostcheckLastAppliedVersionBumpTests.test_does_not_write_last_applied_version_on_failure` | N/A | deferred to CI |
| NFR-OPS-001 | SDD-C-012 | N/A | `plan.md` § Documentation Plan | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — usage block; `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | N/A | `make quality-hooks-run` PASS |
| NFR-A11Y-001 | N/A | N/A | N/A — no UI surface | N/A | N/A | N/A | N/A |
| AC-001 | SDD-C-012 | N/A | `plan.md` § Slice 1 | `upgrade_consumer.py` — `_resolve_baseline_ref` | `BaselineResolutionLastAppliedVersionTests.test_prefers_last_applied_version_over_template_version` (1 test) | N/A | deferred to CI |
| AC-002 | SDD-C-012 | N/A | `plan.md` § Slice 1 | `upgrade_consumer.py` — `_resolve_baseline_ref` fallback | `BaselineResolutionLastAppliedVersionTests.test_falls_back_to_template_version_when_field_absent` (1 test) | N/A | deferred to CI |
| AC-003 | SDD-C-012 | N/A | `plan.md` § Slice 2 | `upgrade_consumer_postcheck.py` — write path | `PostcheckLastAppliedVersionBumpTests.test_writes_last_applied_version_on_success` (1 test) | N/A | deferred to CI |
| AC-004 | SDD-C-012 | N/A | `plan.md` § Slice 3 | `upgrade_consumer_pipeline.sh` — Stage 2 artifact-driven check | `EngineExitCodeIssue264Tests.test_engine_exits_zero_on_conflicts` (1 test) | N/A | `make quality-hooks-run` PASS |
| AC-005 | SDD-C-012 | N/A | `plan.md` § Slice 3 | `upgrade_consumer_pipeline.sh` — abort on true error | `EngineExitCodeIssue264Tests.test_apply_artifact_status_is_conflicts_when_conflicts_present` (1 test) | N/A | `make quality-hooks-run` PASS |
| AC-006 | SDD-C-012 | N/A | `plan.md` § Slice 4 | `upgrade_consumer_pipeline.sh` — `set_default_env BLUEPRINT_UPGRADE_APPLY true` | `PipelineApplyDefaultIssue266Tests.test_pipeline_apply_default_is_true` (1 test) | N/A | `make quality-hooks-run` PASS |
| AC-007 | SDD-C-012 | N/A | `plan.md` § Slice 4 | `upgrade_consumer_pipeline.sh` — banner when APPLY=false | `PipelineApplyDefaultIssue266Tests.test_pipeline_emits_banner_when_apply_false` (1 test) | N/A | `make quality-hooks-run` PASS |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: to be populated after implementation (Verify phase).
- Result summary: to be populated after implementation.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Issue #183 — `upgrade_consumer_postcheck` stale reconcile report detection (`trigger: triage: next-session`). Related since postcheck is touched in this work item; surfaced for triage but not incorporated into scope.
