# Architecture

## Context
- Work item: 2026-04-22-issue-118-137-preflight-module-targets-postgres-eso-key
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Two independent contract drift issues. (1) `blueprint/modules/postgres/module.contract.yaml` lists `POSTGRES_DB` in `outputs.produced` but the ESO ExternalSecret (`infra/gitops/platform/base/security/runtime-external-secrets-core.yaml:166`) emits `POSTGRES_DB_NAME` and `scripts/lib/infra/postgres.sh` reads `POSTGRES_DB_NAME`. The module contract doc is wrong, causing silent mismatch between governance metadata and runtime behaviour. (2) `scripts/lib/blueprint/upgrade_consumer.py` detects *missing required* make targets in consumer repos but does not detect *stale references* to `infra-<module>-*` targets that were removed from `make/blueprint.generated.mk` when the operator disabled an optional module. Consumers retain CI steps or make recipes that call these targets, causing silent CI failures.
- Scope boundaries: (1) One-line key rename in module contract YAML. (2) New helper `_collect_stale_module_target_actions` in `upgrade_consumer.py`, wired into the existing plan assembly block; scoped to files covered by `BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS` and `_collect_platform_make_paths`; gated on generated-consumer repo mode.
- Out of scope: Removing the `should_skip_eso_contract_check()` local-lite workaround; runtime enforcement of module contract output key lists; scanning arbitrary files for make target references.

## Bounded Contexts and Responsibilities
- Context A (governance metadata): `blueprint/modules/postgres/module.contract.yaml` owns the authoritative description of what keys the postgres module produces. Must match the runtime ESO manifest.
- Context B (upgrade tooling): `scripts/lib/blueprint/upgrade_consumer.py` owns upgrade plan generation. Responsible for detecting consumer drift relative to blueprint state, including stale references to targets that no longer exist.

## High-Level Component Design
- Domain layer: Module contract schema (`contract_schema.py`) reads `outputs.produced`; upgrade consumer plan builder reads `make/blueprint.generated.mk` to discover active targets.
- Application layer: `upgrade_consumer.py:_collect_stale_module_target_actions` — iterates module target names known to `render_makefile.sh` per module, checks which are absent from `make/blueprint.generated.mk`, then scans CI and make reference files for any occurrence. Each hit becomes a `RequiredManualAction`.
- Infrastructure adapters: `make/blueprint.generated.mk` is the generated source of truth for active targets (produced by `make blueprint-render-makefile`). `BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS` and `_collect_platform_make_paths` define the consumer file surfaces to scan.
- Presentation/API/workflow boundaries: Output is new entries in the upgrade plan JSON `required_manual_actions` list, surfaced by `make blueprint-upgrade-consumer-preflight`.

## Integration and Dependency Edges
- Upstream dependencies: `contract_schema.py` parses `module.contract.yaml`; `render_makefile.sh` generates `make/blueprint.generated.mk`; `upgrade_consumer.py` reads both.
- Downstream dependencies: `upgrade_preflight.py` aggregates `RequiredManualAction` entries from the plan; CI and operator workflows consume preflight output.
- Data/API/event contracts touched: `blueprint/modules/postgres/module.contract.yaml` (outputs field); `upgrade_consumer.py` plan JSON schema (required_manual_actions).

## Non-Functional Architecture Notes
- Security: All file reads are in-process Python via `pathlib`; no subprocess or shell expansion; no path traversal beyond repo root.
- Observability: Each `RequiredManualAction` reason string includes the file path and stale target name so operators can locate and remove the reference.
- Reliability and rollback: Stale-reference detection reads files defensively (via existing `_read_text` which returns empty string on error); failures produce no `RequiredManualAction` entries (false-negative) rather than aborting plan generation (blast radius limited).
- Monitoring/alerting: none; this is a local developer tooling path.

## Risks and Tradeoffs
- Risk 1: `_read_text` swallowing read errors means a stale reference in an unreadable file goes undetected. Acceptable: the operator will learn about it at CI runtime anyway.
- Tradeoff 1: Scanning only bounded reference paths (not all files) means references hidden in ad-hoc scripts outside those paths are not caught. This is intentional — unlimited scanning would produce false positives and is out of scope.
