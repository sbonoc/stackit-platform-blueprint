# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | — | URL normalization block before Stage 1b | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | pipeline usage block | `[PIPELINE] cloned ...` log line |
| FR-002 | SDD-C-005, SDD-C-009 | — | EXIT trap after clone | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | pipeline usage block | tmp dir absent after pipeline exit |
| FR-003 | SDD-C-005 | — | Skip-clone guard in engine | `scripts/lib/blueprint/upgrade_consumer.py` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | — | — |
| FR-004 | SDD-C-005 | — | Local-path fast-path in URL normalization | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | pipeline usage block | — |
| FR-005 | SDD-C-005, SDD-C-011 | — | New make target + script | `scripts/bin/blueprint/upgrade_consumer_finalize.sh`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `tests/infra/test_pipeline_finalize_issue_267.py` | `SKILL.md` | — |
| FR-006 | SDD-C-005, SDD-C-010 | — | Sync pass with aggregated failures | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | finalize script usage block | `[finalize] sync: ...` log lines |
| FR-007 | SDD-C-005, SDD-C-010 | — | Verify pass with fail-fast + summary banner | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | finalize script usage block | `[finalize] FAILED: ...` log line |
| FR-008 | SDD-C-005, SDD-C-011 | — | Pipeline Stage 8+9 replaced by finalize invocation | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | pipeline usage block | — |
| FR-009 | SDD-C-005, SDD-C-011 | — | Skill runbook update | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `make quality-sdd-check` | `SKILL.md` | — |
| NFR-IDM-001 | SDD-C-012 | — | Idempotent make targets (all sync targets write-if-changed) | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` idempotency assertion | — | second-run exit 0 |
| NFR-OBS-001 | SDD-C-010 | — | Per-step log lines via `log_info`/`log_error` | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | test output assertions | — | `[finalize]` log lines in operator output |
| NFR-REL-001 | SDD-C-009 | — | EXIT trap registered immediately after clone | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | pipeline usage block | — |
| NFR-SEC-001 | SDD-C-009 | — | URL prefix allowlist before git clone | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | pipeline usage block | pipeline abort on invalid prefix |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | — | Updated usage blocks in pipeline and finalize scripts | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh`, `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `make quality-sdd-check` | script `--help` output | — |
| NFR-A11Y-001 | — | — | N/A — CLI tool with no browser-rendered UI surface | — | T-A01 | — | — |
| AC-001 | SDD-C-012 | — | Finalize exits 0 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-002 | SDD-C-012 | — | Idempotent second run | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-003 | SDD-C-012 | — | Sync aggregation | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-004 | SDD-C-012 | — | Verify fail-fast | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-005 | SDD-C-012 | — | Pipeline invokes finalize | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-006 | SDD-C-012 | — | Synthetic upgrade scenario | `tests/infra/test_pipeline_finalize_issue_267.py` | `tests/infra/test_pipeline_finalize_issue_267.py` | — | — |
| AC-007 | SDD-C-011 | — | SKILL.md updated | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `make quality-sdd-check` | `SKILL.md` | — |
| AC-008 | SDD-C-012 | — | URL auto-clone + tmp cleanup | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | — | — |
| AC-009 | SDD-C-012, SDD-C-024 | — | Stage 1b + Stage 5 succeed with URL | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | — | — |
| AC-010 | SDD-C-012 | — | Local-path fast-path | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | — | — |
| AC-011 | SDD-C-012, SDD-C-024 | — | URL-form integration test | `tests/infra/test_pipeline_auto_clone_issue_269.py` | `tests/infra/test_pipeline_auto_clone_issue_269.py` | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009
  - NFR-IDM-001, NFR-OBS-001, NFR-REL-001, NFR-SEC-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011

## Validation Summary
- Required bundles executed: (to be filled during Verify phase)
- Result summary: (to be filled during Verify phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: If a future sync target requires `BLUEPRINT_UPGRADE_SOURCE`/`BLUEPRINT_UPGRADE_REF` (e.g., coverage re-fetch), the finalize script will need those env vars threaded through. Track when adding new sync targets.
- Follow-up 2: Standalone finalize usage without a prior pipeline apply (missing reconcile artifacts) will cause postcheck to fail. Future work (Issue #183) may address stale-reconcile detection.
