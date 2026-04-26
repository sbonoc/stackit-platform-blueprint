# PR Context

## Summary
- Work item: 2026-04-26-issue-208-dynamic-workload-derivation
- Objective: Fix issue #208 — eliminate hardcoded blueprint seed workload manifest names from `bootstrap_infra_static_templates()` (bash) and `validate_app_runtime_conformance()` (Python). Both now derive the app manifest list at runtime from the template kustomization, so any consumer topology rename only requires updating `kustomization.yaml`.
- Scope boundaries: `scripts/bin/infra/bootstrap.sh` (Slice 3), `scripts/lib/blueprint/template_smoke_assertions.py` (Slice 2), new `tests/blueprint/test_template_smoke_assertions.py`, extended `tests/blueprint/test_quality_contracts.py`. No runtime, API, contract schema, or infra changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- Contract surfaces changed: none — no CLI, Make target, or contract schema changes

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/template_smoke_assertions.py` — `_extract_kustomization_resources()` added; `validate_app_runtime_conformance()` dynamic derivation (Slice 2)
  - `scripts/bin/infra/bootstrap.sh` — `bootstrap_infra_static_templates()` sed loop replaces 4 hardcoded calls (Slice 3)
  - `tests/blueprint/test_template_smoke_assertions.py` — 8 new unit tests (Slice 1)
  - `tests/blueprint/test_quality_contracts.py` — regression guard `test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates` (Slice 1)
- High-risk files:
  - `scripts/lib/blueprint/template_smoke_assertions.py` — ensure empty kustomization raises AssertionError (NFR-OBS-001)
  - `scripts/bin/infra/bootstrap.sh` — ensure `log_fatal` fires when template kustomization is missing

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make infra-validate`, `make quality-hardening-review`, `make docs-build`, `make docs-smoke`
- Result summary: all passed — 8 new unit tests green; `test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates` green; full test suite unaffected; `make quality-hooks-fast` passed; `make infra-validate` passed
- Artifact references: `traceability.md` (validation summary section)

## Risk and Rollback
- Main risks: (1) `sed` pattern misses resources with unusual whitespace or quoting — mitigated by template kustomization being blueprint-controlled minimal YAML; pattern tested against real file in `test_blueprint_template_kustomization_is_parseable`. (2) `_extract_kustomization_resources` returns empty list for malformed YAML — mitigated by `AssertionError` guard in `validate_app_runtime_conformance` when resources list is empty and `app_runtime_gitops_enabled=true`.
- Rollback strategy: `git revert` of the PR. No database migrations, no infra state changes, no consumer-repo changes required. Existing consumer repos continue working identically if their kustomization already lists the blueprint seed names.

## Deferred Proposals
- None.
