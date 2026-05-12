# PR Context

## Summary
- Work item: `specs/2026-05-12-issue-263-264-266-pipeline-engine-correctness` — issues #263, #264, #266
- Objective: Fix three pipeline/engine correctness bugs: wrong baseline ref on multi-hop upgrades (#263), engine exiting 1 for file conflicts causing pipeline abort (#264), and pipeline silently defaulting to plan-only mode (#266).
- Scope boundaries: upgrade engine (`upgrade_consumer.py`, `upgrade_version_pin_diff.py`), postcheck (`upgrade_consumer_postcheck.py`), contract schema (`contract_schema.py`), apply artifact schema (`upgrade_apply.schema.json`), pipeline script (`upgrade_consumer_pipeline.sh`), bootstrap template mirror. No changes to app make targets, infra modules, or consumer-owned paths.

## Requirement Coverage
- Requirement IDs covered: FR-001 (baseline ref resolution), FR-002 (last_applied_version persistence), FR-003 (conflict exit code), FR-004 (pipeline APPLY default), FR-005 (plan-only banner)
- Acceptance criteria covered: AC-001 (prefers last_applied_version), AC-002 (falls back to template_version), AC-003 (postcheck writes on success), AC-004 (exit 0 + status=conflicts), AC-005 (exit 1 retained for merge markers), AC-006 (APPLY default=true + plan-only banner)
- Contract surfaces changed: `blueprint/contract.yaml` — new `last_applied_version: ""` field; `upgrade_apply.schema.json` — new `"conflicts"` value in status enum

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_resolve_baseline_ref` (prefers last_applied_version), conflict exit-code path (return 0, status=conflicts)
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — `set_default_env BLUEPRINT_UPGRADE_APPLY true`, PLAN-ONLY banner, Stage 2 artifact-driven check
  - `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — `_write_last_applied_version` helper
- High-risk files:
  - `blueprint/contract.yaml` — added `last_applied_version` field; bootstrap template mirror in `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` synced identically
  - `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — status enum extended with `"conflicts"`

## Validation Evidence
- Required commands executed: `make quality-hooks-fast` → all hooks PASS; 9/9 infra regression tests GREEN
  - `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v` → 4 PASS (AC-001, AC-002, AC-003, NFR-REL-001)
  - `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v` → 5 PASS (AC-004, AC-005, AC-006)
  - `make quality-hooks-fast` → shellcheck PASS, infra-validate PASS, infra-contract-test-fast PASS, quality-sdd-check-all PASS
- Result summary: all 9 new regression tests GREEN; all quality hooks pass; pre-existing `test_public_endpoints_module_flow` failure confirmed unrelated and pre-existing.
- Artifact references: `tests/infra/test_upgrade_baseline_issue_263.py`, `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py`

## Risk and Rollback
- Main risks: (1) `BLUEPRINT_UPGRADE_APPLY=true` default only affects implicit pipeline invocations; callers setting it explicitly are unaffected. (2) Status `"conflicts"` is a new enum value — schema updated accordingly; any tooling hard-coding `["success","failure"]` needs updating. (3) `last_applied_version` field defaults to `""` — no existing consumer broken.
- Rollback strategy: Revert `upgrade_consumer.py`, `upgrade_consumer_pipeline.sh`, `upgrade_consumer_postcheck.py`, `upgrade_apply.schema.json`; remove `last_applied_version` line from both `blueprint/contract.yaml` and its bootstrap template mirror. No database or state migrations required.

## Deferred Proposals
