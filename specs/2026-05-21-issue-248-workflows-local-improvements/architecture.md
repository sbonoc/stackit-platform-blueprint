# Architecture

## Context
- Work item: 2026-05-21-issue-248-workflows-local-improvements
- Owner: sbonoc
- Date: 2026-05-21

## Stack and Execution Model
- Backend stack profile: N/A — bash scripts and Markdown documentation only
- Frontend stack profile: N/A
- Test automation profile: N/A — validation via make targets; no test framework
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: (1) `make infra-local-workflows-smoke` requires the operator to manually start `kubectl port-forward -n data svc/blueprint-airflow-webserver 8080:8080` before running the target, making the smoke non-self-contained. (2) DAG authors developing locally have no guidance or tooling for targeting the Airflow runtime Python (3.12), which conflicts with the blueprint tooling requirement of ≥3.13.
- Scope boundaries: `scripts/bin/infra/local_workflows_smoke.sh` (port-forward automation); `docs/platform/modules/local-workflows/README.md` + its bootstrap template mirror (Python version doc); `scripts/bin/blueprint/render_makefile.sh` (new make target).
- Out of scope: Airflow chart upgrades, DAG linting CI, persistent port-forward make targets, any STACKIT lane changes.

## Bounded Contexts and Responsibilities
- Local-workflows infra scripts: lifecycle of the Airflow deployment on Docker Desktop Kubernetes; owns smoke test, plan, apply, deploy, destroy scripts.
- port_forward.sh library: cross-cutting concern; owns port-forward PID registry, stale pruning, readiness polling, cleanup; used by multiple infra scripts.
- Blueprint documentation: docs at `docs/platform/modules/local-workflows/README.md` and its bootstrap template mirror.

## High-Level Component Design
- Domain layer: N/A — no application domain logic; pure infrastructure scripting.
- Application layer: `local_workflows_smoke.sh` extended to source and use `port_forward.sh` via `start_port_forward` / `wait_for_local_port` / `stop_port_forward`. The Airflow webserver service reference is `svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver` (`svc/blueprint-airflow-webserver` with default helm release name), forwarded on `$WORKFLOWS_LOCAL_AIRFLOW_PORT` (default 8080).
- Infrastructure adapters: `port_forward.sh` registry at `artifacts/infra/port-forwards.registry`; `workflows_local_init_env` (sets `WORKFLOWS_LOCAL_NAMESPACE`, `WORKFLOWS_LOCAL_HELM_RELEASE`, `WORKFLOWS_LOCAL_AIRFLOW_PORT`).
- Presentation/API/workflow boundaries: New make target `infra-local-workflows-dags-venv` rendered by `render_makefile.sh`; guarded by `WORKFLOWS_LOCAL_ENABLED`.

## Integration and Dependency Edges
- Upstream dependencies: `scripts/lib/infra/port_forward.sh` (start/wait/stop API); `scripts/lib/infra/workflows_local.sh` (init_env, env vars).
- Downstream dependencies: None introduced. The smoke state file contract is unchanged.
- Data/API/event contracts touched: Make/CLI contract only — new `infra-local-workflows-dags-venv` target; `infra-local-workflows-smoke` behavior extended (no interface change, only self-contained).

## Non-Functional Architecture Notes
- Security: No changes to secrets, credentials, or auth surfaces. Port-forward is loopback-only (localhost:8080) during smoke execution.
- Observability: No new observability surfaces. The `port_forward.sh` library emits `log_info` on start/stop and `log_fatal` on failure; the smoke script's existing `log_info` / `log_fatal` calls are sufficient.
- Reliability and rollback: The `port_forward.sh` library handles stale PID pruning: if a prior port-forward registry entry exists for `local-workflows-smoke`, it is reaped before starting a new one. `stop_port_forward` is idempotent. The smoke script exits non-zero on health check failure; the port-forward is always cleaned up via the `stop_port_forward` call on both success and failure paths.
- Monitoring/alerting: N/A — no production surfaces.

## Risks and Tradeoffs
- Risk 1: If `port_forward.sh` is not sourced before `workflows_local.sh`, the `init_env` call will set env vars that `start_port_forward` depends on. Mitigation: source `port_forward.sh` after `workflows_local.sh`; `init_env` sets the vars; port-forward call uses them. Ordering must be: bootstrap → profile → state → workflows_local (init_env) → port_forward.
- Tradeoff 1: Using `port_forward.sh` library instead of inline `trap` adds a dependency on the registry file path (`artifacts/infra/port-forwards.registry`). This is acceptable because the path is stable and used by multiple other infra scripts; the benefit (stale pruning, readiness polling, dry-run) outweighs the coupling.
