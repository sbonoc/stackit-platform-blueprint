# ADR — Local Developer Experience Improvements (Issues #284 and #302)

- **Status:** proposed
- **Work item:** issue-284-302-local-dx-improvements
- **Date:** 2026-05-27
- **Author:** sbonoc

## Context

Two independent friction points affect engineers developing features on non-main branches in a local blueprint consumer environment:

**Issue #284 — Local ArgoCD always syncs from `main`:**
`infra/gitops/argocd/overlays/local/application-platform-local.yaml` hard-codes `targetRevision: main`. During feature-branch development, the local ArgoCD Application always syncs from `main`, so in-progress changes are not visible in the local cluster until they are merged. The consumer-side workaround (a `kubectl patch` call in `provision_deploy_local_marketplace.sh` immediately after `make infra-deploy`) shows the correct pattern; it should live in the blueprint.

**Issue #302 — No standard place for persistent local env overrides:**
`load_env_file_defaults` already exists in `scripts/lib/shell/bootstrap.sh` but is never called automatically. Developers override local defaults (passwords, tokens, cluster settings) by exporting vars in their shell or manually sourcing a file before each `make` invocation. There is no standard, gitignored file that gets picked up automatically on every `make` call. The consumer-side pattern (`.env.local` auto-load in `sbonoc/dhe-marketplace` PR #71) is the correct convention and should be promoted to the blueprint.

Both changes are local-lane only, with no impact on STACKIT or CI paths.

## Decision

### Issue #284 — `ARGOCD_LOCAL_TARGET_REVISION` env var (Option A: deploy.sh runtime patch)

Two implementation options were considered:

**Option A (selected): `deploy.sh` runtime patch.** After `run_kustomize_apply "$overlay_path"` for the local profile, read `ARGOCD_LOCAL_TARGET_REVISION` (fallback: `git branch --show-current`) and `kubectl patch` the Application `platform-local-core` if the effective revision differs from `main`. No change to any YAML manifest.

**Option B (rejected): Kustomize patch overlay.** Add a `patches:` entry in `infra/gitops/argocd/overlays/local/kustomization.yaml` that reads `targetRevision` from a substituted `.env` file or generator plugin.

Option A is selected because:
- Keeps all manifests static and version-controlled without local-only substitution machinery.
- Conditional patch logic is naturally expressed in shell; `deploy.sh` already orchestrates the local deploy and has `run_kubectl_with_active_access`.
- Option B would require Kustomize `vars` (deprecated in v5) or a custom generator, adding fragility.
- Option A is consistent with the consumer-side workaround pattern already validated in production use.

Guard conditions for the patch:
- Local profile only (`is_local_profile` check).
- Skip when effective revision is `main`.
- Skip when `git branch --show-current` returns empty (detached HEAD).
- Skip when the Application does not yet exist in the cluster (`kubectl get` pre-check).

### Issue #302 — `.env.local` auto-load in `bootstrap.sh`

Add one call at the end of `scripts/lib/shell/bootstrap.sh`:

```bash
load_env_file_defaults "$ROOT_DIR/.env.local"
```

And add `.env.local` to:
- `.gitignore` (root)
- `scripts/templates/blueprint/bootstrap/.gitignore` (propagated to consumer repos on upgrade)

`load_env_file_defaults` already preserves pre-existing exports (shell env wins), returns early when the file is absent, and uses `set -a` / `set +a` around `source` so all loaded vars are exported. No new logic is required.

## Consequences

**Positive:**
- Engineers on feature branches see their changes in local ArgoCD without any manual `kubectl patch` step after `make infra-deploy`.
- Persistent local overrides (passwords, tokens) survive across shell sessions and `make` invocations without manual `source` steps.
- The `.env.local` convention is standardized and documented; consumer repos receive it on the next blueprint upgrade.

**Negative / risks:**
- The ArgoCD Application CRD in the local cluster will diverge from the manifest on disk when not on `main`. This is intentional and expected for local development.
- `.env.local` with sensitive values is gitignored but not encrypted. Engineers are responsible for not storing plaintext credentials in files synced to cloud storage. This is the same risk as any other local `.env*` file pattern; the gitignore entry is the mitigation.

## Pointers

- `scripts/bin/infra/deploy.sh` — implementation point for the `ARGOCD_LOCAL_TARGET_REVISION` patch
- `scripts/lib/shell/bootstrap.sh` — implementation point for `.env.local` auto-load
- `infra/gitops/argocd/overlays/local/application-platform-local.yaml` — manifest with hard-coded `targetRevision: main` (unchanged)
