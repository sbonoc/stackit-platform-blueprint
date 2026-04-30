# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: minimal change — two `?=` variable declarations, two recipe token substitutions, two help string updates, two contract test assertions; no abstractions introduced.
- Anti-abstraction gate: uses GNU Make `?=` directly — no wrapper layer or indirection beyond the variable itself.
- Integration-first testing gate: contract assertions in `test_quality_contracts.py` verify override-point variables are present in both template and rendered file before any consumer integration is possible.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic in this change.
- Finding-to-test translation gate: GNU Make override warning is not a failing automated test; fix introduces two new contract assertions (AC-005) verifying `?=` declarations are present — assertions fail before fix, pass after.

## Delivery Slices

### Slice 1 — Add contract test assertions (red phase)
Write two new assertions in `tests/blueprint/test_quality_contracts.py`:
1. `test_blueprint_generated_mk_template_exposes_override_point_variables` — asserts `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` and `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` are present in the template file.
2. `test_generated_makefile_exposes_override_point_variables` — same assertions against `make/blueprint.generated.mk`.
Both tests MUST fail before the template/generated file edits are applied.

### Slice 2 — Update template and regenerate (green phase)
1. Edit `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`:
   - Add `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` before the `spec-scaffold` target.
   - Replace `--track "$(or $(SPEC_TRACK),blueprint)"` with `--track "$(or $(SPEC_TRACK),$(SPEC_SCAFFOLD_DEFAULT_TRACK))"` in the `spec-scaffold` recipe.
   - Add `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` before the `blueprint-uplift-status` target.
   - Replace `@scripts/bin/blueprint/uplift_status.sh` with `@$(BLUEPRINT_UPLIFT_STATUS_SCRIPT)` in the `blueprint-uplift-status` recipe.
2. Run `make blueprint-render-makefile` to regenerate `make/blueprint.generated.mk`.
3. Verify the two contract tests now pass.

### Slice 3 — ADR + docs sync
1. Write `docs/blueprint/architecture/decisions/ADR-20260430-issue-241-make-override-warnings.md`.
2. Run `make quality-docs-sync-core-targets` — verify core targets doc unchanged (no new targets).
3. Run `make quality-sdd-check` and fix any remaining violations.

## Change Strategy
- Migration/rollout sequence: template edit → re-render → tests green → ADR → docs check → quality gates
- Backward compatibility policy: fully backward compatible; consumers not setting the new variables see zero behavior change
- Rollback plan: revert the two-line diff in the template and re-run `make blueprint-render-makefile`; no data migration required

## Validation Strategy (Shift-Left)
- Unit checks: `make test-unit-all` after Slice 1 (red) and Slice 2 (green) — confirms contract assertions fail then pass
- Contract checks: `make infra-contract-test-fast` — Makefile template contract tests included
- Integration checks: none required — change is limited to Makefile variable declarations and contract tests
- E2E checks: none required

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
- Notes: tooling-only change; no app delivery workflow or port-forward wrapper is affected; the required make target list is enumerated per SDD-C-015 with no-impact declaration

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR written in Slice 3; no other blueprint narrative docs change
- Consumer docs updates: none — the override-point variables are self-documenting in `make help` output via the existing target doc strings; consumer CLAUDE.md / platform.mk convention update not required by this work item
- Mermaid diagrams updated: architecture.md diagram (this file); no Docusaurus diagram update needed
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP route, query/filter, or API endpoint in scope
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-004, NFR-REL-001, NFR-OPS-001, AC-001–AC-005)
  - include key reviewer files (template diff, generated diff, test diff, ADR)
  - include validation evidence (`make test-unit-all` pass, `make infra-contract-test-fast` pass)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: not applicable
- Alerts/ownership: not applicable
- Runbook updates: none required

## Risks and Mitigations
- Risk 1: consumer sets `SPEC_SCAFFOLD_DEFAULT_TRACK` to an invalid value → `spec_scaffold.py` validates its `--track` argument and exits with a clear error message; no silent failure path introduced
- Risk 2: `make blueprint-render-makefile` produces a diff beyond the two targeted substitutions → caught immediately by contract tests and `cmp`-based freshness check in CI
