# Architecture

## Context
- Work item: issue-281-282-opensearch-bitnami-chart-fixes
- Owner: sbonoc
- Date: 2026-05-13

## Stack and Execution Model
- Backend stack profile: none — YAML template config and Python pytest assertions only
- Frontend stack profile: none — infrastructure-only
- Test automation profile: pytest
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why: Bitnami OpenSearch chart 1.6.x (April 2025) introduced two breaking changes for the local dev lane: (1) charts using `bitnamilegacy/` images require `global.security.allowInsecureImages: true` in Helm values; (2) the `sysctlImage` init container references a Docker Hub tag that has been removed, causing `Init:ImagePullBackOff`. Both issues block local OpenSearch provisioning for all blueprint consumers. The fix is to add two static YAML keys to the local Helm values template and its rendered copies.
- Scope boundaries: local Helm values files (template + seed + rendered artifact) and Python test assertions in `test_opensearch_module.py`.
- Out of scope: STACKIT managed service lane, chart version change, env var wiring, consumer repository changes.

## Bounded Contexts and Responsibilities
- Context A — Local Helm provisioning values layer: owns the three YAML files (`scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`, `infra/local/helm/opensearch/values.yaml`, `artifacts/infra/rendered/opensearch.values.yaml`). These files are in the infrastructure adapter layer; they configure the Bitnami chart runtime, not application business logic.
- Context B — Test assertion layer: owns `tests/infra/modules/opensearch/test_opensearch_module.py` class `OpenSearchLocalHelmChartTests`. Tests parse the seed values file and assert on structural properties; they do not execute Helm or Kubernetes.

## High-Level Component Design
- Domain layer: none — no domain logic is involved; this is a configuration correction.
- Application layer: none — `opensearch.sh` and the apply/plan/smoke/destroy scripts are unchanged.
- Infrastructure adapters: Helm values template and seed files (local provisioning path). Both new keys are static values; no new variable wiring or rendering logic is needed.
- Presentation/API/workflow boundaries: none — no Make target signatures, env-var contracts, or CLI interfaces change.

## Integration and Dependency Edges
- Upstream dependencies: Bitnami OpenSearch chart 1.6.x (pinned at `OPENSEARCH_HELM_CHART_VERSION_PIN="1.6.3"` in `versions.sh`). The chart's pre-install hook enforces the `allowInsecureImages` gate; the chart pulls `bitnami/os-shell` for the sysctl init container.
- Downstream dependencies: consumers who have already bootstrapped will need to apply the fix via blueprint upgrade. The template fix propagates automatically for new consumers at bootstrap time.
- Data/API/event contracts touched: none.

## Non-Functional Architecture Notes
- Security: `global.security.allowInsecureImages: true` permits the Bitnami chart to use `bitnamilegacy/` Docker Hub images. This flag is scoped to the local dev Helm values file and has no effect on the STACKIT managed service lane. The `bitnamilegacy/` namespace contains the same Bitnami image content relocated for namespacing reasons; the pinned tag `2.19.1-debian-12-r4` is still the current latest-stable image for this chart version family.
- Observability: no change.
- Reliability and rollback: the change is additive and backward-compatible. Consumers that re-run `infra-opensearch-apply` after the fix receive the corrected values on the next `helm upgrade`. Rollback: removing both keys from the values file restores the pre-fix state, which was already broken on chart 1.6.x.
- Monitoring/alerting: no change.

## Architecture Decision
- Selected option: Option A — static YAML keys, no new placeholder variables.
- Rationale: both values are invariant for the local dev lane regardless of consumer configuration. Option B (placeholder variables) adds wiring complexity across four files for zero consumer benefit. See ADR for full option analysis.

## Diagram

No diagram required — the change is two static YAML key additions and two test assertions; no control flow, state machine, or component interaction changes.

## Risks and Tradeoffs
- Risk 1: `sysctlImage.enabled: false` means `vm.max_map_count` is not tuned on the host. OpenSearch recommends `262144` for production. Acceptable for local dev (single node, no persistence); STACKIT managed service is unaffected.
- Tradeoff 1: `global.security.allowInsecureImages: true` is present for all consumers, including those who override the image to a trusted registry. The flag is harmless in that case (it permits something that is not present) and does not weaken security for trusted-registry images.
