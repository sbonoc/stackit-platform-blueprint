# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 File the 5 child GitHub issues per FR-001: `#361.1` (dispatch + convergence + schema validator + predicate-registry mechanism), `#361.2` (C7 emitter + bus publisher + reviewer-rotation picker), `#361.3` (OpenHands API client + RabbitMQ trigger subscriber + work loop — filed after `#335` + `#336` spec-complete per Q-1 recommendation), `#361.4` (Helm chart + NetworkPolicy + ESO + ServiceAccount), `#361.5` (ux-ui-designer PERSONA.md + C3 matrix wiring + AGENTS.backlog `#369` closure). Each child issue body MUST cite this parent spec path and its boundary type per Contract C2.
- [ ] T-002 Add the `## Integration Acceptance Criteria` section to the parent `#361` issue body with the 5 cross-child checkboxes from AC-005 .. AC-009 per Contract C4.
- [ ] T-003 Mark `AGENTS.backlog.md` entry for `#369` as `incorporated: issue-361.5` once `#361.5` merges (deferred to a follow-up document-sync pass).
- [ ] T-004 No blueprint runtime code changes land in THIS work item — every code/Helm/PERSONA.md change is owned by one of the 5 children. This parent coordination work item lands only specs/, the ADR, and the GitHub issue updates listed above.

## Test Automation
- [ ] T-101 N/A at parent level — unit tests live in each child work item.
- [ ] T-102 N/A at parent level — contract tests live in each child work item.
- [ ] T-103 N/A — no filter/payload-transform routes in this work item or in any child.
- [ ] T-104 Translate any reproducible pre-PR smoke/`curl`/deterministic-check finding into a failing automated test first, then turn it green with the fix in the same child work item (or document deterministic exception in publish artifacts).
- [ ] T-105 N/A at parent level — boundary/integration tests live in each child work item (AC-005 .. AC-009 land in `#361.3` or `#361.4`).

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 is declared "N/A — headless orchestrator service with no UI surface; operator observability is via Grafana authored downstream by `#350`" in `spec.md`.
- [ ] T-A02 N/A — no UI surface; axe-core scan does not apply.
- [ ] T-A03 N/A — no interactive elements; keyboard operability does not apply.
- [ ] T-A04 N/A — no focused elements; focus indicator does not apply.
- [ ] T-A05 N/A — no non-text content; programmatic labelling does not apply.

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check` and `make quality-hardening-review` on this parent coordination spec.
- [ ] T-202 Attach the C7 lifecycle JSONL evidence to `traceability.md` once each child emits its phase-boundary events.
- [ ] T-203 Confirm no stale TODOs/dead code/drift across the parent spec + ADR.
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`).
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`).

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section.
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes.
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`.

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 N/A — `apps-bootstrap` and `apps-smoke` are not affected by this work item (platform/factory infrastructure, not an app-delivery workload); declared `App onboarding impact: no-impact` in `plan.md`.
- [ ] A-002 N/A — backend app lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are unaffected.
- [ ] A-003 N/A — frontend app lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are unaffected.
- [ ] A-004 N/A — aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are unaffected.
- [ ] A-005 N/A — port-forward operational wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are unaffected; `#361.4` adds `infra-helm-orchestrator-*` targets under the existing `infra-helm-*` family.
