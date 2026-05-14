# ADR — ArgoCD health=N/A fix: override ignoreResourceUpdates.all in local Helm values

## Status

proposed

## Context

After a clean local install (`make infra-post-deploy-consumer`), all 33+ resources managed by the `platform-local-core` ArgoCD Application report `health=N/A`, causing the Application to show `Health: Degraded` despite every pod being in `Running/Ready` state.

The argo-cd Helm chart 9.4.16 (bundling ArgoCD v3.3.5) ships the following default in `configs.cm`:

```yaml
resource.customizations.ignoreResourceUpdates.all: |
  jsonPointers:
    - /status
```

This instructs ArgoCD to suppress watch events for `.status` field changes across all resource types. The intent is to reduce reconciliation churn from controllers that continuously update resource status (autoscalers, HPA, etc.).

In ArgoCD v3.x, this optimization inadvertently suppresses the watch events that the health evaluator depends on to compute and cache resource health. When status update events are dropped, the health evaluator never receives fresh data and leaves resources permanently at `health=N/A`. The blueprint's `argocd.values.yaml` does not currently override this key, so the Helm chart default takes effect.

## Decision

Override `resource.customizations.ignoreResourceUpdates.all` to an empty string in both:
- `infra/local/helm/core/argocd.values.yaml`
- `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`

```yaml
configs:
  cm:
    resource.customizations.ignoreResourceUpdates.all: ""
```

Setting the key to empty string neutralises the Helm chart default for the `all` resource scope. Per-resource-type entries that the Helm chart also ships by default (`argoproj.io_Application`, `argoproj.io_Rollout`, HPA annotation ignores) are not overridden and continue to reduce annotation churn for those specific types.

## Alternatives Considered

**Option B — Pin to a patched ArgoCD chart version:** Wait for an upstream fix in a newer argo-cd Helm chart or ArgoCD release where the health evaluation regression is resolved. Rejected: no patched version has been identified; the bug would remain active for an unknown period; the blueprint chart pin (9.4.16 / ArgoCD v3.3.5) is current.

## Consequences

- ArgoCD health status correctly reflects actual pod readiness after `make infra-deploy`.
- The `platform-local-core` Application reports `Health: Healthy` when pods are running.
- ArgoCD health-based alerting and notifications can be adopted for local development workflows.
- Reconciliation CPU may slightly increase on large clusters due to more status events being processed. Not a concern for local Docker Desktop development.
- This fix is local-lane only. Cloud-lane ArgoCD topology is managed separately and is not affected.

## References

- Issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/277
- Spec: `specs/2026-05-14-issue-277-argocd-health-na/spec.md`
- argo-cd Helm chart 9.4.16 default values: `configs.cm.resource.customizations.ignoreResourceUpdates.all`
