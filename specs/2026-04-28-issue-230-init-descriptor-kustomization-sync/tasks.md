# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0` (currently 1 / 1 — Q-1 option selection is open)
- [ ] G-003 Confirm required sign-offs are approved (`Product`, `Architecture`, `Security`, `Operations`)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section in `spec.md` includes the `SDD-C-###` IDs declared (already populated)
- [ ] G-005 Confirm `Implementation Stack Profile` section in `spec.md` is fully populated (already populated; explicit-consumer-exception fields documented)

## Implementation
- [ ] T-001 Resolve Q-1 (Option A vs. Option B) and update `spec.md` — set `Selected option`, replace `Rationale`, update `Open questions count` and `Unresolved alternatives count` to `0`
- [ ] T-002 Apply selected fix in code:
  - Option A: add `infra/gitops/platform/base/apps/kustomization.yaml` to the `consumer_seeded` list (or new `init_force_paired` list) in `blueprint/contract.yaml`; add a new template `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` mirroring the bootstrap template; ensure `seed_consumer_owned_files` in `scripts/lib/blueprint/init_repo_contract.py` reseeds it on force.
  - Option B: change `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` to `apps: []`; update `docs/platform/consumer/app_onboarding.md`.
- [ ] T-003 Update blueprint docs/diagrams: `docs/blueprint/upgrade/release_notes.md` (v1.8.2 entry), promote ADR `Status: proposed` → `Status: approved`
- [ ] T-004 Update consumer-facing docs/diagrams when contracts/behavior change (Option B only — onboarding doc update; Option A — none)

## Test Automation
- [ ] T-101 Add unit test `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py::test_force_init_against_consumer_kustomization_passes_validate_app_descriptor` (AC-002) — RED before T-002, GREEN after
- [ ] T-102 Add contract drift test `tests/blueprint/test_contract_init_force_paired_paths_complete.py` asserting the on-disk init force-reseed scope matches the `consumer_seeded` list (AC-004)
- [ ] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists — N/A (no filter/transform changes); record N/A in `pr_context.md`
- [ ] T-104 Translate the issue #230 reproducer (postcheck failure on v1.8.0-shaped consumer kustomization) into a failing automated test first — covered by T-101 (unit) and T-105 (smoke), then turned green by T-002
- [ ] T-105 Extend `make blueprint-template-smoke` (or `tests/blueprint/fixtures/upgrade_matrix/`) to cover the v1.8.0-state-shaped consumer kustomization scenario (FR-003) — RED before T-002, GREEN after

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles: `make quality-sdd-check`, `make infra-validate`, `make blueprint-template-smoke`, `make quality-ci-generated-consumer-smoke`
- [ ] T-202 Attach evidence to `traceability.md` (link unit test paths, smoke fixture paths, CI lane names + run IDs)
- [ ] T-203 Confirm no stale TODOs/dead code/drift introduced by the fix (in particular: no orphaned template that points at a now-empty descriptor under Option B)
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (unit + smoke + CI lane evidence per FR-001/AC-001/AC-002/AC-003/AC-004), and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — N/A scope is blueprint init/template only; no app-onboarding surface changed
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — N/A
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — N/A
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — N/A
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — N/A
