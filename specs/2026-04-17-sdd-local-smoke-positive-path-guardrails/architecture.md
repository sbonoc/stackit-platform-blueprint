# Architecture

## Context
- Work item: 2026-04-17-sdd-local-smoke-positive-path-guardrails
- Owner: sbonoc
- Date: 2026-04-17

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: SDD templates and governance currently permit weak test evidence for filter/payload-transform behavior and do not require local positive-path smoke evidence for HTTP/filter scope before publish.
- Scope boundaries: SDD template packs, consumer-init SDD mirrors, governance/interoperability docs, control catalog, and regression tests for guardrail presence.
- Out of scope: runtime application handlers, infra provisioning logic, and endpoint business behavior implementation.

## Bounded Contexts and Responsibilities
- Template policy context: `.spec-kit/templates/{blueprint,consumer}/plan.md` and `tasks.md` define mandatory guardrails for future work items.
- Governance context: `AGENTS.md`, consumer-init `AGENTS.md.tmpl`, and governance docs define assistant-agnostic normative policy.
- Control catalog context: `.spec-kit/control-catalog.json` and rendered `.md` codify stable guardrail IDs and expected evidence.
- Sync context: docs and consumer-init template mirrors remain deterministic through existing sync scripts.

## High-Level Component Design
- Domain layer: SDD governance policy for positive-path tests and local smoke evidence.
- Application layer: quality gates consume template/governance artifacts and enforce catalog consistency.
- Infrastructure adapters: existing sync scripts (`sync_consumer_init_sdd_assets.py`, `sync_blueprint_template_docs.py`) propagate canonical sources.
- Presentation/API/workflow boundaries: Make targets (`quality-sdd-check*`, docs sync checks, infra-validate) expose deterministic validation outcomes.

## Integration and Dependency Edges
- Upstream dependencies: issue #138 requirements and AGENTS lifecycle policy.
- Downstream dependencies: future work-item specs/plans/tasks, assistant runbooks, PR review context artifacts.
- Data/API/event contracts touched: SDD template markdown contract, governance docs contract, control-catalog metadata contract.

## Non-Functional Architecture Notes
- Security: positive-path gate prevents false confidence from empty-result-only tests in filter/transform logic.
- Observability: local smoke gate mandates explicit endpoint evidence in `pr_context.md`.
- Reliability and rollback: changes are docs/template/control-only and rollback is a clean revert plus sync checks.
- Monitoring/alerting: CI SDD/docs/infra validation gates catch drift before merge.

## Risks and Tradeoffs
- Risk 1: stricter gates increase authoring effort for endpoint/filter work items.
- Tradeoff 1: higher author effort is accepted to avoid regressions that pass empty-result-only assertions and to shift discovery left.
