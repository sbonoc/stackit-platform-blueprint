# PR Context

## Summary
- Work item: `2026-04-18-upgrade-validation-required-file-reconciliation`
- Objective: enforce deterministic repo-mode required-file reconciliation and coupled generated-reference validation for consumer upgrade flows.
- Scope boundaries:
  - validate script/schema/metrics/wrapper wiring
  - preflight required-surface risk enrichment
  - fixture-backed tests for generated-consumer/template-source behavior

## Requirement Coverage
- Requirement IDs covered: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria covered: `AC-001`, `AC-002`, `AC-003`, `AC-004`
- Contract surfaces changed:
  - `scripts/lib/blueprint/schemas/upgrade_validate.schema.json`
  - `artifacts/blueprint/upgrade_validate.json` payload structure
  - `artifacts/blueprint/upgrade/required_files_status.json` artifact
  - `artifacts/blueprint/upgrade_preflight.json` required-surface reconciliation section

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer_validate.py`
  - `scripts/lib/blueprint/upgrade_preflight.py`
  - `scripts/lib/blueprint/schemas/upgrade_validate.schema.json`
- High-risk files:
  - `tests/blueprint/test_upgrade_consumer.py`
  - `tests/blueprint/test_upgrade_preflight.py`
  - `scripts/bin/blueprint/upgrade_consumer_validate.sh`
  - `scripts/lib/blueprint/upgrade_report_metrics.py`

## Validation Evidence
- Required commands executed:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer tests.blueprint.test_upgrade_preflight`
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer_wrapper`
  - `python3 -m unittest tests.blueprint.test_quality_contracts`
  - `make infra-validate`
  - `make quality-hooks-fast`
  - `make quality-hooks-run`
  - `make quality-hardening-review`
  - `make docs-build`
  - `make docs-smoke`
- Result summary: all commands above passed.
- Artifact references:
  - `artifacts/blueprint/upgrade_validate.json`
  - `artifacts/blueprint/upgrade/required_files_status.json`
  - `artifacts/blueprint/upgrade_preflight.json`

## Risk and Rollback
- Main risks:
  - stricter required-file reconciliation can fail legacy/minimal fixtures unless repo-mode-aware filtering is correct
  - schema/report consumers must tolerate newly required validate fields
- Rollback strategy:
  - revert changed validate/preflight/metrics/schema/test files
  - rerun `make infra-validate` and `make quality-hooks-fast`

## Deferred Proposals
- Extract repo-mode required-file filtering into a shared helper used by `validate_contract`, `upgrade_consumer_validate`, and `upgrade_preflight`.
