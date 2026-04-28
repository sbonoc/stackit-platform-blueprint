# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0` (Q-1 resolved on PR #231 — Option A selected)
- [x] G-003 Confirm required sign-offs are approved (`Product`, `Architecture`, `Security`, `Operations`)
- [x] G-004 Confirm `Applicable Guardrail Controls` section in `spec.md` includes the `SDD-C-###` IDs declared (already populated)
- [x] G-005 Confirm `Implementation Stack Profile` section in `spec.md` is fully populated (already populated; explicit-consumer-exception fields documented)

## Implementation
- [x] T-001 Lock in Option A in `spec.md` — `Selected option: OPTION_A`, rationale, `Open questions count: 0`, `Unresolved alternatives count: 0` (Step 02 updated spec; Step 03 confirmed under SPEC_READY=true on 2026-04-28)
- [x] T-002 Apply Option A in code: add `infra/gitops/platform/base/apps/kustomization.yaml` to the `consumer_seeded` list (or new `init_force_paired` list) in `blueprint/contract.yaml`; add a new template `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` mirroring the bootstrap template; verify `seed_consumer_owned_files` in `scripts/lib/blueprint/init_repo_contract.py` reseeds it on force (no helper layer needed if the contract list approach is used).
- [x] T-003 Update blueprint docs/diagrams: ADR `Status: proposed` → `Status: approved` recorded at Step 03 (commit ea86b11). Release-notes deviation: `docs/blueprint/upgrade/release_notes.md` does not exist as a repo convention — versioning is ADR-based (consistent with PRs #226–#228). Deviation captured in `pr_context.md`; expanded force-init blast radius is documented in the ADR Consequences section instead.
- [x] T-004 Update consumer-facing docs/diagrams when contracts/behavior change — N/A under Option A; recorded in `pr_context.md` at slice 3

## Test Automation
- [x] T-101 Add unit test `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py::test_force_init_against_consumer_kustomization_passes_validate_app_descriptor` (AC-002) — RED before T-002, GREEN after (red committed in slice 1; green at slice 2)
- [x] T-102 Add contract drift test `tests/blueprint/test_contract_init_force_paired_paths_complete.py` asserting the on-disk init force-reseed scope matches the `consumer_seeded` list (AC-004)
- [ ] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists — N/A (no filter/transform changes); record N/A in `pr_context.md`
- [x] T-104 Translate the issue #230 reproducer (postcheck failure on v1.8.0-shaped consumer kustomization) into a failing automated test first — covered by T-101 (unit) and T-105 (smoke), then turned green by T-002 (red committed in slice 1)
- [x] T-105 Extend `make blueprint-template-smoke` (or `tests/blueprint/fixtures/upgrade_matrix/`) to cover the v1.8.0-state-shaped consumer kustomization scenario (FR-003) — RED before T-002, GREEN after (smoke pre-seed hook + CI lane env var landed in slice 1)

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
