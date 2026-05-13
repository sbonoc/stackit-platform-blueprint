# PR Context

## Summary
- Work item: 2026-05-13-issue-270-test-ownership-contract
- Objective: Relocate blueprint-author tests from `tests/infra/` to `tests/blueprint/` so they are no longer delivered to consumer repos via the upgrade resolver's 3-way merge, eliminating false-positive test failures in consumer repos caused by missing `blueprint/modules/` artefacts.
- Scope boundaries: Test file layout under `tests/infra/` and `tests/blueprint/`; `spec.repository.required_files` in `blueprint/contract.yaml` and its bootstrap template mirror; `contract_test_fast.sh` path references; `test_pyramid_contract.json` registrations; `ownership_matrix.md` taxonomy documentation. No runtime provisioning, HTTP routes, or consumer-visible behaviour changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-REL-001, NFR-REL-002, NFR-A11Y-001
- Acceptance criteria covered: AC-001 (blueprint-author tests not in required_files), AC-002 (consumer-runtime tests remain in tests/infra/), AC-003 (contract assertion enforces taxonomy at commit time), AC-004 (required_files count reduced 16 → 12), AC-005 (infra-contract-test-fast still passes)
- Contract surfaces changed: `spec.repository.required_files` in `blueprint/contract.yaml` — 4 entries removed (tests/infra/test_async_message_contracts.py, tests/infra/test_optional_module_required_env_contract.py, tests/infra/test_python_helper_extractions.py, tests/infra/test_root_dir_resolution.py)

## Key Reviewer Files
- Primary files to review first:
  - `tests/blueprint/test_quality_contracts.py` — new `TestOwnershipContractTests` class (FR-005 contract assertion)
  - `blueprint/contract.yaml` — 4 entries removed from `required_files`
  - `tests/blueprint/test_tooling_contracts.py` — new file: blueprint-author classes split from `tests/infra/test_tooling_contracts.py`
  - `tests/infra/test_tooling_contracts.py` — trimmed to 5 consumer-runtime classes only
- High-risk files:
  - `scripts/bin/infra/contract_test_fast.sh` — path references updated for 2 relocated tests
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — bootstrap mirror, same 4 removals applied
  - `scripts/lib/quality/test_pyramid_contract.json` — 5 new unit-scope registrations added

## Validation Evidence
- Required commands executed: pytest (blueprint + infra), make infra-contract-test-fast, make infra-validate, make quality-docs-check-changed, make docs-build, make docs-smoke, make quality-hardening-review, make quality-hooks-fast — all PASS
- Result summary: All validation gates PASS. `required_files` reduced from 16 to 12 entries. `infra-contract-test-fast` passes 68 tests including relocated paths. Test pyramid within bounds (unit 96.70%, integration 2.48%, e2e 0.83%).
- Artifact references: `specs/2026-05-13-issue-270-test-ownership-contract/evidence_manifest.json`

## Risk and Rollback
- Main risks: Consumer repos with stale copies of relocated files will retain them — they may produce import errors if they reference `blueprint/modules/` content that doesn't exist in generated repos, but they were already failing for this reason (the bug being fixed). No new failures introduced.
- Rollback strategy: Revert the 4 `required_files` removals in `blueprint/contract.yaml` and its bootstrap mirror; move the 4 blueprint-author test files back to `tests/infra/`; restore original `tests/infra/test_tooling_contracts.py`; delete `tests/blueprint/test_tooling_contracts.py`; revert `contract_test_fast.sh` path entries; remove 5 entries from `test_pyramid_contract.json`.

## Deferred Proposals
- Active cleanup of stale blueprint-author test copies from existing consumer repos (delete-on-upgrade): Parked — trigger: on-scope: blueprint — no active consumer complaint; D-3 in architecture.md documents the conscious deferral. Tracked in AGENTS.backlog.md as `proposal(issue-270-test-ownership-contract)`.
