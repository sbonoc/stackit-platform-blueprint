# PR Context

## Summary
- Work item: 2026-04-26-issue-198-199-upgrade-coverage-gaps
- Objective: Close four latent defects in the blueprint upgrade pipeline: (1) `blueprint-template-smoke` and `infra-argocd-topology-validate` missing from `VALIDATION_TARGETS` (issues #198, #199); (2) `apps/catalog*` paths missing from `ownership_path_classes`, causing false-positive uncovered-file audit warnings; (3) `yaml.dump` indentation defect in `resolve_contract_upgrade.py` causing `parse_yaml_subset` failures during pipeline replay (issue #205).
- Scope boundaries: Python validation logic and YAML contract files only; no runtime, API, or infra changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008
- Contract surfaces changed: `VALIDATION_TARGETS` tuple; `RepositoryOwnershipPathClasses` dataclass; `audit_source_tree_coverage` signature; `validate_plan_uncovered_source_files` error message; `blueprint/contract.yaml` `ownership_path_classes`; bootstrap template mirror; `resolve_contract_upgrade.py` yaml.dump formatter.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer_validate.py` — VALIDATION_TARGETS addition (Slice 1)
  - `scripts/lib/blueprint/contract_schema.py` — new `feature_gated` field (Slice 2)
  - `scripts/lib/blueprint/upgrade_consumer.py` — parameter addition + call site update (Slice 2)
  - `scripts/lib/blueprint/resolve_contract_upgrade.py` — `_IndentedDumper` + `width=4096` (Slice 5)
  - `blueprint/contract.yaml` — `feature_gated` YAML section (Slice 4)
- High-risk files:
  - `scripts/bin/blueprint/validate_contract.py` — ensure `feature_gated` is read without disk-presence check
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — must mirror `blueprint/contract.yaml`

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make infra-validate`, `make quality-hardening-review`, `make docs-build`, `make docs-smoke`
- Result summary: all passed — 127 unit tests green (`tests/blueprint/test_upgrade_consumer.py`: 58, `tests/blueprint/test_upgrade_pipeline.py`: 69); `make infra-validate` passed; `make quality-hardening-review` passed; `make docs-build` and `make docs-smoke` passed.
- Artifact references: `traceability.md` (validation summary section)

## Risk and Rollback
- Main risks: (1) YAML loader silently ignoring unknown key — mitigated by test asserting `len(contract.repository.feature_gated_paths) > 0` against the real contract file. (2) Bootstrap template drift — mitigated by Slice 4 explicitly mirroring and `make infra-validate` enforcing the check.
- Rollback strategy: `git revert` of the PR. No database migrations, no infra state, no consumer-repo changes. The `feature_gated` parameter defaults to `frozenset()` so any consumer that hasn't upgraded yet continues to work.

## Deferred Proposals
- Proposal 1: Add a cross-check validator that confirms `feature_gated` paths in `contract.yaml` are a superset of `app_catalog_scaffold_contract.required_paths_when_enabled` — Parked: `app_catalog_scaffold_contract.required_paths_when_enabled` does not exist as a formal data structure; implementing the check now would require either a meaningless hardcoded list or unplanned scope to formalize the catalog scaffold contract. Trigger: `on-scope: blueprint` — surfaces when blueprint contract formalization work is next touched.
