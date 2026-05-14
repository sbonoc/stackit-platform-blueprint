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

Apply two changes together:

**1 — Override `resource.customizations.ignoreResourceUpdates.all` to empty string** in both:
- `infra/local/helm/core/argocd.values.yaml`
- `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml`

```yaml
configs:
  cm:
    resource.customizations.ignoreResourceUpdates.all: ""
```

Setting the key to empty string neutralises the Helm chart default for the `all` resource scope. Per-resource-type entries (`argoproj.io_Application`, `argoproj.io_Rollout`, HPA annotation ignores) are not overridden and continue to reduce annotation churn for those types.

**2 — Bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13`** in:
- `scripts/lib/infra/versions.sh`
- `scripts/lib/infra/versions.baseline.sh`

This tracks ArgoCD v3.4.1, which contains ~5 weeks of upstream fixes over v3.3.5. The chart bump is a minor increment (9.4 → 9.5) with no breaking API or CRD changes in the release notes. The values override acts as a permanent safety net regardless of ArgoCD version.

## Alternatives Considered

**Option A — Values override only, keep chart at 9.4.16:** Fixes the immediate bug but leaves the blueprint on an older ArgoCD version. Rejected: the chart upgrade is a low-risk minor increment and avoiding it would require an immediate follow-up work item; both changes touch the same files so the cost of combining them is negligible.

## Consequences

- ArgoCD health status correctly reflects actual pod readiness after `make infra-deploy`.
- The `platform-local-core` Application reports `Health: Healthy` when pods are running.
- ArgoCD health-based alerting and notifications can be adopted for local development workflows.
- Reconciliation CPU can slightly increase on large clusters due to more status events being processed. Not a concern for local Docker Desktop development.
- Blueprint tracks ArgoCD v3.4.1 (chart 9.5.13) as the pinned version.
- This fix is local-lane only. Cloud-lane ArgoCD topology is managed separately and is not affected.
- Rollback: remove `configs.cm` block, revert `ARGOCD_CHART_VERSION` to `9.4.16`, run `make infra-deploy`.

## References

- Issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/277
- Spec: `specs/2026-05-14-issue-277-argocd-health-na/spec.md`
- argo-cd Helm chart 9.4.16 default values: `configs.cm.resource.customizations.ignoreResourceUpdates.all`
