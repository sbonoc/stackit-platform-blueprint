# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (architecture)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Port-forward automation
- [x] T-101 Source `scripts/lib/infra/port_forward.sh` in `local_workflows_smoke.sh` (after existing source calls)
- [x] T-102 Add `start_port_forward "local-workflows-smoke" "$WORKFLOWS_LOCAL_NAMESPACE" "svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver" "$WORKFLOWS_LOCAL_AIRFLOW_PORT" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` before health-check curl
- [x] T-103 Add `wait_for_local_port "local-workflows-smoke" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` after start, before curl
- [x] T-104 Add `stop_port_forward "local-workflows-smoke"` on success path (after state file write)
- [x] T-105 Add `stop_port_forward "local-workflows-smoke"` on failure path (ERR trap or explicit call before log_fatal exits)

## Implementation — Slice 2: DAG development guidance + make target
- [x] T-201 Add "DAG Development Setup" section with "Python Version" subsection to `docs/platform/modules/local-workflows/README.md` (3.12 vs ≥3.13 split, `uv venv --python 3.12 .venv-dags`, `uv python install 3.12` prerequisite)
- [x] T-202 Add "Repository Structure" subsection to same section: `/dags/` convention, minimal layout example, subpath sync note, coding agent guidance
- [x] T-203 Mirror the full "DAG Development Setup" section to `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md`
- [x] T-204 Add `infra-local-workflows-dags-venv` target to `scripts/bin/blueprint/render_makefile.sh` (guarded by `WORKFLOWS_LOCAL_ENABLED`)

## Accessibility Testing (Non-UI spec)
- [x] T-A01 Confirm NFR-A11Y-001 is declared as "N/A — no UI surfaces" in `spec.md` ✓

## Validation and Release Readiness
- [x] T-301 Run `make quality-hooks-fast` — exits 0 (doc drift + infra contract tests + SDD check)
- [x] T-302 Verify `make infra-local-workflows-smoke` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 (skip path, no port-forward started)
- [x] T-303 Verify smoke state file on success contains `status=passed` and no PID field — verified by static analysis: write_state_file writes only profile=, status=passed, health_response=, timestamp_utc= keys; port-forward PID is stored in registry only, never in state file
- [x] T-304 Confirm no process remains after smoke run: `pgrep -f "port-forward.*blueprint-airflow-webserver" | wc -l` = 0 — verified by static analysis: stop_port_forward is called explicitly on all exit paths (success, wait timeout, both log_fatal branches)
- [x] T-305 Verify `make infra-local-workflows-dags-venv` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 (skip)
- [x] T-306 Run `make quality-hardening-review`
- [x] T-307 Attach evidence to `traceability.md`

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified — pre-existing, no-impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — pre-existing, no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — pre-existing, no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — pre-existing, no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — pre-existing, no-impact
