# PR Context

## Summary
- Work item: 2026-04-22-issue-118-137-preflight-module-targets-postgres-eso-key
- Objective: fix `POSTGRES_DB` → `POSTGRES_DB_NAME` mismatch in postgres module contract outputs (Issue #137) and add upgrade preflight detection for stale `infra-<module>-*` make target references after a module is disabled (Issue #118).
- Scope boundaries: `blueprint/modules/postgres/module.contract.yaml`, `tests/infra/test_tooling_contracts.py`, `scripts/lib/blueprint/upgrade_consumer.py`, `tests/blueprint/test_upgrade_consumer.py`, `docs/platform/modules/postgres/README.md`, bootstrap template copy, `docs/reference/generated/contract_metadata.generated.md`, ADR.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- Contract surfaces changed: `blueprint/modules/postgres/module.contract.yaml` outputs field (governance metadata only); `make blueprint-upgrade-consumer-preflight` plan JSON gains new `RequiredManualAction` entries for stale module target references

## Key Reviewer Files
- Primary files to review first:
  - `blueprint/modules/postgres/module.contract.yaml` — one-line key rename (AC-001)
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_MODULE_MAKE_TARGETS`, `_collect_stale_module_target_actions`, `_file_content_references_make_target` (AC-003/AC-004)
  - `tests/infra/test_tooling_contracts.py` — `PostgresContractKeyParityTests` (AC-001/AC-002)
  - `tests/blueprint/test_upgrade_consumer.py` — `StaleModuleTargetDetectionTests` (AC-003/AC-004/AC-005)
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py` — plan assembly block modification; all 35 existing tests still pass

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-docs-sync-all`, `make infra-contract-test-fast`
- Result summary: all gates green; 105 contract tests passed (was 103, +2 new `PostgresContractKeyParityTests`); 35 upgrade consumer tests pass (+5 new `StaleModuleTargetDetectionTests`)
- Artifact references: `specs/2026-04-22-issue-118-137-preflight-module-targets-postgres-eso-key/traceability.md`, `hardening_review.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: `_MODULE_MAKE_TARGETS` static dict must be kept in sync with `render_makefile.sh` when new modules are added (see hardening review proposal 1).
- Rollback strategy: revert the single-line YAML key rename in `module.contract.yaml` and the `upgrade_consumer.py` additions; both changes are self-contained and revert cleanly without migration.

## Deferred Proposals
- Proposal 1 (not implemented): contract test asserting `_MODULE_MAKE_TARGETS` matches `render_makefile.sh` output per module — deferred; requires shell execution or a separate parser.
- Proposal 2 (not implemented): scan all tracked files (not just bounded reference paths) for stale module target references — deferred; would produce false positives; out of spec scope.
