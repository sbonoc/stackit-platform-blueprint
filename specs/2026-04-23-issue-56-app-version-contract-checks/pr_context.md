# PR Context

## Summary
- Work item: 2026-04-23-issue-56-app-version-contract-checks
- Objective: Close the silent version drift gap in `apps-audit-versions`: add catalog artifact contract checks so the audit fails when `apps/catalog/versions.lock` or `apps/catalog/manifest.yaml` are stale relative to `versions.sh`. Extend `apps-smoke` with a lock↔manifest consistency check. Expand the cached audit fingerprint to include catalog files.
- Scope boundaries: new `scripts/lib/platform/apps/version_contract_checker.py`, extended `audit_versions.sh`, `audit_versions_cached.sh`, `smoke.sh`, 22 unit tests, ADR. No new make targets. No new env vars.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: `apps_version_contract_check_total` metric added; `contract_checks` and `contract_failures` labels added to `apps_version_audit_summary_total`; `apps-smoke` behavior extended (catalog-enabled only).

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/platform/apps/version_contract_checker.py` — pure-function contract checks, `catalog-check` and `consistency` modes
  - `scripts/bin/platform/apps/audit_versions.sh` — catalog-check integration after drift loop
  - `scripts/bin/platform/apps/smoke.sh` — consistency-check integration after structural validate
- High-risk files:
  - `scripts/bin/platform/apps/audit_versions_cached.sh` — fingerprint expansion (conditional catalog file inclusion)

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/infra/test_version_contract_checker.py -v`, `make quality-hooks-fast`, `make infra-validate`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`, `SPEC_SLUG=2026-04-23-issue-56-app-version-contract-checks make quality-spec-pr-ready`
- Result summary: 22/22 tests pass; all quality gates green
- Artifact references: `specs/2026-04-23-issue-56-app-version-contract-checks/traceability.md`, `specs/2026-04-23-issue-56-app-version-contract-checks/evidence_manifest.json`

## Risk and Rollback
- Main risks: text-based manifest matching may produce false negatives if the manifest format changes (mitigated: manifest is machine-generated from a fixed template).
- Rollback strategy: revert the commit; no persistent cluster or infra state is introduced.

## Deferred Proposals
- Proposal 1 (not implemented): extend manifest checks to use PyYAML when available — deferred; text-based matching is sufficient for the fixed schema.
- Proposal 2 (not implemented): add source file checks for `pyproject.toml` / `package.json` — deferred; consumer-provided files belong in consumer-owned CI.
