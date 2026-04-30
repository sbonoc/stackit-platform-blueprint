# Tasks

## Parallel Dispatch Note (Step 05)
See `plan.md § Parallel Execution Map`. Launch **Track A** (Slice 1+2, subagent A) and **Track B** (Slice 3 docs authoring T-301/T-302/T-308, subagent B) as concurrent isolated worktrees. Merge both tracks before running T-303–T-307 in the main session.

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — pnpm lockfile pre-push hook (Issue #236)
- [ ] T-101 Write failing contract assertion `test_precommit_template_has_pnpm_lockfile_sync_hook` (red)
- [ ] T-102 Write failing contract assertion `test_precommit_template_pnpm_lockfile_sync_covers_workspace` — verifies `(^|/)package\.json$` pattern (red)
- [ ] T-103 Add `pnpm-lockfile-sync` hook block to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` (green)
- [ ] T-104 Verify both Slice 1 assertions pass (`make infra-contract-test-fast`)

## Slice 2 — Consumer quality gate extension stubs (Issue #237)
- [ ] T-201 Write failing contract assertion `test_make_template_has_quality_consumer_pre_push_stub` (red)
- [ ] T-202 Write failing contract assertion `test_make_template_has_quality_consumer_ci_stub` (red)
- [ ] T-203 Write failing contract assertion `test_quality_ci_blueprint_calls_quality_consumer_ci` (red)
- [ ] T-204 Write failing contract assertion `test_precommit_template_has_quality_consumer_pre_push_hook` (red)
- [x] T-211 Write failing contract assertion `test_agents_md_template_has_consumer_extension_targets` — verifies `quality-consumer-pre-push` and `quality-consumer-ci` in `scripts/templates/consumer/init/AGENTS.md.tmpl` (red)
- [ ] T-205 Add `quality-consumer-pre-push` and `quality-consumer-ci` stub targets to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (green)
- [ ] T-206 Add `@$(MAKE) quality-consumer-ci` as final step of `quality-ci-blueprint` in `blueprint.generated.mk.tmpl` (green)
- [ ] T-207 Add `quality-consumer-pre-push` hook to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` (green)
- [ ] T-208 Mirror all template changes to live `make/blueprint.generated.mk` (add stubs + quality-ci-blueprint extension)
- [ ] T-209 Add `quality-consumer-pre-push` and `quality-consumer-ci` to `.PHONY` list in both Makefile files
- [ ] T-210 Verify all five Slice 2 assertions pass (`make infra-contract-test-fast`)

## Slice 3 — Docs + validation
- [x] T-301 Update `docs/blueprint/governance/quality_hooks.md` — add Consumer Extension Targets section
- [x] T-302 Create `docs/platform/consumer/consumer_quality_gates.md` — consumer guide for overriding extension stubs
- [x] T-308 Update `scripts/templates/consumer/init/AGENTS.md.tmpl` — add `quality-consumer-pre-push` and `quality-consumer-ci` to quality gate section with tier placement convention (green for AC-007)
- [ ] T-303 Sync `docs/blueprint/governance/quality_hooks.md` to bootstrap template mirror (`make quality-docs-sync-blueprint-template`)
- [ ] T-304 Regenerate `core_targets.generated.md` (`make quality-docs-sync-core-targets`)
- [ ] T-305 Run `make docs-build && make docs-smoke`
- [ ] T-306 Run `make infra-contract-test-fast` — all assertions pass
- [ ] T-307 Run `make quality-hooks-fast` — all checks pass

## Accessibility Testing (Normative — N/A for non-UI specs)
- [ ] T-A01 Confirm NFR-A11Y-001 compliance scope is declared in `spec.md` (N/A — tooling and governance change; no UI components)
- [ ] T-A02 axe-core scan: N/A — no UI components
- [ ] T-A03 Keyboard operability: N/A — no interactive elements
- [ ] T-A04 Focus indicator: N/A — no interactive elements
- [ ] T-A05 Non-text content labels: N/A — no visual output

## Validation and Release Readiness
- [ ] T-401 Confirm `make infra-contract-test-fast` — all 6 new assertions + full suite pass
- [ ] T-402 Confirm `make quality-sdd-check` — PASS
- [ ] T-403 Confirm `make quality-hardening-review` — PASS
- [ ] T-404 Confirm `make quality-hooks-fast` — PASS
- [ ] T-405 Confirm `make infra-validate` — PASS (no bootstrap template drift)
- [ ] T-406 Attach evidence to traceability document

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact — unaffected by this work item)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact)
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact)
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact)
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
