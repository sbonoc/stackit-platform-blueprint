# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (architecture)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation — Slice 1: Port-forward automation
- [ ] T-101 Source `scripts/lib/infra/port_forward.sh` in `local_workflows_smoke.sh` (after existing source calls)
- [ ] T-102 Add `start_port_forward "local-workflows-smoke" "$WORKFLOWS_LOCAL_NAMESPACE" "svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver" "$WORKFLOWS_LOCAL_AIRFLOW_PORT" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` before health-check curl
- [ ] T-103 Add `wait_for_local_port "local-workflows-smoke" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"` after start, before curl
- [ ] T-104 Add `stop_port_forward "local-workflows-smoke"` on success path (after state file write)
- [ ] T-105 Add `stop_port_forward "local-workflows-smoke"` on failure path (ERR trap or explicit call before log_fatal exits)

## Implementation — Slice 2: DAG development guidance + make target
- [ ] T-201 Add "DAG Development Setup" section with "Python Version" subsection to `docs/platform/modules/local-workflows/README.md` (3.12 vs ≥3.13 split, `uv venv --python 3.12 .venv-dags`, `uv python install 3.12` prerequisite)
- [ ] T-202 Add "Repository Structure" subsection to same section: `/dags/` convention, minimal layout example, subpath sync note, coding agent guidance
- [ ] T-203 Mirror the full "DAG Development Setup" section to `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md`
- [ ] T-204 Add `infra-local-workflows-dags-venv` target to `scripts/bin/blueprint/render_makefile.sh` (guarded by `WORKFLOWS_LOCAL_ENABLED`)

## Accessibility Testing (Non-UI spec)
- [ ] T-A01 Confirm NFR-A11Y-001 is declared as "N/A — no UI surfaces" in `spec.md` ✓

## Validation and Release Readiness
- [ ] T-301 Run `make quality-hooks-fast` — exits 0 (doc drift + infra contract tests + SDD check)
- [ ] T-302 Verify `make infra-local-workflows-smoke` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 (skip path, no port-forward started)
- [ ] T-303 Verify smoke state file on success contains `status=passed` and no PID field
- [ ] T-304 Confirm no process remains after smoke run: `pgrep -f "port-forward.*blueprint-airflow-webserver" | wc -l` = 0
- [ ] T-305 Verify `make infra-local-workflows-dags-venv` with `WORKFLOWS_LOCAL_ENABLED=false` exits 0 (skip)
- [ ] T-306 Run `make quality-hardening-review`
- [ ] T-307 Attach evidence to `traceability.md`

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified — pre-existing, no-impact
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — pre-existing, no-impact
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — pre-existing, no-impact
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — pre-existing, no-impact
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — pre-existing, no-impact
