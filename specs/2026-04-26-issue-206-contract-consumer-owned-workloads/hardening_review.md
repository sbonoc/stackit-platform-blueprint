# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Blueprint contract (`blueprint/contract.yaml`) embedded consumer workload naming decisions (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) as blueprint requirements in `required_files` and `app_runtime_gitops_contract.required_paths_when_enabled`. This forced consumers to re-patch their `blueprint/contract.yaml` after every blueprint upgrade, creating a recurring manual tax that leaked blueprint implementation details into the consumer upgrade workflow. Fixed: 4 paths moved to `source_only_paths` and removed from `required_paths_when_enabled` in `blueprint/contract.yaml` and its bootstrap template mirror. Bootstrap template drift validated by `infra-validate`. Contract docs regenerated (`docs/reference/generated/contract_metadata.generated.md`).

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: No metrics changes. After implementation, the upgrade plan output will show `source-only / skip` for the 4 seed manifest paths (previously: potentially `update` or `create` depending on consumer state), making the behavioral boundary observable in plan JSON artifacts.
- Operational diagnostics updates: No operational runbook changes. Consumer upgrade output becomes cleaner — no false-positive create/update/delete actions for seed manifest paths.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: This change enforces the domain boundary: blueprint seeds initial consumer workload manifests at init time but does not own them thereafter. The `source_only_paths` classification is the correct mechanism for this invariant. Config-only change; no new SOLID violations introduced.
- Test-automation and pyramid checks: Tests added — T-101 (`test_seed_manifest_paths_not_in_required_files`), T-102 (`test_seed_manifest_paths_in_source_only_paths`), T-103 (`test_app_runtime_required_paths_no_hardcoded_manifest_names`), T-104 (`test_consumer_renamed_manifests_no_delete_or_create_for_seed_paths` + `test_original_seed_names_classified_as_source_only_skip`), T-106 (`test_seed_manifest_templates_exist_in_infra_bootstrap`). Two pre-existing test assertion bugs fixed in `test_optional_runtime_contract_validation.py`. All unit scope. 551 blueprint tests pass.
- Documentation/diagram/CI/skill consistency checks: ADR written — `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md` (status: approved). Mermaid diagram in architecture.md represents the contract flow. `docs/reference/generated/contract_metadata.generated.md` regenerated. `make docs-build` and `make docs-smoke` pass. No CI workflow changes required.

## Proposals Only (Not Implemented)
- none
