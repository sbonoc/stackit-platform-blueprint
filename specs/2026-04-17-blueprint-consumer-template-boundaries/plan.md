# Implementation Plan

## Implementation Start Gate
- Implementation tasks remain coupled to `SPEC_READY=true` and approved sign-offs in `spec.md`.
- Missing inputs block token remains defined (`BLOCKED_MISSING_INPUTS`), with zero unresolved counts recorded.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Limit scope to ownership-boundary contract, init pruning behavior, docs mirror sync logic, and direct tests.
  - Avoid new workflow wrappers or additional make targets.
- Anti-abstraction gate:
  - Reuse existing `ChangeSummary`, `remove_path`, and sync utility flow.
  - Keep pruning as a small helper in `init_repo_contract.py` instead of adding new modules.
- Integration-first testing gate:
  - Validate behavior through focused contract tests before broad make lane execution.
  - Validate docs-sync behavior with dedicated test and command checks.

## Delivery Slices
1. Slice 1: introduce contract/schema support for initial source-artifact prune globs and apply prune logic only on first repo-mode transition.
2. Slice 2: restrict blueprint docs template sync to consumer-facing allowlisted paths and prune source-only docs from template mirror.
3. Slice 3: update ownership/governance docs, add/refine tests, and complete SDD publish artifacts with validation evidence.

## Change Strategy
- Migration/rollout sequence:
  - Add contract keys in source + bootstrap mirrors.
  - Update runtime/parser/doc-sync implementations.
  - Update tests and docs, then run validation bundle.
- Backward compatibility policy:
  - Existing generated-consumer repositories remain safe because prune helper exits unless repo mode is `template-source`.
  - Existing make targets/command surfaces remain unchanged.
- Rollback plan:
  - Revert contract key and helper invocation if prune behavior is not desired.
  - Restore removed template docs files by running docs sync from reverted source state.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_blueprint_docs_template_sync_prunes_source_only_docs`
  - `python3 -m unittest tests.blueprint.test_quality_contracts.QualityContractsTests.test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode`
- Contract checks:
  - `python3 -m unittest tests.blueprint.contract_refactor_docs_cases.DocsRefactorCases.test_bootstrap_docs_templates_are_synchronized`
  - `python3 -m unittest tests.blueprint.contract_refactor_governance_structure_cases.GovernanceStructureCases.test_contract_surface_assets_targets_and_namespaces_are_present`
  - `python3 -m unittest tests.blueprint.contract_refactor_governance_init_cases.GovernanceInitRepoCases.test_blueprint_template_init_assets_exist`
- Integration checks:
  - `make quality-docs-check-blueprint-template-sync`
  - `make infra-validate`
- E2E checks:
  - Not applicable for this governance/template-boundary scope.

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
- Notes: this work item changes blueprint governance/template boundaries only and does not modify app onboarding target behavior.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/governance/ownership_matrix.md`
  - `AGENTS.md`
  - `AGENTS.decisions.md`
- Consumer docs updates:
  - bootstrap template ownership matrix mirror only.
- Mermaid diagrams updated:
  - ADR diagram and gantt are included in this work item ADR.
- Docs validation commands:
  - `make quality-docs-sync-all`
  - `make quality-docs-check-changed`
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
  - rely on existing deterministic command/test outputs and hard-fail quality gates.
- Alerts/ownership:
  - ownership boundary now explicitly documented in governance matrix and decision log.
- Runbook updates:
  - no operator runbook command changes required.

## Risks and Mitigations
- Risk 1: glob overreach in initial prune step.
- Mitigation 1: contract-bounded patterns and explicit mode gate (`repo_mode == mode_from`) with direct unit tests.
- Risk 2: docs allowlist drift hides required consumer-facing docs.
- Mitigation 2: sync script raises on missing allowlist source files and CI docs-sync checks enforce parity.

## Rollback Notes
- Revert this branch commit set to restore previous full blueprint docs template mirroring and remove prune-glob behavior.
- Re-run `make quality-docs-sync-all` after rollback to restore deleted template docs from reverted source state.
