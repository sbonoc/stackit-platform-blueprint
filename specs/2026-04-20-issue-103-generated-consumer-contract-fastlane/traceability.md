# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Repo-mode-aware fast-lane selector | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode; tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/spec.md | selector logs include `repo_mode` |
| FR-002 | SDD-C-005 | Generated-consumer skip set for template-source-only tests | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/plan.md | metric `infra_contract_test_fast_test_selection_total` with `selection=skipped_template_source_only` |
| FR-003 | SDD-C-005 | Template-source required selected-test existence gate | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/spec.md | fatal output includes missing relative test paths |
| NFR-SEC-001 | SDD-C-009 | No new secret/env requirements | scripts/bin/infra/contract_test_fast.sh | make infra-contract-test-fast | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/hardening_review.md | no secret-contract deltas |
| NFR-OBS-001 | SDD-C-010 | Deterministic selection telemetry | scripts/bin/infra/contract_test_fast.sh | make infra-contract-test-fast | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/hardening_review.md | selection metrics emitted with repo mode |
| NFR-REL-001 | SDD-C-011 | Stable selected-test ordering | scripts/bin/infra/contract_test_fast.sh | make infra-contract-test-fast | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/spec.md | deterministic argument order in lane output |
| NFR-OPS-001 | SDD-C-018 | Explicit remediation diagnostics | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/pr_context.md | fatal guidance points to missing required paths |
| AC-001 | SDD-C-012 | Template-source includes source-only tests | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/pr_context.md | lane output contains source-only test paths |
| AC-002 | SDD-C-012 | Generated-consumer excludes source-only tests | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/pr_context.md | skip log + selected shared tests |
| AC-003 | SDD-C-012 | Template-source fail-fast for missing selected test | scripts/bin/infra/contract_test_fast.sh | tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing | specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/pr_context.md | missing-path fatal diagnostics |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing -v`
  - `make infra-contract-test-fast`
  - `make infra-validate`
  - `make quality-hooks-fast`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
  - `make quality-hooks-run`
- Result summary:
  - all commands listed above passed.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: address remaining upgrade-regression items in backlog group (`#104`, `#106`, `#107`) after this repo-mode fast-lane fix.
