# Architecture

## Context
- Work item: `2026-04-19-issue-130-required-env-fixture-parity`
- Owner: `@sbonoc`
- Date: `2026-04-19`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2` (contract parsing and fixture-hydration utilities)
- Frontend stack profile: `none (not in scope)`
- Test automation profile: `pytest + unittest contract assertions`
- Agent execution model: `single-agent deterministic execution`

## Problem Statement
- What needs to change and why:
  - optional-module `required_env` contracts evolve over time while test fixture helper defaults can drift.
  - drift currently surfaces late in heavier optional-module tests after bootstrap/preflight steps.
  - fast infra contract checks need explicit parity coverage between contract-required env vars and fixture defaults.
- Scope boundaries:
  - `tests/_shared/helpers.py`
  - new fast parity test file under `tests/infra/`
  - `scripts/bin/infra/contract_test_fast.sh`
  - SDD artifacts + backlog/decision synchronization
- Out of scope:
  - runtime optional-module provisioning behavior
  - module contract schema changes
  - app/runtime docs feature behavior updates

## Bounded Contexts and Responsibilities
- Module contract context:
  - source of truth for optional-module `required_env` entries (`blueprint/modules/*/module.contract.yaml`)
- Fixture hydration context:
  - deterministic env assembly for tests (`module_flags_env`)
- Fast validation context:
  - fail-fast parity guard in `infra-contract-test-fast`

## High-Level Component Design
- Domain layer:
  - canonical required-env contract per optional module
- Application layer:
  - `module_flags_env` derives enabled modules and resolves required env defaults via shared init-repo env resolver
- Infrastructure adapters:
  - contract loaders from `scripts/lib/blueprint/init_repo_contract.py` and module env resolver from `scripts/lib/blueprint/init_repo_env.py`
- Presentation/API/workflow boundaries:
  - deterministic contract test output in pytest failures and fast-lane script execution output

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml` optional module catalog
  - `blueprint/modules/*/module.contract.yaml` required env declarations
  - `scripts/lib/blueprint/init_repo_env.py` default catalog and resolver
- Downstream dependencies:
  - `tests/infra/test_optional_modules.py` and other tests that call `module_flags_env`
  - `make quality-hooks-fast` via `infra-contract-test-fast`
- Data/API/event contracts touched:
  - env contract only (test-fixture scope); no API/event payload changes

## Non-Functional Architecture Notes
- Security:
  - no live secret acquisition; test defaults remain deterministic placeholders or local overrides
- Observability:
  - deterministic sorted drift diagnostics in parity test assertions
- Reliability and rollback:
  - single-source resolver removes duplicated helper branches and reduces drift risk
  - rollback is revert of helper + parity test + fast-lane script changes
- Monitoring/alerting:
  - CI fast lane acts as contract-drift alert surface

## Risks and Tradeoffs
- Risk 1: helper hydration may still pass with empty defaults if resolver map regresses.
  - Mitigation: parity test asserts non-empty required values for enabled modules.
- Tradeoff 1: helper now loads contract metadata during test env assembly.
  - Mitigation: keep logic cached/deterministic and limited to test processes.
