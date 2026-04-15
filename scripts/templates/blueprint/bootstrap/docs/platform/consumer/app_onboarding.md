# App Onboarding Contract

This page defines the minimum contract when adding a new app or changing existing app delivery behavior in a generated consumer repository.

## Scope

Apply this contract when work touches one or more of:
- `apps/**`
- `apps/catalog/manifest.yaml`
- `apps/catalog/versions.lock`
- `infra/gitops/platform/base/apps/**`
- app-related targets in `make/platform.mk` or `make/platform/*.mk`

## Local-First Baseline

For local execution, keep the blueprint local-first baseline explicit:
- Kubernetes context policy: prefer `docker-desktop` (override with `LOCAL_KUBE_CONTEXT` only when intentional)
- Provisioning/deploy baseline: Crossplane + Helm + ArgoCD wrappers
- Runtime identity baseline: ESO + Argo repo credentials + Keycloak reconciliation

If your app onboarding deviates from this baseline, record approved rationale in `spec.md`, ADR, and `AGENTS.decisions.md`.

## Minimum Make Targets

Every app onboarding change set must keep these targets available and runnable:

| Target | Contract Purpose |
|---|---|
| `apps-bootstrap` | App bootstrap prerequisites |
| `apps-smoke` | App runtime smoke checks |
| `backend-test-unit` | Backend unit lane |
| `backend-test-integration` | Backend integration lane |
| `backend-test-contracts` | Backend contract lane |
| `backend-test-e2e` | Backend e2e lane |
| `touchpoints-test-unit` | Frontend unit lane |
| `touchpoints-test-integration` | Frontend integration lane |
| `touchpoints-test-contracts` | Frontend contract lane |
| `touchpoints-test-e2e` | Frontend e2e lane |
| `test-unit-all` | Aggregate unit lane |
| `test-integration-all` | Aggregate integration lane |
| `test-contracts-all` | Aggregate contract lane |
| `test-e2e-all-local` | Aggregate local e2e lane |
| `infra-port-forward-start` | Canonical local port-forward start wrapper |
| `infra-port-forward-stop` | Canonical local port-forward stop wrapper |
| `infra-port-forward-cleanup` | Canonical local port-forward cleanup wrapper |

## Port-Forward Wrapper Contract

Use canonical wrappers instead of ad-hoc `kubectl port-forward` commands:

```bash
PF_NAME=backend-api PF_NAMESPACE=apps PF_RESOURCE=svc/backend-api PF_LOCAL_PORT=18080 PF_REMOTE_PORT=8080 make infra-port-forward-start
make infra-port-forward-stop PF_NAME=backend-api
make infra-port-forward-cleanup
```

Optional controls:
- `PF_FORCE_KILL=true` for forced stop/cleanup
- `PF_WAIT_READY=false` to skip readiness wait on start

## App Onboarding Workflow

1. Scaffold and approve SDD artifacts first (`make spec-scaffold SPEC_SLUG=<slug>`).
2. Update app catalog contract:
   - `apps/catalog/manifest.yaml`
   - `apps/catalog/versions.lock`
3. Update runtime manifests under `infra/gitops/platform/base/apps/**`.
4. Keep minimum targets above wired in `make/platform.mk` and `make/platform/*.mk`.
5. Update docs (at least this page and `quickstart.md` when behavior changes).
6. Run canonical validation bundle:
   - `make quality-hooks-run`
   - `make infra-validate`
   - `make docs-build`
   - `make docs-smoke`
