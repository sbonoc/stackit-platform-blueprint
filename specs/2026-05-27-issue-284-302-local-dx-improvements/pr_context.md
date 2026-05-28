# PR Context

## Summary
- Work item: issue-284-302-local-dx-improvements
- Objective: Eliminate two local developer experience friction points: (1) ArgoCD always syncing from `main` during feature-branch development (#284), and (2) no standard gitignored file for persistent local env overrides (#302).
- Scope boundaries: Local profile only (#284). `bootstrap.sh` auto-load affects all profiles but is a no-op when `.env.local` is absent. No CI, STACKIT, or prod paths modified.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-013, NFR-SEC-001, NFR-SEC-002, NFR-OBS-001, NFR-REL-001, NFR-A11Y-001, AC-001 through AC-008
- Acceptance criteria covered: all 8 ACs

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/shell/bootstrap.sh` — one-line addition: `load_env_file_defaults "$ROOT_DIR/.env.local"`
  - `scripts/bin/infra/deploy.sh` — `patch_argocd_local_target_revision()` function + call site
  - `.gitignore` + `scripts/templates/blueprint/bootstrap/.gitignore` — `.env.local` entries
  - `scripts/templates/blueprint/bootstrap/.env.local.example` — new reference file
- High-risk files: `deploy.sh` (local profile branch only; STACKIT guard critical)

## Validation Evidence
- `python3 -m pytest tests/blueprint/test_tooling_contracts.py::LocalDxImprovementsTests -v` → 8 passed (2026-05-27)
- `python3 -m pytest tests/ -x -q` → all 538 tests passed (2026-05-27)
- `make quality-hooks-fast` → all 11/11 checks pass (2026-05-27)
- `make quality-docs-check-changed` → pass; platform seed mirrors synchronized (2026-05-27)
- Docs updated: `docs/platform/consumer/quickstart.md`, `docs/platform/consumer/first_30_minutes.md`; synced to bootstrap template mirrors via `python3 scripts/lib/docs/sync_platform_seed_docs.py`

## Deferred Proposals

- Proposal A (encrypt `.env.local` at rest via `age`/`sops`): Parked — trigger: on-scope: local-dx — adds tooling dependency for a local convenience file; gitignore enforcement mitigates commit risk; encryption is local developer responsibility.
- Proposal B (extend `ARGOCD_LOCAL_TARGET_REVISION` to patch multiple ArgoCD Applications): Parked — trigger: on-scope: gitops — only `platform-local-core` is in scope; multi-app patching requires a list-based contract.

## Risk and Rollback
- Main risks: `deploy.sh` patch inadvertently running on STACKIT profile (mitigated by `is_local_profile` guard and test T-203). `.env.local` overriding CI env vars (mitigated by shell-env-wins behavior in `load_env_file_defaults` and NFR-SEC-001 assertion).
- Rollback: Remove the `load_env_file_defaults` call from `bootstrap.sh` and the `patch_argocd_local_target_revision` call from `deploy.sh`. No state migration needed — both changes are pure behaviour additions with no persistent side effects.
