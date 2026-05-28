# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Resolve Open Decisions Q-1 through Q-7 in `spec.md § Informative Notes` per the Draft PR review cycle; record the selected option + rationale for each; set `Open clarification markers count: 0` (complete — Step 02 cycle, commits `27b89e1` + `ab57634`)
- [ ] T-002 Author `docs/blueprint/architecture/decisions/ADR-issue-337-llm-model-router-policy.md` per FR-001 with `Status: approved` from inception (meta-ADR sign-off envelope per traceability Follow-up 8)
- [ ] T-003 Author `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` per FR-002 with `Status: approved` from inception
- [ ] T-004 Author `docs/blueprint/architecture/decisions/ADR-issue-337-trigger-authorization-model.md` per FR-003 with `Status: approved` from inception
- [ ] T-005 Author `docs/blueprint/architecture/decisions/ADR-issue-337-sovereignty-zdr-posture.md` per FR-004 with `Status: approved` from inception; cite #339 NFR-SEC-001 verbatim per NFR-SEC-001 (of this work item, which prohibits factory-side egress allowlist content)
- [ ] T-006 Author `docs/blueprint/architecture/decisions/ADR-issue-337-separation-of-duties-at-factory-velocity.md` per FR-005 with `Status: approved` from inception; cite #339 NFR-SEC-001 verbatim per this work item's NFR-SEC-002
- [ ] T-007 Author `docs/blueprint/architecture/decisions/ADR-issue-337-reject-rerun-cap.md` per FR-006 with `Status: approved` from inception
- [ ] T-008 Author `docs/blueprint/architecture/decisions/ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md` per FR-007 with `Status: approved` from inception; concrete ceiling values from Q-1
- [ ] T-009 Author `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` per FR-008 with `Status: approved` from inception
- [ ] T-010 Author `docs/blueprint/architecture/decisions/ADR-issue-337-triage-size-threshold.md` per FR-009 with `Status: approved` from inception; concrete thresholds from Q-2
- [ ] T-011 Author `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md` per FR-010 with `Status: approved` from inception
- [ ] T-012 Author `docs/blueprint/autonomous-factory/instrumentation-plan.md` per FR-012 + FR-013; dashboard target from Q-4; durable-bus pick from Q-5; retention from Q-4; per-`owner_team` breakdown shape per FR-012(f); source-of-truth field per metric per NFR-OBS-001
- [ ] T-013 Author `docs/blueprint/autonomous-factory/pre-factory-baselines.md` per FR-014; measurement window from Q-6; per-`owner_team` breakdown row
- [ ] T-014 Author `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` per FR-015; Markdown table; one row per ticket cycle; `### Sample Size` subsection per Q-7
- [ ] T-015 Replace `.github/CODEOWNERS` placeholder content with two-layer routing per FR-011; gate-1 four roles from Q-3; gate-2 bounded contexts from Q-3; verify zero `@your-org/...` placeholders; if Q-3 Option C, record deferred provisioning in CODEOWNERS comment block
- [ ] T-016 Update `docs/blueprint/autonomous-factory/design-contracts.md` per FR-016: populate C6 `### Blueprint instance` (Q-3 slugs + bounded-context enumeration), populate C7 `### Blueprint instance` (`stackit-managed-grafana` + Q-4 retention + Q-4 owner), resolve C7 `### Open Decisions` durable-bus pick to Q-5 value
- [ ] T-017 Update `docs/blueprint/autonomous-factory/design-contracts.md` per FR-017: extend C8 to enumerate the ten content ADRs (stability `stable` + extensibility per each FR's classification) and the three autonomous-factory documents (stability `stable` + extensibility `extensible`)
- [ ] T-018 Regenerate #339 spec's `evidence_manifest.json` SHA-256 entries for `docs/blueprint/autonomous-factory/design-contracts.md` and its bootstrap mirror
- [ ] T-019 Extend `blueprint/contract.yaml` `template_sync_allowlist` to include the three new autonomous-factory documents from T-012/T-013/T-014
- [ ] T-020 Run `python3 scripts/lib/docs/sync_blueprint_template_docs.py`; verify zero diff on re-run (AC-009)
- [ ] T-021 Create `.agents/personas/consumer/.gitkeep` per FR-018; ensure `.agents/personas/` exists
- [x] T-022 Meta-ADR `docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md` `Status: approved` + ADR technical decision sign-off: approved (Step 03 commit `715014a`); relative links to ten content ADRs and three autonomous-factory documents present (verification of link targets pending Slices 2–3 file creation in Step 05)

## Test Automation
- [ ] T-101 Add or update unit tests — N/A (governance-documentation change; no code units)
- [ ] T-102 Add or update contract tests — N/A (no API/event/Pact contracts added; FR-012 references the #339 Contract C7 schema as definition, not implementation)
- [ ] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists — N/A (no filter/transform logic)
- [ ] T-104 Translate any reproducible pre-PR smoke/`curl`/deterministic-check finding into a failing automated test first — N/A (no smoke/curl path; docs validation is `make docs-smoke`)
- [ ] T-105 Add boundary/integration tests where required — N/A (no integration boundaries introduced)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 Confirm NFR-A11Y-001 compliance scope is declared in `spec.md` — declared as `N/A — internal governance documentation. No UI surface is introduced or modified by this work item.`
- [ ] T-A02 Run axe-core WCAG 2.1 AA scan — N/A (no UI surface)
- [ ] T-A03 Verify keyboard operability — N/A (no UI surface)
- [ ] T-A04 Verify focus indicator visible on focused interactive elements — N/A (no UI surface)
- [ ] T-A05 Verify all non-text content has a programmatic label — N/A (no UI surface)

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles (`make quality-sdd-check`, `make docs-build`, `make docs-smoke`)
- [ ] T-202 Attach evidence to traceability document (`make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review` summaries in `evidence_manifest.json`)
- [ ] T-203 Confirm no stale TODOs/dead code/drift — verify zero deferred-decision placeholders outside `### Open Decisions` subsections in any new ADR or autonomous-factory document; verify no orphan ticket numbers in `Referenced by:` lines on the updated #339 design-contracts.md
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## Sign-off and Status Promotion
- [x] T-301 All four canonical sign-offs recorded on PR #345 and in `spec.md` (Step 03 commit `715014a`); meta-ADR flipped to `Status: approved` in the same commit. The ten content ADRs (T-002…T-011) are authored at Step 05 with `Status: approved` from inception under this PR's spec-level sign-off envelope — no separate status-flip pass needed

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — N/A (no app scope affected by this governance-documentation work item)
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — N/A (no app scope affected)
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — N/A (no app scope affected)
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — N/A (no app scope affected)
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — N/A (no app scope affected)
