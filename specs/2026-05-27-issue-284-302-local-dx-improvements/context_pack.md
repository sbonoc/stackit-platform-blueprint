# Work Item Context Pack

## Context Snapshot
- Work item: issue-284-302-local-dx-improvements
- Track: blueprint
- Issues: #284 (ARGOCD_LOCAL_TARGET_REVISION), #302 (bootstrap.sh .env.local auto-load)
- Date: 2026-05-27

## Key Source Files

| File | Role |
|---|---|
| `scripts/lib/shell/bootstrap.sh` | Auto-load call site for `.env.local`; `load_env_file_defaults` already implemented here |
| `scripts/bin/infra/deploy.sh` | Orchestration point for local deploy; patch call goes after local kustomize apply |
| `scripts/lib/infra/tooling.sh` | `run_kubectl_with_active_access` helper used by patch logic |
| `infra/gitops/argocd/overlays/local/application-platform-local.yaml` | Manifest with hard-coded `targetRevision: main` (unchanged) |
| `.gitignore` | Add `.env.local` |
| `scripts/templates/blueprint/bootstrap/.gitignore` | Add `.env.local` (consumer repos receive on upgrade) |

## Consumer Context
- `sbonoc/dhe-marketplace` PR #71 (`local-credential-management`) — origin of both patterns: `.env.local.example` convention and `kubectl patch` after deploy. These patterns are proven in production use; this work item promotes them to the blueprint.

## Scope Guard
- Local profile only for #284. No STACKIT, CI, or prod paths are touched.
- No new make targets.
- No changes to any YAML manifest (application-platform-local.yaml stays as-is).
