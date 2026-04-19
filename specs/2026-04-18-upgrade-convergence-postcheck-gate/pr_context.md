# PR Context

## Summary
- Work item: `specs/2026-04-18-upgrade-convergence-postcheck-gate`
- Objective: enforce deterministic upgrade convergence by introducing reconcile bucketing across preflight/apply and a strict postcheck gate before merge.
- Scope boundaries:
  - reconcile artifact generation and schema (`upgrade_reconcile_report.json`)
  - preflight merge-risk classification enrichment from reconcile buckets
  - new postcheck command/report (`blueprint-upgrade-consumer-postcheck`)
  - wrapper metrics/logging updates and source-ref engine backward compatibility
  - contract, docs/template mirrors, skill runbooks, and upgrade test suite updates

## Requirement Coverage
- Requirement IDs covered: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria covered: `AC-001`, `AC-002`, `AC-003`, `AC-004`, `AC-005`
- Contract surfaces changed:
  - `blueprint/contract.yaml` and template counterpart (`required_files`, make targets)
  - new upgrade artifacts:
    - `artifacts/blueprint/upgrade/upgrade_reconcile_report.json`
    - `artifacts/blueprint/upgrade_postcheck.json`
  - enriched preflight artifact field: `merge_risk_classification`

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_reconcile_report.py`
  - `scripts/lib/blueprint/upgrade_consumer_postcheck.py`
  - `scripts/bin/blueprint/upgrade_consumer.sh`
  - `scripts/lib/blueprint/upgrade_preflight.py`
  - `scripts/lib/blueprint/upgrade_report_metrics.py`
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py`
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`
  - `tests/blueprint/test_upgrade_consumer.py`
  - `tests/blueprint/test_upgrade_preflight.py`
  - `tests/blueprint/test_upgrade_postcheck.py`

## Validation Evidence
- Required commands executed:
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_consumer_wrapper tests.blueprint.test_upgrade_postcheck -v`
  - `make quality-docs-sync-all`
  - `make quality-hooks-fast`
  - `make quality-hooks-run`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
- Result summary:
  - initial run reproduced three failures (merge-risk classification gap, source-ref engine arg compatibility, stale reconcile-count assertion).
  - all failures fixed in-code and full fast validation bundle is now green.
- Artifact references:
  - `artifacts/blueprint/upgrade/upgrade_reconcile_report.json`
  - `artifacts/blueprint/upgrade_preflight.json`
  - `artifacts/blueprint/upgrade_postcheck.json`
  - `docs/reference/generated/core_targets.generated.md`
  - `docs/reference/generated/contract_metadata.generated.md`

## Risk and Rollback
- Main risks:
  - stricter postcheck gating could block upgrades that previously passed with unresolved convergence states.
  - source-ref fallback behavior must remain deterministic across historical source tags.
- Rollback strategy:
  - revert upgrade reconcile/postcheck scripts + schemas + wrapper wiring + contract docs.
  - rerun `make quality-hooks-fast` and `make infra-validate` to confirm baseline restoration.

## Deferred Proposals
- Add an explicit CI lane that executes `blueprint-upgrade-consumer-postcheck` against representative generated-consumer fixtures after upgrade apply to enforce convergence policy before release tagging.
