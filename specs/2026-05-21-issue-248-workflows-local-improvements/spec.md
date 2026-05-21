# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-workflows-local-improvements.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: sbonoc

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-008, SDD-C-010, SDD-C-011, SDD-C-013
- Control exception rationale: No API surfaces (SDD-C-006, SDD-C-007, SDD-C-009 N/A); no UI (SDD-C-012 N/A); no pact contracts (SDD-C-014 N/A); no new service bindings (SDD-C-015 N/A); no migration (SDD-C-016 N/A); no new secrets injection (SDD-C-017 N/A); no new ESO stores (SDD-C-018 N/A); no canary/rollout (SDD-C-019 N/A); no new CRDs (SDD-C-020 N/A); no consumer-facing upgrade impact (SDD-C-021 N/A)

## Implementation Stack Profile (Normative)
- Backend stack profile: N/A — bash scripts and Markdown documentation only
- Frontend stack profile: N/A
- Test automation profile: N/A — validation via make targets; no test framework tests added
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A

## Objective
- Business outcome: Make `make infra-local-workflows-smoke` fully self-contained (no manual `kubectl port-forward` prerequisite); provide DAG authors with clear documentation and a dedicated make target for creating a Python 3.12-pinned local development venv that matches the Airflow 3.1.8 runtime.
- Success metric: Smoke target runs end-to-end without operator intervention; `make infra-local-workflows-dags-venv` provisions a `.venv-dags` at Python 3.12 in one command.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The smoke script MUST source `scripts/lib/infra/port_forward.sh` and call `start_port_forward "local-workflows-smoke" "$WORKFLOWS_LOCAL_NAMESPACE" "svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver" "$WORKFLOWS_LOCAL_AIRFLOW_PORT" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` before issuing the health-check HTTP request.
- FR-002 The smoke script MUST call `wait_for_local_port "local-workflows-smoke" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` immediately after `start_port_forward`, before the health-check `curl`, to guarantee the local port is accepting connections.
- FR-003 The smoke script MUST call `stop_port_forward "local-workflows-smoke"` on both the success and failure exit paths so no `kubectl port-forward` process spawned by the smoke remains running after the script exits.
- FR-004 `docs/platform/modules/local-workflows/README.md` MUST include a "DAG Development Setup" section containing two subsections:
  (a) **Python Version** — documents the version split (blueprint tooling ≥3.13 on host; Airflow 3.1.8 container ships Python 3.12), explains that DAG code must target Python 3.12, provides the `uv venv --python 3.12 .venv-dags` command, and notes that `uv python install 3.12` is a prerequisite if Python 3.12 is not yet available to `uv`.
  (b) **Repository Structure** — states that by default DAG Python files MUST be placed under a `/dags/` directory at the root of the DAG repository (matching `subPath: "/dags"` in `airflow.values.yaml` and the default `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH`); includes a minimal repository layout example; states that if the consumer overrides `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH`, they MUST update `subPath` in `airflow.values.yaml` to match; and explicitly addresses coding agents: when writing DAGs for this setup, place `.py` files under `dags/` at the repository root unless instructed otherwise via the configured subpath.
- FR-005 A Makefile target `infra-local-workflows-dags-venv` MUST be added via `scripts/bin/blueprint/render_makefile.sh`, calling `uv venv --python 3.12 .venv-dags` in the project root, guarded by `WORKFLOWS_LOCAL_ENABLED=true`.

### Non-Functional Requirements (Normative)
- NFR-OPS-001 The port-forward background PID MUST NOT be written to any state file. The `port_forward.sh` registry (`artifacts/infra/port-forwards.registry`) is the sole lifecycle record for the background process.
- NFR-OPS-002 The smoke script's state file contract MUST remain unchanged: on success, `write_state_file "local_workflows_smoke"` with keys `profile`, `status=passed`, `health_response`, `timestamp_utc`. No new fields for port-forward lifecycle are added.
- NFR-OPS-003 When `WORKFLOWS_LOCAL_ENABLED` is false (or unset), the smoke script MUST exit 0 immediately without starting any port-forward process.
- NFR-SEC-001 N/A — no secrets, credentials, or auth surfaces are introduced or modified by this work item.
- NFR-OBS-001 N/A — no new observability surfaces. Existing `log_info` / `log_fatal` calls in `port_forward.sh` and the smoke script provide sufficient diagnostic output.
- NFR-REL-001 N/A — the smoke target is idempotent. The `port_forward.sh` library handles stale PID pruning on next invocation.
- NFR-A11Y-001 N/A — no UI surfaces in this work item.

