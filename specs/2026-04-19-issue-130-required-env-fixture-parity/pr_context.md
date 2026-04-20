# PR Context

## Summary
- Work item: `specs/2026-04-19-issue-130-required-env-fixture-parity/`
- Objective: enforce deterministic parity between optional-module `required_env` contracts and test fixture defaults in fast validation lanes.
- Scope boundaries:
  - `tests/_shared/helpers.py`
  - `tests/infra/test_optional_module_required_env_contract.py` (new)
  - `scripts/bin/infra/contract_test_fast.sh`
  - `scripts/lib/blueprint/init_repo_env.py`
  - `scripts/lib/quality/test_pyramid_contract.json`
  - SDD artifacts + ADR + governance backlog/decision updates

## Requirement Coverage
- Requirement IDs covered:
  - `FR-001`, `FR-002`, `FR-003`, `NFR-SEC-001`, `NFR-OBS-001`, `NFR-REL-001`, `NFR-OPS-001`
- Acceptance criteria covered:
  - `AC-001`, `AC-002`, `AC-003`
- Contract surfaces changed:
  - fast lane command surface (`infra-contract-test-fast`) now includes required-env parity check
  - canonical module required-env default map includes workflows `STACKIT_PROJECT_ID` + `STACKIT_REGION`

## Key Reviewer Files
- Primary files to review first:
  - `tests/infra/test_optional_module_required_env_contract.py`
  - `tests/_shared/helpers.py`
  - `scripts/lib/blueprint/init_repo_env.py`
  - `scripts/bin/infra/contract_test_fast.sh`
- High-risk files:
  - `tests/_shared/helpers.py`
  - `scripts/lib/blueprint/init_repo_env.py`

## Validation Evidence
- Required commands executed:
  - `pytest -q tests/infra/test_optional_module_required_env_contract.py`
  - `python3 -m unittest tests.blueprint.test_init_repo_env -v`
  - `make infra-contract-test-fast`
  - `make quality-hooks-fast`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
  - `make quality-hooks-run`
- Result summary:
  - all commands above passed after parity/test-pyramid fixes.
  - one additional targeted integration spot-check (`pytest -q tests/infra/test_optional_modules.py -k "test_postgres_module_flow or test_workflows_module_flow"`) reported an unrelated sandbox permission failure when writing kubeconfig (`~/.kube/stackit-stackit-dev.yaml: Operation not permitted`).
- Artifact references:
  - `specs/2026-04-19-issue-130-required-env-fixture-parity/spec.md`
  - `specs/2026-04-19-issue-130-required-env-fixture-parity/traceability.md`
  - `specs/2026-04-19-issue-130-required-env-fixture-parity/hardening_review.md`
  - `artifacts/docs/docs_build.env`
  - `artifacts/docs/docs_smoke.env`

## Risk and Rollback
- Main risks:
  - fixture helper now depends on contract loading; regressions would affect tests that call `module_flags_env`.
  - future `required_env` additions without default entries will intentionally fail fast.
- Rollback strategy:
  - revert helper/parity-test/fast-lane/default-map changes in this work item.
  - rerun `make infra-contract-test-fast` and `make quality-hooks-fast`.

## Deferred Proposals
- Extract a typed shared API in `init_repo_env` for required-env defaults + missing-default diagnostics so all fixture and init consumers use one explicit contract surface.
