# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Reconcile bucket artifact contract | scripts/lib/blueprint/upgrade_reconcile_report.py; scripts/lib/blueprint/upgrade_consumer.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_*reconcile* | specs/2026-04-18-upgrade-convergence-postcheck-gate/spec.md | artifacts/blueprint/upgrade/upgrade_reconcile_report.json |
| FR-002 | SDD-C-005 | Reconcile metadata and command-plan contract | scripts/lib/blueprint/upgrade_consumer.py; scripts/lib/blueprint/schemas/upgrade_reconcile_report.schema.json | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_*reconcile* | specs/2026-04-18-upgrade-convergence-postcheck-gate/pr_context.md | reconcile report summary + metadata |
| FR-003 | SDD-C-005 | Preflight merge-risk bucketing and remediation hints | scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_*merge_risk* | docs/platform/consumer/quickstart.md | artifacts/blueprint/upgrade_preflight.json merge_risk_classification |
| FR-004 | SDD-C-005 | Postcheck convergence gate | scripts/bin/blueprint/upgrade_consumer_postcheck.sh; scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_postcheck.UpgradePostcheckTests.test_* | docs/README.md | artifacts/blueprint/upgrade_postcheck.json |
| FR-005 | SDD-C-005 | Repo-mode-aware docs-hook branch | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_postcheck.UpgradePostcheckTests.test_postcheck_repo_mode_docs_hooks | docs/blueprint/architecture/execution_model.md | postcheck docs_hook_checks |
| FR-006 | SDD-C-005 | Skill safe/blocked contract | .agents/skills/blueprint-consumer-upgrade/SKILL.md; scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/SKILL.md.tmpl | tests.blueprint.test_quality_contracts.QualityContractTests.test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports | docs/platform/consumer/troubleshooting.md | skill reporting checklist |
| NFR-SEC-001 | SDD-C-009 | Repo-scoped artifact path resolution | scripts/lib/blueprint/upgrade_consumer.py; scripts/lib/blueprint/upgrade_preflight.py; scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_rejects_*outside_repo_root | specs/2026-04-18-upgrade-convergence-postcheck-gate/spec.md | path validation errors |
| NFR-OBS-001 | SDD-C-010 | Reconcile/postcheck metrics | scripts/lib/blueprint/upgrade_report_metrics.py; scripts/bin/blueprint/upgrade_consumer.sh; scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests.blueprint.test_quality_contracts.QualityContractTests.test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports | specs/2026-04-18-upgrade-convergence-postcheck-gate/hardening_review.md | wrapper metrics output |
| NFR-REL-001 | SDD-C-011 | Deterministic ordering and status contract | scripts/lib/blueprint/upgrade_reconcile_report.py; scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_dry_run_is_deterministic_and_preserves_target_content | specs/2026-04-18-upgrade-convergence-postcheck-gate/spec.md | sorted buckets and deterministic summary keys |
| NFR-OPS-001 | SDD-C-018 | Actionable diagnostics and next commands | scripts/lib/blueprint/upgrade_preflight.py; scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_*merge_risk* | docs/platform/consumer/troubleshooting.md | blocked reasons + next commands |
| AC-001 | SDD-C-012 | Reconcile artifact required buckets + metadata | scripts/lib/blueprint/upgrade_reconcile_report.py; scripts/lib/blueprint/upgrade_consumer.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_*reconcile* | specs/2026-04-18-upgrade-convergence-postcheck-gate/pr_context.md | upgrade_reconcile_report summary |
| AC-002 | SDD-C-012 | Preflight bucketed risk hints | scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_*merge_risk* | specs/2026-04-18-upgrade-convergence-postcheck-gate/plan.md | merge_risk_classification |
| AC-003 | SDD-C-012 | Postcheck pass/fail convergence conditions | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_postcheck.UpgradePostcheckTests.test_postcheck_* | specs/2026-04-18-upgrade-convergence-postcheck-gate/pr_context.md | upgrade_postcheck summary.status |
| AC-004 | SDD-C-012 | Repo-mode docs-hook behavior | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests.blueprint.test_upgrade_postcheck.UpgradePostcheckTests.test_postcheck_repo_mode_docs_hooks | docs/README.md | docs_hook_checks |
| AC-005 | SDD-C-012 | Skill UX and deterministic next commands | .agents/skills/blueprint-consumer-upgrade/SKILL.md | tests.blueprint.test_quality_contracts.QualityContractTests.test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports | scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/SKILL.md.tmpl | skill report checklist |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_consumer_wrapper tests.blueprint.test_upgrade_postcheck -v`
  - `make quality-docs-sync-all`
  - `make quality-hooks-fast`
  - `make quality-hooks-run`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
- Result summary:
  - all commands above passed after applying reconcile classification + wrapper compatibility fixes.
  - generated docs artifacts and test-pyramid classification were synchronized to satisfy fast quality gates.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: evaluate unifying preflight and upgrade reconcile report rendering under one schema-validator CLI.
