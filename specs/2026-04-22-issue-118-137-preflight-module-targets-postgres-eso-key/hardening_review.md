# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1 (Issue #137): `blueprint/modules/postgres/module.contract.yaml` `spec.outputs.produced` listed `POSTGRES_DB` instead of `POSTGRES_DB_NAME`. The ESO ExternalSecret (`runtime-external-secrets-core.yaml:166`) emits `secretKey: POSTGRES_DB_NAME` and `postgres.sh` reads `POSTGRES_DB_NAME`. The module contract governance metadata was silently wrong. Fixed by renaming the key; `PostgresContractKeyParityTests` added to prevent recurrence.
- Finding 2 (Issue #118): `upgrade_consumer.py` detected missing required make targets but did not detect consumer CI or make files referencing `infra-<module>-*` targets absent from `make/blueprint.generated.mk` after a module was disabled. Consumers could silently retain stale CI steps after a module disable. Fixed by adding `_collect_stale_module_target_actions`; covered by `StaleModuleTargetDetectionTests`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new metrics; stale-reference `RequiredManualAction` entries are surfaced in the upgrade plan JSON consumed by the existing preflight reporting path.
- Operational diagnostics updates: each stale-reference action includes the file path and target name in `reason`, giving operators precise cleanup instructions.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: `_collect_stale_module_target_actions` follows the Single Responsibility pattern of existing peer helpers; `_MODULE_MAKE_TARGETS` is a pure constant, not a hidden side effect; `_file_content_references_make_target` is a pure predicate.
- Test-automation and pyramid checks: 7 new tests added (2 contract parity + 5 stale-reference unit); pyramid ratios unaffected; all tests are deterministic and run without external dependencies.
- Documentation/diagram/CI/skill consistency checks: ADR created; postgres module docs synced via `make quality-docs-sync-all`; no diagram or CI workflow changes needed.

## Proposals Only (Not Implemented)
- Proposal 1: Add a contract test asserting `_MODULE_MAKE_TARGETS` in `upgrade_consumer.py` is a subset of targets produced by `render_makefile.sh` for each module, so the static dict cannot silently drift when a new module is added. Deferred — requires either shell execution or a separate parser; acceptable risk given the static dict and `render_makefile.sh` are in the same repo and change together.
- Proposal 2: Extend stale-reference scanning to all files under the consumer's tracked repository (not just the bounded reference paths). Deferred — would produce false positives from unrelated scripts and documentation; out of scope per spec FR-003.
