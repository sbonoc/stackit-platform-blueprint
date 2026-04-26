# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Blueprint contract (`blueprint/contract.yaml`) embeds consumer workload naming decisions (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) as blueprint requirements in `required_files` and `app_runtime_gitops_contract.required_paths_when_enabled`. This forces consumers to re-patch their `blueprint/contract.yaml` after every blueprint upgrade, creating a recurring manual tax that leaks blueprint implementation details into the consumer upgrade workflow. Fixed (pending implementation) by moving the 4 paths to `source_only_paths` and removing them from `required_paths_when_enabled`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: No metrics changes. After implementation, the upgrade plan output will show `source-only / skip` for the 4 seed manifest paths (previously: potentially `update` or `create` depending on consumer state), making the behavioral boundary observable in plan JSON artifacts.
- Operational diagnostics updates: No operational runbook changes. Consumer upgrade output becomes cleaner — no false-positive create/update/delete actions for seed manifest paths.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: This spec enforces the domain boundary: blueprint seeds initial consumer workload manifests at init time but does not own them thereafter. The `source_only_paths` classification is the correct mechanism for this invariant. No code changes means no new SOLID violations.
- Test-automation and pyramid checks: The implementing work item MUST add 3 contract content regression guards and 2 upgrade planner integration tests (per plan.md Slice 2). All tests classify as unit scope.
- Documentation/diagram/CI/skill consistency checks: ADR to be written during implementation. Mermaid diagram in architecture.md represents the contract flow. No CI workflow changes required.

## Proposals Only (Not Implemented)
- none
