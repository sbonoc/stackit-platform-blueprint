# Hardening Review

## Repository-Wide Findings Fixed
- Added red->green regression for missing contract-required consumer-owned target detection when no known invoker path exists.
- Extended upgrade planner manual-action generation to include contract fallback dependency context and deterministic target-location guidance.
- Kept existing placeholder safeguards (`apps-ci-bootstrap-consumer`, `infra-post-deploy-consumer`) active while adding location guidance.
- Updated consumer upgrade runbook docs to explain required-target checklist behavior and remediation locations.

## Observability and Diagnostics Changes
- Manual action diagnostics now include deterministic location hints for missing required targets (`make/platform.mk` or `make/platform/*.mk`).
- Fallback `dependency_of` context now remains explicit when invoker path is unavailable: `blueprint/contract.yaml: spec.make_contract.required_targets -> <target>`.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks:
  - change remains localized to upgrade planner helper functions and preserves existing `RequiredManualAction` contract shape.
- Test-automation and pyramid checks:
  - unit-level regression first (red->green) plus existing unit suite coverage preserved.
- Documentation/diagram/CI/skill consistency checks:
  - consumer docs updated and synced to bootstrap template mirror.

## Proposals Only (Not Implemented)
- Proposal 1: add optional `suggested_target_stub` field in required manual actions for direct boilerplate generation without changing current schema consumers until explicitly approved.
