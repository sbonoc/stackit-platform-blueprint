# Hardening Review

## Repository-Wide Findings Fixed
- None pre-implementation. Post-implementation: confirm no dead code introduced and no stale TODOs remain.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `validate_plan_uncovered_source_files` error string updated to list `feature_gated` alongside `required_files`, `init_managed`, `conditional_scaffold_paths`, `blueprint_managed_roots`, `source_only` so operators can interpret remaining warnings without reading source.
- Operational diagnostics updates: none — `blueprint-template-smoke` already emits its own diagnostics; adding it to `VALIDATION_TARGETS` means its output appears in the validation report automatically.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: dependency direction preserved (contract YAML → schema dataclass → validation logic); no circular imports introduced; `feature_gated` is a pure data field, no behaviour leakage.
- Test-automation and pyramid checks: new unit tests in `tests/blueprint/` at the lowest valid layer (no subprocess, no filesystem beyond tempdir fixtures). Pre-existing pyramid ratios unchanged.
- Documentation/diagram/CI/skill consistency checks: no docs or diagrams require update — this is internal validation tooling. Bootstrap template mirror enforced by `make infra-validate`.

## Proposals Only (Not Implemented)
- Proposal 1: Add a cross-check validator in `validate_contract.py` that asserts `feature_gated` paths are a superset of `app_catalog_scaffold_contract.required_paths_when_enabled`, so contract drift is caught statically. Deferred to a follow-up issue — not needed for correctness of this fix.
