# Architecture

## Context
- Work item: 2026-04-17-prune-glob-ownership-check
- Owner: sbonoc
- Date: 2026-04-17

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: prune-glob ownership expectations are currently implicit. Contract patterns can drift from ownership documentation without a hard validation failure.
- Scope boundaries: contract schema/docs sync contract, contract validation for ownership matrix mapping, ownership matrix content, and supporting tests.
- Out of scope: runtime provisioning behavior, app delivery flows, and non-doc ownership classes.

## Bounded Contexts and Responsibilities
- Contract context: declares canonical prune-glob patterns and docs template allowlist.
- Validation context: validates that prune-glob patterns are documented in source-only ownership rows.
- Docs sync context: mirrors blueprint docs subset from contract allowlist.

## High-Level Component Design
- Domain layer: ownership policy and source-only prune semantics.
- Application layer: contract validator orchestration in `infra-validate`.
- Infrastructure adapters: markdown table parsing and filesystem checks in docs validator.
- Presentation/API/workflow boundaries: `make infra-validate` and unittest suites provide deterministic diagnostics.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` (`consumer_init` + `docs_contract`).
- Downstream dependencies: `scripts/lib/docs/sync_blueprint_template_docs.py`, `scripts/bin/blueprint/validate_contract.py`, docs/tests.
- Data/API/event contracts touched: markdown docs ownership and contract field parsing only.

## Non-Functional Architecture Notes
- Security: prune safety hardening blocks path traversal and out-of-root symlink escapes.
- Observability: validation emits explicit contract error strings for missing docs mapping.
- Reliability and rollback: checker is deterministic and fail-fast in contract validation lane.
- Monitoring/alerting: CI contract lanes detect drift before bootstrap/runtime execution.

## Risks and Tradeoffs
- Risk 1: strict string matching may require frequent docs updates when patterns evolve.
- Tradeoff 1: explicit contract-to-doc parity is preferred over implicit narrative mapping for deterministic governance.
