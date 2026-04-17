# Architecture

## Context
- Work item: `2026-04-17-sdd-strict-default-branching`
- Owner: `sbonoc`
- Date: `2026-04-17`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2`
- Frontend stack profile: `vue_router_pinia_onyx`
- Test automation profile: `pytest_vitest_playwright_pact`
- Agent execution model: `specialized-subagents-isolated-worktrees`

## Problem Statement
- What needs to change and why: assistant workflows were not consistently enforcing SDD as default and new work items were not guaranteed to start on dedicated branches.
- Scope boundaries: governance/contract, scaffolding workflow, quality checks, templates, and interoperability documentation.
- Out of scope: runtime module behavior, infrastructure provisioning behavior, and generated-consumer business logic.

## Bounded Contexts and Responsibilities
- Governance contract context: defines normative SDD lifecycle and branch contract in `blueprint/contract.yaml`.
- Work-item scaffolding context: creates deterministic SDD artifacts and dedicated branch state in `spec_scaffold.py` + make target wiring.
- Validation context: enforces contract-to-implementation parity in `check_sdd_assets.py`.
- Documentation context: keeps Codex/Claude interoperability and consumer template mirrors aligned.

## High-Level Component Design
- Domain layer: SDD governance semantics captured in executable contract fields (`spec_driven_development_contract`).
- Application layer: scaffold orchestration translates contract defaults into CLI behavior (`--branch`, `--no-create-branch`).
- Infrastructure adapters: git branch discovery/create/checkout commands and make passthrough variables.
- Presentation/API/workflow boundaries: human-facing workflow commands (`make spec-scaffold`, `make quality-sdd-check-all`) and assistant runbooks.

## Integration and Dependency Edges
- Upstream dependencies: git CLI, repository branch naming contract, control catalog, SDD template packs.
- Downstream dependencies: consumer bootstrap templates, assistant interoperability docs, SDD quality gates.
- Data/API/event contracts touched:
  - `blueprint/contract.yaml` `spec.spec_driven_development_contract.branch_contract`
  - SDD controls `SDD-C-020` and `SDD-C-021`
  - `spec-scaffold` make target contract (`SPEC_BRANCH`, `SPEC_NO_BRANCH`)

## Non-Functional Architecture Notes
- Security: bypassing dedicated-branch auto-creation requires an explicit opt-out flag; no implicit privilege escalation added.
- Observability: scaffold and checker emit deterministic, grep-friendly messages for operator diagnostics.
- Reliability and rollback: behavior remains deterministic under contract; rollback is a single-PR revert.
- Monitoring/alerting: CI quality gates (`quality-sdd-check-all`, `infra-validate`, `quality-hooks-run`) provide enforcement signals.

## Risks and Tradeoffs
- Risk 1: stricter defaults can increase perceived workflow friction.
- Mitigation 1: explicit override paths remain available (`SPEC_BRANCH`, `SPEC_NO_BRANCH=true`) with documented intent.
- Tradeoff 1: stronger guardrails reduce ambiguity and prevent silent policy drift.
