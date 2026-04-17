# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep branch behavior deterministic and contract-driven.
  - Avoid duplicate policy logic across script/template/doc surfaces.
- Anti-abstraction gate:
  - Keep branch naming logic centralized in `spec_scaffold.py`.
  - Keep contract validation centralized in `check_sdd_assets.py`.
- Integration-first testing gate:
  - Validate branch behavior with focused unit tests.
  - Validate contract/template wiring with SDD quality checks.

## Delivery Slices
1. Slice 1: contract and controls
- Add branch contract schema fields and control statements (`SDD-C-020`, `SDD-C-021`).
- Synchronize control catalog, policy mapping, and consumer template mirrors.

2. Slice 2: scaffold + make integration
- Implement default dedicated-branch behavior in `spec_scaffold.py`.
- Add explicit branch override and opt-out wiring in make targets and templates.

3. Slice 3: quality enforcement + docs
- Extend `check_sdd_assets.py` branch-contract validations.
- Update governance/interoperability docs and assistant runbook references.
- Add scaffold branch tests and update quality contract metadata.

## Change Strategy
- Migration/rollout sequence:
  - Update executable contract and checker first.
  - Apply scaffold/make changes.
  - Synchronize templates/docs.
  - Execute validation bundles before opening PR.
- Backward compatibility policy:
  - Existing explicit branch workflows remain supported via `SPEC_BRANCH`.
  - Explicit bypass remains supported via `SPEC_NO_BRANCH=true` / `--no-create-branch`.
- Rollback plan:
  - Revert this work-item commit to restore previous scaffold/check behavior.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `./.venv/bin/python -m pytest -q tests/blueprint/test_spec_scaffold.py`
  - `./.venv/bin/python -m pytest -q tests/infra/test_sdd_asset_checker.py`
- Contract checks:
  - `make quality-sdd-check-all`
  - `make infra-validate`
- Integration checks:
  - `make quality-hooks-run`
- E2E checks:
  - not required for governance/contract-only scope.

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
- Notes: this work item does not modify app onboarding target semantics.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `AGENTS.md`
  - `README.md`
  - `specs/README.md`
  - `docs/blueprint/governance/spec_driven_development.md`
  - `docs/blueprint/governance/assistant_compatibility.md`
  - `CLAUDE.md`
- Consumer docs updates:
  - `scripts/templates/consumer/init/AGENTS.md.tmpl`
  - `scripts/templates/consumer/init/README.md.tmpl`
  - `scripts/templates/consumer/init/specs/README.md.tmpl`
- Mermaid diagrams updated: not required for this scope.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces:
  - scaffold emits deterministic branch status lines.
  - checker emits deterministic violations tied to branch contract keys.
- Alerts/ownership:
  - CI quality lanes fail on contract/tooling drift.
- Runbook updates:
  - `make spec-scaffold` usage now documents dedicated-branch default and explicit opt-out.

## Risks and Mitigations
- Risk 1: contributors may perceive branch auto-creation as friction.
- Mitigation 1: preserve explicit opt-out and explicit branch override while keeping default strict.
- Risk 2: contract/template/checker drift can regress in future refactors.
- Mitigation 2: enforce branch-contract parity checks in `quality-sdd-check-all`.
