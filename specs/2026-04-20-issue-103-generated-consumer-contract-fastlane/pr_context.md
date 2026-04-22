# PR Context

## Summary
- Work item: `specs/2026-04-20-issue-103-generated-consumer-contract-fastlane`
- Objective: make `infra-contract-test-fast` repo-mode aware so generated-consumer repos do not require template-source-only tests, while template-source remains fail-fast.
- Scope boundaries:
  - `scripts/bin/infra/contract_test_fast.sh`
  - `tests/infra/test_tooling_contracts.py`
  - SDD/ADR/backlog/decision artifacts for Issue #103.

## Requirement Coverage
- Requirement IDs covered: `FR-001`, `FR-002`, `FR-003`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria covered: `AC-001`, `AC-002`, `AC-003`
- Contract surfaces changed:
  - [x] fast infra contract lane test selection by `repo_mode`
  - [x] deterministic missing-selected-test fail-fast diagnostics
  - [x] selection telemetry (`infra_contract_test_fast_test_selection_total`)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/infra/contract_test_fast.sh`
  - `tests/infra/test_tooling_contracts.py`
- Governance artifacts:
  - `specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/spec.md`
  - `docs/blueprint/architecture/decisions/ADR-20260420-issue-103-generated-consumer-fast-contract-repo-mode-selection.md`
  - `AGENTS.backlog.md`
  - `AGENTS.decisions.md`

## Validation Evidence
- Required commands executed:
  - `python3 -m unittest tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_skips_template_source_only_tests_in_generated_consumer_mode tests.infra.test_tooling_contracts.ToolingContractsTests.test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing -v`
  - `make infra-contract-test-fast`
  - `make infra-validate`
  - `make quality-hooks-fast`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
  - `make quality-hooks-run`
- Result summary:
  - all commands above passed.
- Artifact references:
  - `specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/evidence_manifest.json`
  - `specs/2026-04-20-issue-103-generated-consumer-contract-fastlane/traceability.md`

## Risk and Rollback
- Main risks:
  - incorrect skip scope could hide regressions.
  - repo-mode resolution drift from contract semantics.
- Rollback strategy:
  - revert `contract_test_fast.sh` selector + tooling contract tests and rerun `make infra-contract-test-fast` and `make quality-hooks-fast`.

## Deferred Proposals
- Complete the remaining generated-consumer upgrade-regression scope tracked in backlog (`#104`, `#106`, `#107`) after this mode-selection hardening lands.
