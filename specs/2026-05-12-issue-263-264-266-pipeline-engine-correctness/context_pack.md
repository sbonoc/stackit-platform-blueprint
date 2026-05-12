# Work Item Context Pack

## Context Snapshot
- Work item: `specs/2026-05-12-issue-263-264-266-pipeline-engine-correctness`
- Track: blueprint
- SPEC_READY: false
- ADR path: `docs/blueprint/architecture/decisions/ADR-issue-263-264-266-pipeline-engine-correctness.md`
- ADR status: proposed

## Scope Summary
Three correctness bugs in the scripted upgrade pipeline, all confirmed in a real consumer upgrade (sbonoc/dhe-marketplace v1.7.0 → v1.10.0, PR #62, 88 conflicts):
- **#263** — `_resolve_baseline_ref` reads `template_version` (immutable init version) instead of the most recently applied version, causing baseline-unavailable conflicts on every upgrade hop after the first.
- **#264** — GNU make wraps engine `exit 1` (conflicts present) as `exit 2`; pipeline's `> 1` check always fires, aborting Stages 3–10 whenever there are conflicts.
- **#266** — `upgrade_consumer_pipeline.sh` never sets `BLUEPRINT_UPGRADE_APPLY=true`; standalone script defaults to `false`; pipeline silently runs in plan-only mode unless the user explicitly exports the variable.

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024

## Key Files
- `scripts/lib/blueprint/upgrade_consumer.py` — engine: `_resolve_baseline_ref` + apply exit code + status
- `scripts/lib/blueprint/contract_schema.py` — `TemplateBootstrapContract.last_applied_version` field
- `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — writes `last_applied_version` on success
- `scripts/lib/blueprint/upgrade_version_pin_diff.py` — also uses `_resolve_baseline_ref`; needs same update
- `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — adds "conflicts" to status enum
- `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — Stage 2 fix + APPLY default + banner
- `blueprint/contract.yaml` — gains `last_applied_version` optional field under `template_bootstrap`
- `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — runbook update (apply-by-default)
- `tests/infra/test_upgrade_baseline_issue_263.py` — new regression test file (4 tests, to be created)
- `tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py` — new regression test file (4 tests, to be created)

## Required Commands
- `uv run python3 -m pytest tests/infra/test_upgrade_baseline_issue_263.py -v`
- `uv run python3 -m pytest tests/infra/test_upgrade_pipeline_correctness_issue_264_266.py -v`
- `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules`
- `make quality-hooks-fast`
- `make quality-hooks-run`
- `make infra-validate`
- `make quality-sdd-check`
- `make quality-hardening-review`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `context_pack.md`
- `pr_context.md`
- `hardening_review.md`
