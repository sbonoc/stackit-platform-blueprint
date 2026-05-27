# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## App Onboarding Minimum Targets (Normative)

- [x] A-001 `apps-bootstrap` — N/A: tooling-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: tooling-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: no new port-forward targets

## Slice 1 — `.env.local` auto-load (#302)

### Tests (write failing first)
- [x] T-101 Write `test_bootstrap_calls_load_env_file_defaults` — assert `scripts/lib/shell/bootstrap.sh` contains `load_env_file_defaults "$ROOT_DIR/.env.local"`
- [x] T-102 Write `test_gitignore_contains_env_local` — assert `.gitignore` contains `.env.local`
- [x] T-103 Write `test_bootstrap_template_gitignore_contains_env_local` — assert `scripts/templates/blueprint/bootstrap/.gitignore` contains `.env.local`

### Implementation
- [x] T-104 Add `load_env_file_defaults "$ROOT_DIR/.env.local"` to `scripts/lib/shell/bootstrap.sh` (after `exec.sh` sourcing, before `require_env_vars`)
- [x] T-105 Add `.env.local` to root `.gitignore`
- [x] T-106 Add `.env.local` to `scripts/templates/blueprint/bootstrap/.gitignore`
- [x] T-107 Add `scripts/templates/blueprint/bootstrap/.env.local.example` with commented-out reference variables

### Turn green
- [x] T-108 Run `python3 -m pytest tests/ -k "env_local or issue_284_302" -x -q` — all pass

## Slice 2 — `ARGOCD_LOCAL_TARGET_REVISION` patch (#284)

### Tests (write failing first)
- [x] T-201 Write `test_deploy_references_argocd_local_target_revision` — assert `deploy.sh` contains `ARGOCD_LOCAL_TARGET_REVISION`
- [x] T-202 Write `test_deploy_skips_patch_on_main` — assert `deploy.sh` contains skip guard when revision equals `main`
- [x] T-203 Write `test_deploy_patch_inside_local_profile_guard` — assert patch logic is inside local profile branch
- [x] T-204 Write `test_deploy_logs_effective_revision` — assert `deploy.sh` contains a `log_info` call referencing `targetRevision`
- [x] T-205 Write `test_deploy_skips_patch_on_empty_branch` — assert `deploy.sh` guards against empty revision string

### Implementation
- [x] T-206 Add `patch_argocd_local_target_revision()` function to `scripts/bin/infra/deploy.sh` with full guard logic (empty revision, `main`, Application existence check)
- [x] T-207 Call `patch_argocd_local_target_revision` in the local profile block of `deploy.sh`, after `run_kustomize_apply "$overlay_path"`

### Turn green
- [x] T-208 Run `python3 -m pytest tests/ -k "argocd_local_target or issue_284_302" -x -q` — all pass

## Slice 3 — Documentation + publish artifacts

- [ ] T-301 Check `docs/platform/local-development.md` — add `ARGOCD_LOCAL_TARGET_REVISION` and `.env.local` sections if file exists
- [ ] T-302 Populate `traceability.md` — map all FR/NFR/AC to implementation and test evidence
- [ ] T-303 Populate `hardening_review.md` with NFR-SEC-001 and NFR-SEC-002 findings
- [ ] T-304 Populate `evidence_manifest.json` with SHA256 hashes
- [ ] T-305 Populate `pr_context.md` with key reviewer files, validation evidence, risk/rollback
- [ ] T-306 Run `make quality-hooks-fast` — all 11 checks pass
- [ ] T-307 Run `python3 -m pytest tests/ -x -q` — all green (≥ 8 new assertions)

## Publish Gate
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`
