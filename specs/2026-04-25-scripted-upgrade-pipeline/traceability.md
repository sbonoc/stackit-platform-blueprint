# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Stage 1 pre-flight: dirty-tree abort | `scripts/lib/blueprint/upgrade_preflight.py` (called by `upgrade_consumer.sh`) | `tests/blueprint/test_upgrade_pipeline.py::TestPreflightDirtyTree` | `architecture.md § Stage 1`, `plan.md § Slice 1` | `upgrade-residual.md` abort message |
| FR-002 | SDD-C-005 | Stage 1 pre-flight: unresolved ref abort | `scripts/lib/blueprint/upgrade_preflight.py` (called by `upgrade_consumer.sh`) | `tests/blueprint/test_upgrade_pipeline.py::TestPreflightInvalidRef` | `architecture.md § Stage 1`, `plan.md § Slice 1` | `upgrade-residual.md` abort message |
| FR-003 | SDD-C-005 | Stage 1 pre-flight: bad contract abort | `scripts/lib/blueprint/upgrade_preflight.py` (called by `upgrade_consumer.sh`) | `tests/blueprint/test_upgrade_pipeline.py::TestPreflightBadContract` | `architecture.md § Stage 1`, `plan.md § Slice 1` | `upgrade-residual.md` abort message |
| FR-004 | SDD-C-005, SDD-C-007 | Stage 2 ALLOW_DELETE propagation; `make help` entry | `scripts/bin/blueprint/upgrade_consumer.sh` Stage 2; `make/blueprint.mk` | `tests/blueprint/test_upgrade_pipeline.py::TestAllowDeletePropagation` | `plan.md § Slice 7`, `SKILL.md` | `upgrade-residual.md` delete summary |
| FR-005 | SDD-C-005, SDD-C-012 | Stage 3 contract resolver: preserve identity | `scripts/lib/blueprint/resolve_contract_upgrade.py` | `tests/blueprint/test_upgrade_pipeline.py::TestContractResolverIdentityPreservation` (AC-002) | `architecture.md § Stage 3`, `plan.md § Slice 2` | `contract_resolve_decisions.json` |
| FR-006 | SDD-C-005, SDD-C-012 | Stage 3 contract resolver: merge required_files | `scripts/lib/blueprint/resolve_contract_upgrade.py` | `tests/blueprint/test_upgrade_pipeline.py::TestContractResolverRequiredFilesMerge` | `architecture.md § Stage 3`, `plan.md § Slice 2` | `contract_resolve_decisions.json` dropped entries |
| FR-007 | SDD-C-005, SDD-C-012 | Stage 3 contract resolver: drop matching prune globs | `scripts/lib/blueprint/resolve_contract_upgrade.py` | `tests/blueprint/test_upgrade_pipeline.py::TestContractResolverPruneGlobDrop` | `architecture.md § Stage 3`, `plan.md § Slice 2` | `contract_resolve_decisions.json` dropped globs |
| FR-008 | SDD-C-005, SDD-C-010 | Stage 3: emit contract_resolve_decisions.json | `scripts/lib/blueprint/resolve_contract_upgrade.py` | `tests/blueprint/test_upgrade_pipeline.py::TestContractResolverDecisionJSON` | `spec.md § Contract Changes`, `architecture.md § Stage 3` | `artifacts/blueprint/contract_resolve_decisions.json` |
| FR-009 | SDD-C-005, SDD-C-012 | Stage 5: compare contract refs vs disk | `scripts/lib/blueprint/upgrade_coverage_fetch.py` | `tests/blueprint/test_upgrade_pipeline.py::TestCoverageGapDetection` | `architecture.md § Stage 5`, `plan.md § Slice 3` | `upgrade-residual.md` coverage section |
| FR-010 | SDD-C-005, SDD-C-009 | Stage 5: fetch absent files via local git | `scripts/lib/blueprint/upgrade_coverage_fetch.py` | `tests/blueprint/test_upgrade_pipeline.py::TestCoverageGapFileFetch` (AC-003) | `architecture.md § Stage 5`, `plan.md § Slice 3` | `upgrade-residual.md` fetched files |
| FR-011 | SDD-C-005 | Stage 6: mirror sync | `scripts/lib/blueprint/upgrade_mirror_sync.py` | `tests/blueprint/test_upgrade_pipeline.py::TestMirrorSync` | `architecture.md § Stage 6`, `plan.md § Slice 4` | `scripts/templates/blueprint/bootstrap/` updated paths |
| FR-012 | SDD-C-005, SDD-C-010 | Stage 7: doc target validation (warns, no abort) | `scripts/lib/blueprint/upgrade_doc_target_check.py` | `tests/blueprint/test_upgrade_pipeline.py::TestDocTargetCheck` | `architecture.md § Stage 7`, `plan.md § Slice 5` | `upgrade-residual.md` missing target warnings |
| FR-013 | SDD-C-005, SDD-C-016 | Stage 8: docs regen (single prescribed sync point) | `scripts/bin/blueprint/upgrade_consumer.sh` Stage 8 | `tests/blueprint/test_upgrade_pipeline.py::TestDocsSyncInvoked` | `plan.md § Slice 7` | make output |
| FR-014 | SDD-C-005, SDD-C-014 | Stage 9: gate chain; structured error on failure | `scripts/bin/blueprint/upgrade_consumer.sh` Stage 9 | `tests/blueprint/test_upgrade_pipeline.py::TestGateChainAbort` | `architecture.md § Stage 9`, `plan.md § Slice 7` | `upgrade-residual.md` gate status |
| FR-015 | SDD-C-005, SDD-C-010 | Stage 10: residual report always emitted | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/test_upgrade_pipeline.py::TestResidualReportAlwaysEmitted` | `architecture.md § Stage 10`, `plan.md § Slice 6` | `artifacts/blueprint/upgrade-residual.md` |
| FR-016 | SDD-C-005, SDD-C-010 | Stage 10: every item has prescribed action | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/test_upgrade_pipeline.py::TestResidualReportPrescribedActions` | `architecture.md § Stage 10`, `plan.md § Slice 6` | `artifacts/blueprint/upgrade-residual.md` |
| FR-017 | SDD-C-005, SDD-C-010 | Stage 10: consumer-owned files listed | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/test_upgrade_pipeline.py::TestResidualReportConsumerOwned` | `architecture.md § Stage 10`, `plan.md § Slice 6` | `artifacts/blueprint/upgrade-residual.md` |
| FR-018 | SDD-C-005, SDD-C-010 | Stage 10: pyramid classification gaps listed | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/test_upgrade_pipeline.py::TestResidualReportPyramidGaps` | `architecture.md § Stage 10`, `plan.md § Slice 6` | `artifacts/blueprint/upgrade-residual.md` |
| FR-019 | SDD-C-005 | Existing targets remain independently callable | `make/blueprint.mk` (additive only) | `tests/blueprint/test_upgrade_consumer.py` no regression (AC-006) | `plan.md § Backward compatibility policy` | individual make targets |
| NFR-SEC-001 | SDD-C-009 | No HTTP fetches; local git only for file retrieval | `scripts/lib/blueprint/upgrade_coverage_fetch.py` | `tests/blueprint/test_upgrade_pipeline.py::TestCoverageGapNoHTTP` | `architecture.md § Security`, `spec.md § NFR-SEC-001` | no external network calls in pipeline |
| NFR-REL-001 | SDD-C-012 | Idempotency: twice on clean tree → no changes, exit 0 | `scripts/bin/blueprint/upgrade_consumer.sh` | `tests/blueprint/test_upgrade_pipeline.py::TestIdempotency` | `architecture.md § Reliability`, `plan.md § Slice 7` | second run produces no diff |
| NFR-OPS-001 | SDD-C-005 | No consumer-specific logic in scripts | All new `scripts/lib/blueprint/upgrade_*.py` | `tests/blueprint/test_upgrade_pipeline.py::TestNoConsumerSpecificHardcoding` | `architecture.md § Non-Functional`, `spec.md § NFR-OPS-001` | code review |
| NFR-OBS-001 | SDD-C-010 | Stage-labeled progress lines to stdout | `scripts/bin/blueprint/upgrade_consumer.sh` | `tests/blueprint/test_upgrade_pipeline.py::TestProgressLines` | `architecture.md § Observability`, `spec.md § NFR-OBS-001` | stdout during pipeline run |
| AC-001 | SDD-C-012 | End-to-end pipeline exits 0 on clean tree, all gates pass | `scripts/bin/blueprint/upgrade_consumer.sh` + all stages | `tests/blueprint/test_upgrade_pipeline.py::TestEndToEnd` | `spec.md § AC-001`, `plan.md § Slice 8` | make exit code + residual report |
| AC-002 | SDD-C-012 | contract.yaml name+repo_mode preserved; verified by unit test | `scripts/lib/blueprint/resolve_contract_upgrade.py` | `tests/blueprint/test_upgrade_pipeline.py::TestContractResolverIdentityPreservation` | `spec.md § AC-002`, `plan.md § Slice 2` | decision JSON + resolved YAML |
| AC-003 | SDD-C-012 | Absent required file auto-fetched from upgrade source | `scripts/lib/blueprint/upgrade_coverage_fetch.py` | `tests/blueprint/test_upgrade_pipeline.py::TestCoverageGapFileFetch` | `spec.md § AC-003`, `plan.md § Slice 3` | fixture source repo integration test |
| AC-004 | SDD-C-012 | action=skip files deleted by Stage 2 (when delete enabled) | existing `blueprint-upgrade-fresh-env-gate` | existing `test_upgrade_fresh_env_gate.py` (no modification) | `spec.md § AC-004`, `plan.md § Slice 7` | fresh-env-gate pass |
| AC-005 | SDD-C-012 | Residual report always generated; every item has prescribed action | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/test_upgrade_pipeline.py::TestResidualReportAlwaysEmitted` | `spec.md § AC-005`, `plan.md § Slice 6` | `artifacts/blueprint/upgrade-residual.md` |
| AC-006 | SDD-C-012 | Existing upgrade gate tests pass without modification | existing targets (unchanged) | `tests/blueprint/test_upgrade_consumer.py`, `test_upgrade_consumer_wrapper.py`, `test_upgrade_preflight.py`, `test_upgrade_postcheck.py` | `spec.md § AC-006`, `plan.md § Backward compatibility policy` | pytest output |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010
  - FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019
  - NFR-SEC-001, NFR-REL-001, NFR-OPS-001, NFR-OBS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed: pending implementation
- Result summary: pending implementation
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1 (resolved): Q-1 → Option B selected (broad scope). FR-010 fetches any contract-referenced file absent from disk regardless of plan coverage. Decision recorded in spec.md 2026-04-25.
- Follow-up 2 (resolved): Q-2 → Option A selected (delete ON). `BLUEPRINT_UPGRADE_ALLOW_DELETE=true` is the pipeline default; `=false` is the non-destructive override. FR-004 updated in spec.md 2026-04-25.
- Follow-up 3: Issue #189 (prune glob enforcement in planner/validate/postcheck) — complementary work item that enforces `source_artifact_prune_globs_on_init` at the plan phase; Stage 5 of this work item is independent (broad scope option B does not rely on the #185 invariant). Keep as a separate work item.
