# App Onboarding Contract

This page defines the minimum contract when adding a new app or changing existing app delivery behavior in a generated consumer repository.

## Scope

Apply this contract when work touches one or more of:
- `apps/descriptor.yaml` — canonical consumer-owned app metadata source (see App Descriptor below)
- `apps/**`
- `apps/catalog/manifest.yaml` — **deprecated generated compatibility output** (regenerated from the descriptor; do not edit by hand)
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

## App Descriptor (`apps/descriptor.yaml`)

`apps/descriptor.yaml` is the consumer-owned app/component topology contract. It declares
your apps, their components, owner team, service ports, health checks, and explicit GitOps
manifest references. Blueprint validation reads this file to verify GitOps wiring; the
catalog renderer derives `apps/catalog/manifest.yaml` from it on every `make apps-bootstrap`.

The baseline descriptor seeded by `make blueprint-init-repo` looks like:

```yaml
schemaVersion: v1
apps:
  - id: backend-api
    owner:
      team: platform
    components:
      - id: backend-api
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/backend-api-deployment.yaml
          service: infra/gitops/platform/base/apps/backend-api-service.yaml
        service:
          port: 8080
        health:
          readiness: /
```

**Schema fields**:

| Path | Required | Notes |
|---|---|---|
| `schemaVersion` | yes | Currently `v1`. |
| `apps[].id` | yes | DNS-style label (lowercase alphanumerics + hyphens). No `..`, `/`, or shell metacharacters. |
| `apps[].owner.team` | yes | Owning team name; non-empty. |
| `apps[].components[].id` | yes | DNS-style label (same rules as `apps[].id`). |
| `apps[].components[].kind` | yes | Kubernetes workload kind (e.g. `Deployment`). |
| `apps[].components[].manifests.deployment` | optional | Defaults to `infra/gitops/platform/base/apps/{component-id}-deployment.yaml` when omitted. Must live under `infra/gitops/platform/base/apps/`. |
| `apps[].components[].manifests.service` | optional | Defaults to `infra/gitops/platform/base/apps/{component-id}-service.yaml` when omitted. Same path constraint. |
| `apps[].components[].service.port` | optional | Service port number used by the catalog renderer. |
| `apps[].components[].health.*` | optional | Free-form health metadata (e.g. `readiness`, `liveness`). |

Multiple components per app are supported (e.g. an app with `api` + `worker` + `web`
components, each with its own manifests, ports, and health metadata).

**Validation**: `make infra-validate` parses the descriptor with safe YAML loading,
rejects unsafe IDs and manifest paths (NFR-SEC-001), confirms each resolved manifest
exists and is listed in `infra/gitops/platform/base/apps/kustomization.yaml`, and emits
deterministic error messages naming the descriptor app, component, and path.

**Migration for existing consumers**: if your repo lacks `apps/descriptor.yaml` when
running `make blueprint-upgrade-consumer`, the upgrade emits a starting-point descriptor
at `artifacts/blueprint/app_descriptor.suggested.yaml` derived from your current
`infra/gitops/platform/base/apps/kustomization.yaml`. Review and edit the suggested file
(set `owner.team`, adjust IDs as needed), then move it to `apps/descriptor.yaml`. The
upgrade flow does not write `apps/descriptor.yaml` automatically — adoption is explicit.

## App Onboarding Workflow

1. Scaffold and approve SDD artifacts first (`make spec-scaffold SPEC_SLUG=<slug>`).
2. Edit `apps/descriptor.yaml` to declare new apps/components, owner team, and (optionally)
   explicit manifest refs. Convention defaults under
   `infra/gitops/platform/base/apps/{component-id}-{deployment,service}.yaml` apply when
   the explicit refs are omitted.
3. Add the corresponding manifests under `infra/gitops/platform/base/apps/**` and list
   their basenames in `infra/gitops/platform/base/apps/kustomization.yaml`.
4. Run `make apps-bootstrap` — this regenerates `apps/catalog/manifest.yaml` from your
   descriptor (do not edit the catalog manifest by hand; it is a deprecated generated
   compatibility artifact).
5. Keep minimum targets above wired in `make/platform.mk` and `make/platform/*.mk`.
6. Update docs (at least this page and `quickstart.md` when behavior changes).
7. Run canonical validation bundle:
   - `make quality-hooks-run`
   - `make infra-validate`
   - `make docs-build`
   - `make docs-smoke`
