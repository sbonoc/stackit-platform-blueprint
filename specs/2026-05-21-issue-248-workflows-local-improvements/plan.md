# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two discrete changes: (1) smoke port-forward automation, (2) Python version guidance + make target. No shared abstraction layer needed.
- Anti-abstraction gate: Reuse `port_forward.sh` library directly; no wrapper added. New make target uses `uv venv --python 3.12` directly; no helper function.
- Integration-first testing gate: No new automated test framework tests. Validation is via make quality gates and manual smoke with a running stack. No reproducible pre-PR smoke finding to translate; this work item IS the fix for a manual-step requirement.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: N/A — no pre-PR smoke finding to translate into a failing automated test; the port-forward requirement itself is the fix.

## Delivery Slices

1. **Slice 1 — Port-forward automation in smoke script**
   - Source `port_forward.sh` in `local_workflows_smoke.sh`.
   - Call `start_port_forward` + `wait_for_local_port` before health-check curl.
   - Call `stop_port_forward` on exit (success and failure paths).
   - Verify: `make infra-local-workflows-smoke` passes without manual port-forward; `pgrep -f "port-forward.*blueprint-airflow-webserver"` returns empty after run.

2. **Slice 2 — DAG development guidance + make target**
   - Add "DAG Development Setup" section to `docs/platform/modules/local-workflows/README.md` with two subsections: (a) Python Version — 3.12 vs ≥3.13 split, `uv venv --python 3.12 .venv-dags`; (b) Repository Structure — `/dags/` convention, layout example, subpath sync note, coding agent guidance.
   - Mirror the full section to `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md`.
   - Add `infra-local-workflows-dags-venv` target to `scripts/bin/blueprint/render_makefile.sh`.
   - Verify: `make infra-local-workflows-dags-venv` creates `.venv-dags` at Python 3.12; `make quality-hooks-fast` exits 0.

## Change Strategy
- Migration/rollout sequence: Slices are independent; order does not matter. Slice 1 first since it was the higher-priority parked proposal.
- Backward compatibility policy: Fully backward-compatible. Smoke script interface and state file contract are unchanged. New make target is additive.
- Rollback plan: Revert `local_workflows_smoke.sh` to remove the three port-forward calls. Remove `infra-local-workflows-dags-venv` from `render_makefile.sh`. Revert README and template changes. No state file migration required.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no unit test framework applicable to bash scripts.
- Contract checks: `make quality-hooks-fast` (infra contract tests, doc drift, SDD check).
- Integration checks: `make infra-local-workflows-smoke` with `WORKFLOWS_LOCAL_ENABLED=false` (exit 0 skip); with a running stack and `WORKFLOWS_LOCAL_ENABLED=true` (smoke passes).
- E2E checks: N/A — no E2E framework for this work item.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: This work item adds no new app-level targets. `infra-local-workflows-dags-venv` is a developer convenience target, not an onboarding requirement. All required minimum targets above are pre-existing.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/local-workflows/README.md` — "DAG Development Setup" section (Python Version + Repository Structure subsections).
- Consumer docs updates: Bootstrap template mirrored at `scripts/templates/blueprint/bootstrap/docs/platform/modules/local-workflows/README.md`.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter changes.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: No changes to observability surfaces.
- Alerts/ownership: N/A.
- Runbook updates: README updated (part of this work item).

## Risks and Mitigations
- Risk 1: `uv python install 3.12` may be needed on developer machines where Python 3.12 is not already available to uv. Mitigation: README section documents this requirement explicitly.
- Risk 2: Source order in `local_workflows_smoke.sh` — `port_forward.sh` must be sourced after `bootstrap.sh` sets `ROOT_DIR`. Mitigation: source immediately after existing `source` calls, before `start_script_metric_trap`.
