# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `_classify_entries()` in `upgrade_consumer.py` treated `infra/gitops/platform/base/apps/` as fully blueprint-managed, causing consumer workload manifests to be enqueued for `OPERATION_DELETE` when absent in the blueprint source with `allow_delete=True`. Fixed by adding a domain-boundary predicate guard before the delete branch.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: No metrics or tracing changes. The existing plan output `action` and `ownership` fields now carry a new value `consumer-owned-workload` for affected paths, which is visible in `artifacts/blueprint/upgrade_plan.json`.
- Operational diagnostics updates: Operators running `blueprint-upgrade` with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true` will see `action=skip` entries for consumer workload manifests instead of `action=update/operation=delete`. The `reason` field distinguishes these from other skip classes.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Single responsibility maintained — `_is_consumer_owned_workload()` is a pure predicate with a single concern. The domain boundary between blueprint-owned and consumer-owned files is now explicit in code rather than implicit by omission. No circular dependencies introduced.
- Test-automation and pyramid checks: 6 new unit tests added. All classified as unit scope in `test_pyramid_contract.json` (tests are in `test_upgrade_consumer.py`, already classified). Pre-existing 105 tests pass unchanged.
- Documentation/diagram/CI/skill consistency checks: ADR written. Architecture Mermaid diagram in `architecture.md` reflects the updated classification flow. No CI workflow changes. No skill runbook changes required.

## Proposals Only (Not Implemented)
- none
