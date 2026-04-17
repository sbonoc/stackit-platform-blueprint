# Implementation Plan

## Implementation Start Gate
- Implementation is allowed with `SPEC_READY=true` and all sign-offs approved in `spec.md`.
- Blocker token remains defined but not present in active implementation-ready artifacts.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Reuse existing docs validator delegation path in `validate_contract.py`.
  - Keep checker scope limited to prune-glob -> source-only ownership matrix mapping.
- Anti-abstraction gate:
  - Use lightweight markdown table row parsing in existing docs validator module.
  - Avoid introducing new tooling or parser dependencies.
- Integration-first testing gate:
  - Add targeted validator and regression tests before broad lane runs.

## Delivery Slices
1. Slice 1: move blueprint docs allowlist source fully into contract and keep docs sync utility contract-driven.
2. Slice 2: add prune-glob ownership-matrix validator and wire into `infra-validate`.
3. Slice 3: update ownership matrix exact pattern docs and tests/SDD evidence artifacts.

## Change Strategy
- Migration/rollout sequence:
  - update contract/schema and docs sync utility.
  - add validation delegate + hook into `validate_contract.py`.
  - sync docs template mirror and update tests.
- Backward compatibility policy:
  - no new make targets; existing validation command surfaces remain stable.
- Rollback plan:
  - revert new validator and contract/docs edits, then rerun docs sync.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows`
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks`
- Contract checks:
  - `python3 -m unittest tests.blueprint.contract_refactor_docs_cases.DocsRefactorCases.test_bootstrap_docs_templates_are_synchronized`
  - `python3 -m unittest tests.blueprint.contract_refactor_governance_init_cases.GovernanceInitRepoCases.test_blueprint_template_init_assets_exist`
- Integration checks:
  - `make quality-docs-check-blueprint-template-sync`
  - `make infra-validate`
- E2E checks:
  - not applicable for this contract/docs-only governance scope.

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
- App onboarding impact: no-impact
- Notes: this change is governance/docs validation only.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/governance/ownership_matrix.md`
  - `AGENTS.decisions.md`
- Consumer docs updates:
  - bootstrap mirror ownership matrix and assistant compatibility docs parity.
- Mermaid diagrams updated:
  - captured in work-item ADR.
- Docs validation commands:
  - `make quality-docs-check-blueprint-template-sync`
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces:
  - explicit validator error messages for missing ownership matrix pattern mappings.
- Alerts/ownership:
  - contract lane failures indicate governance drift ownership.
- Runbook updates:
  - no new operational runbook commands required.

## Risks and Mitigations
- Risk 1: false negatives if ownership matrix structure diverges from expected markdown row format.
- Mitigation 1: keep checker logic minimal and assert source-only rows exist.
- Risk 2: docs/contract drift during future pattern updates.
- Mitigation 2: enforce through contract test assertions and infra-validate gate.

## Rollback Notes
- Revert this PR commit set and run `python3 scripts/lib/docs/sync_blueprint_template_docs.py` to restore mirror.
- Re-run `make infra-validate` to confirm rollback clears added checker path.