## Normative Option Decision
- Option A: Use the existing `port_forward.sh` library (`start_port_forward` / `wait_for_local_port` / `stop_port_forward`) in the smoke script.
- Option B: Inline a custom trap-based background `kubectl port-forward` process directly in the smoke script.
- Selected option: OPTION_A
- Rationale: The `port_forward.sh` library already provides PID registry, stale process pruning, readiness polling (configurable timeout), dry-run support, and consistent `log_info` / `log_fatal` logging. Duplicating this logic inline would violate DRY, risk divergence from the registry integration other infra scripts rely on, and add signal-handling complexity with no benefit.

## Contract Changes (Normative)
- Config/Env contract: No new env vars. Reuses `WORKFLOWS_LOCAL_NAMESPACE`, `WORKFLOWS_LOCAL_HELM_RELEASE`, `WORKFLOWS_LOCAL_AIRFLOW_PORT` already set by `workflows_local_init_env`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: New target `infra-local-workflows-dags-venv` (rendered by `render_makefile.sh`); existing `infra-local-workflows-smoke` behavior extended (self-contained port-forward).
- Docs contract: `docs/platform/modules/local-workflows/README.md` gains "DAG Development Setup" section (two subsections: Python Version, Repository Structure); bootstrap template mirrored at `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md`.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 Running `make infra-local-workflows-smoke` with `WORKFLOWS_LOCAL_ENABLED=true` and a deployed local-workflows stack succeeds without requiring a manually started `kubectl port-forward`.
- AC-002 Running `make infra-local-workflows-smoke` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 immediately and emits a skip log line; no port-forward process is started.
- AC-003 After a successful or failed smoke run, no `kubectl port-forward` process for the Airflow webserver (spawned by the smoke script) remains running. Verifiable by: `pgrep -f "port-forward.*blueprint-airflow-webserver" | wc -l` returns 0.
- AC-004 The smoke state file written on success contains `status=passed` and does not contain a `port_forward_pid` or any PID field.
- AC-005 `docs/platform/modules/local-workflows/README.md` contains a "DAG Development Setup" section with a "Python Version" subsection referencing Python 3.12, Airflow 3.1.8, and the `uv venv --python 3.12 .venv-dags` command.
- AC-006 The bootstrap template at `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md` is an exact mirror of the "DAG Development Setup" section added in AC-005 and AC-010.
- AC-010 The "DAG Development Setup" section contains a "Repository Structure" subsection that: (a) states DAG `.py` files belong under `/dags/` at the DAG repository root by default; (b) includes a minimal layout example (`dags/my_dag.py`); (c) states that `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH` and `subPath` in `airflow.values.yaml` must be kept in sync if changed; (d) addresses coding agents explicitly: place DAG files under `dags/` at the repository root unless the configured subpath differs.
- AC-007 Running `make infra-local-workflows-dags-venv` with `WORKFLOWS_LOCAL_ENABLED=true` and Python 3.12 available (via `uv`) creates a `.venv-dags` directory pinned to Python 3.12 (verifiable by `.venv-dags/bin/python --version`).
- AC-008 Running `make infra-local-workflows-dags-venv` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 with a skip log message; no venv is created.
- AC-009 `make quality-hooks-fast` exits 0 after all changes (doc drift check, infra contract tests, and SDD check all pass).

## Informative Notes (Non-Normative)
- Context: Both improvements are parked proposals promoted together from the AGENTS.backlog.md under `on-scope: workflows`. They are lightweight enough to share a single PR; neither requires a new module, new env vars, or schema changes.
- Tradeoffs: FR-003 uses the `port_forward.sh` `stop_port_forward` call rather than a raw `trap` because the library registry guarantees cleanup even if the script is re-entrant or if the PID was already reaped. The minor tradeoff is a dependency on the library's internal registry file path (`artifacts/infra/port-forwards.registry`), which is stable.
- Clarifications: The `uv venv --python 3.12` approach in FR-005 requires Python 3.12 to be installed on the host (available via `uv python install 3.12`). The make target emits a clear error if Python 3.12 is not found by `uv`.

## Explicit Exclusions
- Airflow chart upgrade or version changes (out of scope; tracked separately).
- Automated DAG linting or CI pipeline for the DAG repository (out of scope).
- Persistent port-forward (`make infra-port-forward-start` style) for Airflow webserver (out of scope; smoke is the only target that needs transient access).
