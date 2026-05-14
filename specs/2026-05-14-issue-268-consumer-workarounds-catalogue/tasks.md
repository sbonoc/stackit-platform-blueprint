# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions count is `0` and all sign-offs are approved
- [ ] G-003 Resolve Q-1 (apply_phase model / Stage-1c-vs-2c ordering)
- [ ] G-004 Resolve Q-2 (failure policy for workaround application errors)
- [ ] G-005 Resolve Q-3 (python_script security model)
- [ ] G-006 Resolve Q-4 (landed_in values for v1.10.0 workarounds / next release tag)

## Intake Tasks (current phase)
- [x] T-001 Scaffold spec directory and branch
- [x] T-002 Fetch and analyse issue #268 requirements
- [x] T-003 Analyse existing pipeline stages and insertion points
- [x] T-004 Populate spec.md with REQ/NFR/AC and open questions
- [x] T-005 Populate architecture.md with bounded contexts, decisions, diagrams
- [x] T-006 Populate plan.md with provisional delivery slices
- [x] T-007 Populate tasks.md, traceability.md, graph.json
- [x] T-008 Create ADR (proposed)
- [x] T-009 Run `make quality-sdd-check`
- [x] T-010 Commit and open Draft PR

## Implementation Tasks (blocked on SPEC_READY=true)
- [ ] T-011 Slice 1: schema + engine skeleton (load/evaluate/dispatch/write) + unit tests
- [ ] T-012 Slice 2: `contract_merge` action kind apply + revert + idempotency tests
- [ ] T-013 Slice 3: `patch` action kind + `apply_phase` field + phase-split entry points
- [ ] T-014 Slice 4: `python_script` action kind + security isolation + tests
- [ ] T-015 Slice 5: pipeline Stage 1c + Stage 2c wiring in `upgrade_consumer_pipeline.sh`
- [ ] T-016 Slice 6: author v1.10.0 catalogue entries (#258, #259, #260, #261)
- [ ] T-017 Slice 7: SKILL.md update + ADR finalisation
- [ ] T-018 Slice 8: publish artefacts (hardening_review, pr_context, traceability summary)

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — no-impact (upgrade pipeline tooling only)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — no-impact
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — no-impact
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — no-impact
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — no-impact

## Quality Gate Checks (pre-PR)
- [ ] T-019 `make blueprint-test-unit` — 0 failures
- [ ] T-020 `make quality-hooks-run QUALITY_HOOKS_FORCE_FULL=true` — all gates green
- [ ] T-021 `make quality-sdd-check` — spec validity confirmed
