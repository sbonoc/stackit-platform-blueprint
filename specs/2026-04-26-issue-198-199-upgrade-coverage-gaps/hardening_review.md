# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `VALIDATION_TARGETS` in `upgrade_consumer_validate.py` was missing `blueprint-template-smoke` and `infra-argocd-topology-validate` — consumer repos were not validated against these make targets after blueprint upgrades (issues #198, #199). Fixed by adding both to the tuple; regression-tested via two new unit tests.
- Finding 2: `audit_source_tree_coverage` had no `feature_gated` ownership class — `apps/catalog/manifest.yaml` and peers were wrongly flagged as uncovered source files during plan audit. Fixed by adding `feature_gated` field to `RepositoryOwnershipPathClasses` and wiring it into `all_coverage_roots`.
- Finding 3: `resolve_contract_conflict` used bare `yaml.dump` which produced indentless sequences and 80-char scalar wrapping — the written `blueprint/contract.yaml` was rejected by `parse_yaml_subset` during pipeline replay (issue #205). Fixed by introducing `_IndentedDumper` and `width=4096`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `validate_plan_uncovered_source_files` error string updated to list `feature_gated` alongside `required_files`, `init_managed`, `conditional_scaffold_paths`, `blueprint_managed_roots`, `source_only` so operators can interpret remaining warnings without reading source.
- Operational diagnostics updates: none — `blueprint-template-smoke` already emits its own diagnostics; adding it to `VALIDATION_TARGETS` means its output appears in the validation report automatically.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: dependency direction preserved (contract YAML → schema dataclass → validation logic); no circular imports introduced; `feature_gated` is a pure data field, no behaviour leakage.
- Test-automation and pyramid checks: new unit tests in `tests/blueprint/` at the lowest valid layer (no subprocess, no filesystem beyond tempdir fixtures). Pre-existing pyramid ratios unchanged.
- Documentation/diagram/CI/skill consistency checks: no docs or diagrams require update — this is internal validation tooling. Bootstrap template mirror enforced by `make infra-validate`.

## Proposals Only (Not Implemented)
- Proposal 1: Add a cross-check validator in `validate_contract.py` that asserts `feature_gated` paths are a superset of `app_catalog_scaffold_contract.required_paths_when_enabled`, so contract drift is caught statically. Deferred to a follow-up issue — not needed for correctness of this fix.
