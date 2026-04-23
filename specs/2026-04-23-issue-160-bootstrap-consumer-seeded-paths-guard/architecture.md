# Architecture

## Context
- Work item: 2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard
- Owner: blueprint
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `ensure_infra_template_file` and `ensure_infra_rendered_file` in `scripts/bin/infra/bootstrap.sh` check for `init_managed` paths but not `consumer_seeded` paths. When a consumer replaces a blueprint placeholder manifest with a consumer-specific one and deletes the placeholder from git, bootstrap unconditionally recreates the deleted file on every fresh checkout.
- Scope boundaries: two local functions in `scripts/bin/infra/bootstrap.sh`; one new structural test assertion.
- Out of scope: changing `init_managed` behavior; adding new `consumer_seeded` declarations to the blueprint's own `contract.yaml`; documentation updates (the `consumer_seeded` path class is already documented).

## Bounded Contexts and Responsibilities
- Blueprint bootstrap context: manages infra scaffolding file lifecycle. Owns the decision of whether to create/skip a file.
- Consumer contract context: `blueprint/contract.yaml` declares which paths are consumer-owned. Read at runtime by `blueprint_path_is_consumer_seeded`.

## High-Level Component Design
- Domain layer: `blueprint_path_is_consumer_seeded` (existing in `scripts/lib/blueprint/contract_runtime.sh`) — returns truthy when a path is in `consumer_seeded_paths`.
- Application layer: `ensure_infra_template_file` and `ensure_infra_rendered_file` — add a guard block after the `init_managed` guard, before `ensure_file_from_template` / `ensure_file_from_rendered_template`.
- Infrastructure adapters: `log_info`, `log_metric` (existing shell helpers).
- Presentation/API/workflow boundaries: none.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint_path_is_consumer_seeded` (existing, no change needed).
- Downstream dependencies: none new.
- Data/API/event contracts touched: `infra_consumer_seeded_skip_count` metric added to bootstrap stdout.

## Non-Functional Architecture Notes
- Security: uses existing `blueprint_path_is_consumer_seeded` helper; no subprocess, no new env vars, no shell injection vectors.
- Observability: `infra_consumer_seeded_skip_count` metric emitted; `log_info` per skipped path.
- Reliability and rollback: revert the commit; no persistent state introduced.
- Monitoring/alerting: no new alerts needed; skip count metric is informational.

## Risks and Tradeoffs
- Risk 1: consumer miscategorizes an actually-managed path as `consumer_seeded`. Mitigation: explicit declaration is intentional and the consumer owns the decision; the existing workaround (keep file at template content) remains available.
- Tradeoff 1: structural test (text search) rather than a live bootstrap integration test. Accepted because `contract_refactor_scripts_cases.py` is the established pattern for this type of assertion; a live integration test would require a full consumer fixture.
