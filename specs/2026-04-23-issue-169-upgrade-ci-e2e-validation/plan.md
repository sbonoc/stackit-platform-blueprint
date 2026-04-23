# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Minimal new code — shell wrapper + make target entry + CI renderer extension. No new Python scripts. No new fixture files.
- Anti-abstraction gate: `ci_upgrade_validate.sh` is a thin wrapper; all business logic stays in `test_upgrade_fixture_matrix.py`. No new Python abstractions.
- Integration-first testing gate: Pre-PR finding (no dedicated upgrade CI job) translated to a structural test asserting the script and make target exist.
- Positive-path filter/transform test gate: Not applicable — no filter or payload-transform logic.
- Finding-to-test translation gate: The pre-PR finding (missing dedicated CI gate for upgrade validation) is a structural gap, not a reproducible runtime failure. The structural test (AC-006) asserts the required artifacts exist.

## Delivery Slices
1. Slice 1 — Shell script + make target: Create `ci_upgrade_validate.sh`; add `quality-ci-upgrade-validate` to `blueprint.generated.mk.tmpl` and `blueprint.generated.mk`; add structural test (T-101); run shellcheck.
2. Slice 2 — CI workflow rendering: Extend `render_ci_workflow.py` with `UPGRADE_E2E_VALIDATE_LANE` and `upgrade-e2e-validation` job; re-render `.github/workflows/ci.yml`; run `quality-ci-check-sync`.

## Change Strategy
- Migration/rollout sequence: Slice 1 then Slice 2. `quality-ci-check-sync` fails until Slice 2 is applied — run slices in order before `make quality-hooks-fast`.
- Backward compatibility policy: All existing make targets unchanged. The `.PHONY` list in `blueprint.generated.mk.tmpl` gains `quality-ci-upgrade-validate`; `blueprint.generated.mk` is regenerated to match.
- Rollback plan: Remove `quality-ci-upgrade-validate` from `blueprint.generated.mk.tmpl`, remove the `upgrade-e2e-validation` job from `render_ci_workflow.py`, re-render both outputs, delete `ci_upgrade_validate.sh`.

## Validation Strategy (Shift-Left)
- Unit checks: Structural test in `contract_refactor_scripts_cases.py` asserting script existence and make target presence.
- Contract checks: `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh`; `make quality-ci-check-sync` (CI workflow drift check).
- Integration checks: `make quality-hooks-fast` — runs shellcheck on all scripts, SDD checks, CI sync check, test pyramid.
- E2E checks: `make quality-ci-upgrade-validate` — runs the actual pytest invocation locally.

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
- App onboarding impact: no-impact — blueprint CI lane target only; no app lane behavior changes.
- Notes: `quality-ci-upgrade-validate` is a blueprint-internal CI lane target; it does not affect any consumer-facing make targets.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — the make target doc comment in `blueprint.generated.mk.tmpl` is the authoritative documentation.
- Consumer docs updates: none — no consumer-facing contract changes.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes touched.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `ci_upgrade_validate.sh` uses `start_script_metric_trap` from `bootstrap.sh` for script-level metric emission.
- Alerts/ownership: CI job failure on push to main is the primary signal; no additional alerts required.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1: `quality-ci-check-sync` fails if `render_ci_workflow.py` is updated but `.github/workflows/ci.yml` is not re-rendered → mitigation: apply Slice 2 atomically (render script update + `make quality-ci-sync` output + CI workflow) in one commit.
