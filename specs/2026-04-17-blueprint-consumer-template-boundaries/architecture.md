# Architecture

## Context
- Work item: 2026-04-17-blueprint-consumer-template-boundaries
- Owner: sbonoc
- Date: 2026-04-17

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: generated-consumer scaffolding currently receives blueprint-maintainer artifacts (work-item history and blueprint ADR files) that belong only in the blueprint source repository.
- Scope boundaries: consumer-init contract, init runtime pruning behavior, docs template synchronization boundaries, governance docs, and validation tests.
- Out of scope: consumer-owned `docs/platform/**`, runtime infrastructure behavior, and app delivery contracts.

## Bounded Contexts and Responsibilities
- Consumer init contract context: declares initial transition behavior from `template-source` to `generated-consumer`.
- Init runtime context: applies pruning only during initial mode transition.
- Docs synchronization context: mirrors only approved consumer-facing blueprint docs into bootstrap template surface.
- Governance context: records ownership boundaries and decisions for maintainers and assistant workflows.

## High-Level Component Design
- Domain layer: repository ownership policy declared in contract and governance docs.
- Application layer: `seed_consumer_owned_files` orchestrates source-only path cleanup and initial prune rules.
- Infrastructure adapters: filesystem glob resolution/removal (`Path.glob`, `remove_path`) and docs mirror sync utilities.
- Presentation/API/workflow boundaries: make targets (`quality-docs-*`, `infra-validate`) and unittest suites report deterministic validation outcomes.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` contract fields and template contract mirror.
- Downstream dependencies: init-repo runtime, docs template sync utility, and contract-governance tests.
- Data/API/event contracts touched: file-path ownership and template mirror contracts only.

## Non-Functional Architecture Notes
- Security: prune logic is contract-bounded and repository-root scoped.
- Observability: change summary output and test assertions provide deterministic diagnostics.
- Reliability and rollback: prune executes only on first mode transition to avoid consumer data loss on subsequent runs.
- Monitoring/alerting: CI quality lanes fail fast on contract or docs-template drift.

## Risks and Tradeoffs
- Risk 1: an incorrect prune glob could remove valid consumer artifacts during initial init.
- Risk 2: docs allowlist drift can hide newly required consumer-facing blueprint docs.
- Tradeoff 1: explicit docs allowlist adds maintenance overhead but avoids seeding blueprint-maintainer-only narratives into generated repositories.
