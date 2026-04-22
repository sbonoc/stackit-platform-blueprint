# Architecture

## Context
- Work item: `2026-04-20-issue-103-generated-consumer-contract-fastlane`
- Owner: `@sbonoc`
- Date: `2026-04-20`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2`
- Frontend stack profile: `none (not in scope)`
- Test automation profile: `unittest + pytest wrapper-contract checks`
- Agent execution model: `single-agent deterministic execution`

## Problem Statement
- What needs to change and why:
  - `scripts/bin/infra/contract_test_fast.sh` always executed template-source-only tests.
  - generated-consumer upgrades can miss those source-only files and fail `infra-validate` for non-contract reasons.
  - fast-lane behavior must be deterministic by `repo_mode` while preserving fail-fast strictness in template-source mode.
- Scope boundaries:
  - `scripts/bin/infra/contract_test_fast.sh`
  - `tests/infra/test_tooling_contracts.py`
  - SDD artifacts + decision/backlog synchronization for Issue #103.
- Out of scope:
  - additive-file conflict classification changes (`#104`)
  - missing helper distribution fixes (`#106`, `#107`)
  - runtime behavior changes outside fast contract lane selection.

## Bounded Contexts and Responsibilities
- Contract-runtime mode context:
  - `blueprint/contract.yaml` (`repo_mode`, `mode_from`, `mode_to`) governs lane selection.
- Fast contract lane context:
  - chooses canonical tests and enforces path existence before execution.
- Tooling contract test context:
  - validates mode-aware selection and fail-fast behavior without requiring live pytest execution.

## High-Level Component Design
- Domain layer:
  - deterministic lane policy by repository mode.
- Application layer:
  - `contract_test_fast.sh` computes selected tests + skip set.
- Infrastructure adapters:
  - contract runtime helper (`scripts/lib/blueprint/contract_runtime.sh`) resolves active repo mode.
- Presentation/API/workflow boundaries:
  - structured shell logs/metrics communicate selected/skipped test sets and remediation paths.

## Integration and Dependency Edges
- Upstream dependencies:
  - `scripts/lib/blueprint/contract_runtime.sh`
  - `blueprint/contract.yaml`.
- Downstream dependencies:
  - `make infra-contract-test-fast`
  - `make infra-validate`
  - `make quality-hooks-fast`.
- Data/API/event contracts touched:
  - Make/script contract only; no API/event payload changes.

## Non-Functional Architecture Notes
- Security:
  - no secret handling changes; mode resolution consumes existing contract metadata.
- Observability:
  - adds deterministic test-selection metrics and explicit repo-mode skip logs.
- Reliability and rollback:
  - selected tests are path-validated before execution; rollback is revert of selector + tests.
- Monitoring/alerting:
  - CI fast-lane failure reason becomes explicit (`missing required fast contract test path(s)`).

## Risks and Tradeoffs
- Risk 1: repo-mode selector drift from contract semantics.
  - Mitigation: selection uses canonical runtime helpers (`blueprint_repo_mode*`) and dedicated tests.
- Tradeoff 1: generated-consumer lane executes fewer tests by design.
  - Mitigation: template-source remains strict and generated-consumer still runs shared infra contract tests.
