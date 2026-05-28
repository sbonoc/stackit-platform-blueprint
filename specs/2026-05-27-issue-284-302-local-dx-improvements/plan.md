# Plan

## Work item: issue-284-302-local-dx-improvements

## Delivery Slices

### Slice 1 — `.env.local` auto-load (#302) [red → green TDD]

**Scope:** `bootstrap.sh`, both `.gitignore` files, optional `.env.local.example`.

**Failing tests first:**
- `test_bootstrap_calls_load_env_file_defaults` — assert `bootstrap.sh` contains `load_env_file_defaults "$ROOT_DIR/.env.local"`.
- `test_gitignore_contains_env_local` — assert `.gitignore` contains `.env.local`.
- `test_bootstrap_template_gitignore_contains_env_local` — assert `scripts/templates/blueprint/bootstrap/.gitignore` contains `.env.local`.

**Implementation:**
1. Add `load_env_file_defaults "$ROOT_DIR/.env.local"` at the end of `scripts/lib/shell/bootstrap.sh` (after `exec.sh` sourcing block, before `require_env_vars`).
2. Add `.env.local` line to `.gitignore`.
3. Add `.env.local` line to `scripts/templates/blueprint/bootstrap/.gitignore`.
4. Add `scripts/templates/blueprint/bootstrap/.env.local.example` with commented-out reference vars documenting the convention.

**Validation:** `python3 -m pytest tests/ -k "env_local or issue_284_302" -x -q`

---

### Slice 2 — `ARGOCD_LOCAL_TARGET_REVISION` patch in `deploy.sh` (#284) [red → green TDD]

**Scope:** `scripts/bin/infra/deploy.sh`.

**Failing tests first:**
- `test_deploy_references_argocd_local_target_revision` — assert `deploy.sh` contains `ARGOCD_LOCAL_TARGET_REVISION`.
- `test_deploy_skips_patch_on_main` — assert `deploy.sh` contains logic to skip when revision equals `main`.
- `test_deploy_patch_inside_local_profile_guard` — assert patch block is inside `is_local_profile` / local profile branch.
- `test_deploy_logs_effective_revision` — assert `deploy.sh` contains log call for the patched revision.
- `test_deploy_skips_patch_on_empty_branch` — assert `deploy.sh` handles empty-string revision guard.

**Implementation:**
1. Add `patch_argocd_local_target_revision()` function inline in `deploy.sh`:
   - Resolve: `local revision="${ARGOCD_LOCAL_TARGET_REVISION:-$(git branch --show-current)}"`.
   - Skip when `revision` is empty or equals `main`.
   - Check Application exists: `run_kubectl_with_active_access get application platform-local-core -n argocd >/dev/null 2>&1 || return 0`.
   - Patch: `run_kubectl_with_active_access patch application platform-local-core -n argocd --type=merge -p "{\"spec\":{\"source\":{\"targetRevision\":\"$revision\"}}}"`.
   - Log: `log_info "patched ArgoCD Application targetRevision=$revision"`.
2. Call `patch_argocd_local_target_revision` in the local profile block of `deploy.sh`, immediately after `run_kustomize_apply "$overlay_path"`.

**Validation:** `python3 -m pytest tests/ -k "argocd_local_target or issue_284_302" -x -q`

---

### Slice 3 — Documentation + publish artifacts

**Scope:** docs, traceability, hardening review, evidence manifest, pr_context.

1. Check `docs/platform/local-development.md` — add section for `ARGOCD_LOCAL_TARGET_REVISION` and `.env.local` if file exists; otherwise note in pr_context.md.
2. Populate `traceability.md`.
3. Populate `hardening_review.md`.
4. Populate `evidence_manifest.json` with SHA256 hashes.
5. Populate `pr_context.md`.
6. Run `make quality-hooks-fast` — all checks pass.
7. Run `python3 -m pytest tests/ -x -q` — all green.

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
- All N/A for this work item — tooling/bootstrap-only change; no app code modifications.

## Execution Notes

- Slices 1 and 2 are independent — implement concurrently.
- Slice 3 gates on both Slices 1 and 2.
- No new make targets. No consumer-visible API surface changes beyond the two new env conventions.
