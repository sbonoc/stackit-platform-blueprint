# ADR: OpenSearch Bitnami Chart 1.6.x Breaking Changes — Local Dev Fixes

- Status: proposed
- Date: 2026-05-13
- Work item: `specs/2026-05-13-issue-281-282-opensearch-bitnami-chart-fixes/`
- Issues: #281, #282

## Context

Bitnami OpenSearch chart 1.6.x (released April 2025) introduced two breaking changes that block local OpenSearch provisioning for all blueprint consumers:

1. **Issue #281 — `allowInsecureImages` gate**: Charts using images from the `bitnamilegacy/` Docker Hub namespace now require `global.security.allowInsecureImages: true` in Helm values. Without it, the chart's pre-install validation hook rejects the deployment. The blueprint defaults to `bitnamilegacy/opensearch` (chart 1.6.x app version 2.19.x), triggering this gate.

2. **Issue #282 — `sysctlImage` init container removed tag**: The chart uses a `bitnami/os-shell` init container to set `vm.max_map_count` before OpenSearch starts. The tag referenced by chart 1.6.x has been removed from Docker Hub, causing all OpenSearch pods to remain in `Init:ImagePullBackOff` indefinitely.

The chart version is pinned to `1.6.3` in `scripts/lib/infra/versions.sh`. Both issues affect only the local Bitnami Helm chart path; the STACKIT managed service lane is unaffected.

## Decision

**Add two static YAML keys to the local Helm values template and its rendered copies (Option A).**

Files changed:
- `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`
- `infra/local/helm/opensearch/values.yaml`
- `artifacts/infra/rendered/opensearch.values.yaml`

Keys added:
```yaml
global:
  security:
    allowInsecureImages: true
sysctlImage:
  enabled: false
```

Two new unit test assertions are added to `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py` to prevent regression.

## Options Considered

### Option A — Static YAML keys (selected)

Add both keys directly as hardcoded static YAML in the template and seed files. No new placeholder variables.

**Pros:**
- Minimal diff; no new wiring across `opensearch.sh`, `versions.sh`, or `opensearch_render_values_file()`.
- `allowInsecureImages: true` is invariant for any consumer using a `bitnamilegacy/` image (the blueprint default) and is harmless for consumers who override to a trusted registry.
- `sysctlImage.enabled: false` is always correct for the local single-node dev cluster with `persistence.enabled: false`.
- No new env-var API surface; no consumer configuration required.

**Cons:**
- `allowInsecureImages: true` is always present even for consumers using a non-`bitnamilegacy/` image. The flag is harmless in that case but slightly misleading.

### Option B — Placeholder variables

Introduce `{{OPENSEARCH_ALLOW_INSECURE_IMAGES}}` and `{{OPENSEARCH_SYSCTL_IMAGE_ENABLED}}` as new placeholders, wired through `opensearch.sh` and `versions.sh`.

**Pros:**
- Consumers who override to a trusted registry can opt out of `allowInsecureImages`.

**Cons:**
- Four additional files changed for zero consumer benefit in practice (no consumer uses a non-`bitnamilegacy/` image today; the flag is harmless anyway).
- Introduces a new env-var API surface not warranted by the scope.
- Increases test surface: new pins in `versions.sh`, new assertions in the version-pin test class.

## Security Considerations

`global.security.allowInsecureImages: true` permits the Bitnami chart to pull `bitnamilegacy/` images. This permission is scoped to the local dev Helm values file. The `bitnamilegacy/` namespace is Bitnami's Docker Hub relocation namespace for images not yet migrated to OCI-compliant registries; it does not indicate the images are insecure in the traditional sense. The pinned tag `2.19.1-debian-12-r4` is the latest-stable image for the 1.6.x chart family. The STACKIT managed service lane is completely unaffected.

Disabling `sysctlImage` means `vm.max_map_count` is not tuned on the host. OpenSearch recommends `262144` for production workloads. For a single-node local dev cluster with `persistence.enabled: false`, this is acceptable.

## Deferred Proposals

- **Long-term**: Evaluate chart version upgrade to restore a working `sysctlImage` init container tag. Pinning to a newer chart version that resolves the `bitnami/os-shell` tag removal would restore sysctl tuning capability. Deferred because: (1) chart version changes require separate validation of all chart API surface changes; (2) `sysctlImage.enabled: false` is sufficient for local dev. Trigger: when chart 1.6.x is no longer the latest-stable or when a consumer requires sysctl tuning for local dev.
