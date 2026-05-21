# ADR — Workflows Local Improvements: Port-forward Library Reuse + Python Version Split

- **Status:** proposed
- **ADR technical decision sign-off:** pending
- **Work item:** issue-248-workflows-local-improvements
- **Date:** 2026-05-21
- **Author:** sbonoc

## Context

PR #316 (local-workflows lane) parked two proposals under `on-scope: workflows`:

1. **Automate port-forward in smoke** — `make infra-local-workflows-smoke` requires the operator to manually start `kubectl port-forward -n data svc/blueprint-airflow-webserver 8080:8080` before running the target. The proposal is to embed a transient port-forward inside the smoke script so the make target is fully self-contained.

2. **Python version split** — Blueprint tooling requires Python ≥3.13 (see `pyproject.toml`). Airflow 3.1.8 ships Python 3.12 inside the Kubernetes container. DAG authors developing locally need to target Python 3.12 for type checking and local runs, not the host tooling Python. No guidance or tooling exists for this split.

Two architecture decisions must be made:

**Decision 1**: How to implement the transient port-forward in the smoke script — use the existing `port_forward.sh` library or write an inline custom `trap`-based approach?

**Decision 2**: How to surface the Python version split for DAG authors — documentation only, or documentation plus a dedicated make target?

## Decision

### Decision 1: Use `port_forward.sh` library — OPTION_A selected

**Option A (selected):** Source `scripts/lib/infra/port_forward.sh` and call `start_port_forward` / `wait_for_local_port` / `stop_port_forward` in `local_workflows_smoke.sh`. Cleanup on both success and failure paths via `stop_port_forward`.

**Option B (rejected):** Inline `kubectl port-forward &` with a custom `trap EXIT INT TERM` handler and a `wait_for_port` polling loop directly in the smoke script.

**Rationale for A:** The `port_forward.sh` library already provides:
- PID registry (`artifacts/infra/port-forwards.registry`) shared with other infra scripts.
- Stale PID pruning: if a prior invocation's port-forward process is still running, it is reaped before starting a new one.
- Readiness polling with a configurable timeout (`wait_for_local_port`).
- Dry-run support consistent with other infra scripts.
- Consistent `log_info` / `log_fatal` logging.

Writing this logic inline would duplicate all of the above, diverge from the established registry contract, and introduce signal-handling complexity with no benefit. The library is already sourced by other scripts in `scripts/bin/infra/`; sourcing it in `local_workflows_smoke.sh` is a direct analogue.

The resource reference for the port-forward is `svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver`, which resolves to `svc/blueprint-airflow-webserver` using the default Helm release name set by `workflows_local_init_env`.

### Decision 2: Documentation + make target — OPTION_A selected

**Option A (selected):** Add a "DAG Development Python Version" section to `docs/platform/modules/local-workflows/README.md` and add an `infra-local-workflows-dags-venv` target in `render_makefile.sh` that runs `uv venv --python 3.12 .venv-dags`.

**Option B (rejected):** Documentation only, no make target.

**Rationale for A:** A dedicated make target provides a single, discoverable command that sets up the correct venv without the engineer needing to remember the `--python 3.12` flag or know to use `.venv-dags` as the venv name. It surfaces naturally in `make help` output alongside other `infra-local-workflows-*` targets, making the version split visible at the right moment. The implementation cost is minimal (a few lines in `render_makefile.sh`); the discoverability benefit is high.

The target is guarded by `WORKFLOWS_LOCAL_ENABLED` to keep it consistent with all other local-workflows targets. `uv` is already a required tool in the project, so no new dependency is introduced.

## Consequences

- `scripts/bin/infra/local_workflows_smoke.sh` sources `port_forward.sh` and calls `start_port_forward` / `wait_for_local_port` / `stop_port_forward`.
- Port-forward PID is NOT written to any state file; the `port_forward.sh` registry is the sole lifecycle record.
- Smoke state file contract is unchanged: `status=passed`, `profile`, `health_response`, `timestamp_utc`.
- `docs/platform/modules/local-workflows/README.md` gains a "DAG Development Python Version" section; mirrored in the bootstrap template.
- `scripts/bin/blueprint/render_makefile.sh` gains an `infra-local-workflows-dags-venv` target (pending implementation).
- `.venv-dags` is a new conventioned directory name for DAG development venvs; should be added to `.gitignore` if not already covered.
- Engineers who don't have Python 3.12 available to `uv` must run `uv python install 3.12` first — documented in the README section.
