# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Repo-mode required-file reconciliation | scripts/lib/blueprint/upgrade_consumer_validate.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_reports_success_and_runs_required_targets | specs/2026-04-18-upgrade-validation-required-file-reconciliation/spec.md | artifacts/blueprint/upgrade/required_files_status.json |
| FR-002 | SDD-C-005 | Missing required-file hard-fail with remediation | scripts/lib/blueprint/upgrade_consumer_validate.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_fails_when_required_file_is_missing | specs/2026-04-18-upgrade-validation-required-file-reconciliation/pr_context.md | stderr diagnostics + upgrade_validate summary counts |
| FR-003 | SDD-C-005 | Coupled generated-reference contract checks | scripts/lib/blueprint/upgrade_consumer_validate.py; scripts/lib/blueprint/schemas/upgrade_validate.schema.json | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_reports_success_and_runs_required_targets | specs/2026-04-18-upgrade-validation-required-file-reconciliation/spec.md | generated_reference_contract_check payload + wrapper metrics |
| FR-004 | SDD-C-005 | Preflight required-surfaces-at-risk enrichment | scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_preflight_report_groups_actions_manual_steps_and_follow_up_commands | specs/2026-04-18-upgrade-validation-required-file-reconciliation/plan.md | artifacts/blueprint/upgrade_preflight.json required_surface_reconciliation |
| NFR-SEC-001 | SDD-C-009 | Repo-scoped path resolution | scripts/lib/blueprint/upgrade_consumer_validate.py; scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_rejects_plan_path_outside_repo_root; tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_preflight_rejects_relative_paths_outside_repo_root | specs/2026-04-18-upgrade-validation-required-file-reconciliation/spec.md | path validation failures with deterministic error text |
| NFR-OBS-001 | SDD-C-010 | Validate summary counters + metrics extraction | scripts/lib/blueprint/upgrade_report_metrics.py; scripts/bin/blueprint/upgrade_consumer_validate.sh | tests.blueprint.test_quality_contracts.QualityContractTests.test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports | specs/2026-04-18-upgrade-validation-required-file-reconciliation/hardening_review.md | blueprint_upgrade_validate_* metrics for required-file/generated-reference counters |
| NFR-REL-001 | SDD-C-011 | Deterministic ordering in artifacts | scripts/lib/blueprint/upgrade_consumer_validate.py; scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerTests.test_dry_run_is_deterministic_and_preserves_target_content | specs/2026-04-18-upgrade-validation-required-file-reconciliation/spec.md | sorted path lists in report payloads |
| NFR-OPS-001 | SDD-C-018 | Actionable remediation + operator guidance | scripts/lib/blueprint/upgrade_consumer_validate.py; scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_fails_when_required_file_is_missing | specs/2026-04-18-upgrade-validation-required-file-reconciliation/context_pack.md | required_surfaces_at_risk and stderr remediation actions |
| AC-001 | SDD-C-012 | Missing required-file failure is enforced | scripts/lib/blueprint/upgrade_consumer_validate.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_fails_when_required_file_is_missing | specs/2026-04-18-upgrade-validation-required-file-reconciliation/pr_context.md | upgrade_validate summary.required_files_missing_count |
| AC-002 | SDD-C-012 | Repo-mode gating behavior is verified | scripts/lib/blueprint/upgrade_consumer_validate.py | tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_generated_consumer_repo_mode_excludes_source_only_required_paths; tests.blueprint.test_upgrade_consumer.UpgradeConsumerValidateTests.test_validate_template_source_repo_mode_requires_source_only_required_paths | specs/2026-04-18-upgrade-validation-required-file-reconciliation/spec.md | required_file_reconciliation.excluded_by_repo_mode |
| AC-003 | SDD-C-012 | Preflight required-surface risk reporting is verified | scripts/lib/blueprint/upgrade_preflight.py | tests.blueprint.test_upgrade_preflight.UpgradePreflightTests.test_preflight_report_groups_actions_manual_steps_and_follow_up_commands | specs/2026-04-18-upgrade-validation-required-file-reconciliation/plan.md | summary.required_surface_at_risk_count |
| AC-004 | SDD-C-012 | Validation bundle stays green for impacted scope | scripts/lib/blueprint/**; tests/blueprint/** | python3 -m unittest tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_preflight tests.blueprint.test_upgrade_consumer_wrapper tests.blueprint.test_quality_contracts | specs/2026-04-18-upgrade-validation-required-file-reconciliation/evidence_manifest.json | make infra-validate; make quality-hooks-fast |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_preflight`
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer_wrapper`
  - `python3 -m unittest tests.blueprint.test_quality_contracts`
  - `make infra-validate`
  - `make quality-hooks-fast`
  - `make quality-hooks-run`
  - `make quality-hardening-review`
  - `make docs-build`
  - `make docs-smoke`
- Result summary:
  - all listed commands passed after SDD artifact completion
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: externalize shared repo-mode required-file helper into one library function to remove duplicate logic in validate/preflight.
