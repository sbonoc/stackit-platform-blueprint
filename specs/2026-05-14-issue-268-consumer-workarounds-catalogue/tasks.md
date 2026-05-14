# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions count is `0` and all sign-offs are approved
- [x] G-003 Resolve Q-1 (apply_phase model / Stage-1c-vs-2c ordering) — Option A
- [x] G-004 Resolve Q-2 (failure policy for workaround application errors) — Option C
- [x] G-005 Resolve Q-3 (python_script security model) — Option A
- [x] G-006 Resolve Q-4 (landed_in values for v1.10.0 workarounds / next release tag) — Option A

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

## Implementation Tasks (SPEC_READY=true — implementation unlocked)

### Wave 1 (parallel — disjoint file sets)
- [ ] T-011 Slice 0: extend `bug_report.yml` with workaround section + GitHub Actions scaffolder + `workaround_report_parser.py` + tests
- [ ] T-012 Slice 1: schema + engine skeleton `upgrade_workarounds.py` (load/evaluate/dispatch/write) + `test_upgrade_workarounds.py`
- [ ] T-018 Slice 6b: `workaround_report_filer.py` + `test_workaround_report_filer.py` (NO SKILL.md)

### Wave 2 (sequential internally — one agent owns both files)
- [ ] T-013 Slice 2: `contract_merge` action kind apply + revert + idempotency tests
- [ ] T-014 Slice 3: `patch` action kind + `apply_phase` field + phase-split entry points
- [ ] T-015 Slice 4: `python_script` action kind + security isolation + tests

### Wave 3 (parallel — disjoint file sets)
- [ ] T-016 Slice 5: pipeline Stage 1c + Stage 2c wiring in `upgrade_consumer_pipeline.sh`
- [ ] T-017 Slice 6: author v1.10.0 catalogue entries in `workarounds/manifest.yaml` + `workarounds/v1.10.0/`

### Wave 4 (sequential — waits for Waves 1–3)
- [ ] T-019 Slice 7: ALL SKILL.md additions (catalogue section + filing step) + ADR finalisation

### Wave 5 (sequential — waits for Wave 4)
- [ ] T-020 Slice 8: publish artefacts (hardening_review, pr_context, traceability summary)

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — no-impact (upgrade pipeline tooling only)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — no-impact
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — no-impact
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — no-impact
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — no-impact

## Quality Gate Checks (pre-PR)
- [ ] T-021 `make blueprint-test-unit` — 0 failures
- [ ] T-022 `make quality-hooks-run QUALITY_HOOKS_FORCE_FULL=true` — all gates green
- [ ] T-023 `make quality-sdd-check` — spec validity confirmed
