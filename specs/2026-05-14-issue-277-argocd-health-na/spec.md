# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-277-argocd-health-na.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-007: N/A — no application layer code; purely a YAML configuration change.
  - SDD-C-009: N/A — no new secrets, authentication, or authorization surfaces introduced.
  - SDD-C-013: N/A — local-lane scope only; no STACKIT managed service involved.
  - SDD-C-018: N/A — this IS the upstream blueprint fix, not a consumer-side workaround.
  - SDD-C-022: N/A — no HTTP route or API endpoint changes.
  - SDD-C-023: N/A — no filter or payload-transform logic.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: this work item is a local-lane Helm values override; no runtime service module is introduced or modified; the explicit-consumer-exception reflects the absence of any managed service surface
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: ArgoCD health status correctly reflects actual pod readiness for all local-lane managed resources, and the blueprint tracks ArgoCD v3.4.1 (chart 9.5.13); operators can trust the ArgoCD UI/CLI health rollup and unblock notifications/alerting adoption.
- Success metric: `argocd app get platform-local-core` reports `Health: Healthy` (not `Degraded`) after a clean `make infra-post-deploy-consumer` when all pods are running; `infra-audit-version` reports `ARGOCD_CHART_VERSION=9.5.13`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The blueprint MUST override `resource.customizations.ignoreResourceUpdates.all` to an empty string in `infra/local/helm/core/argocd.values.yaml`, neutralising the argo-cd Helm chart default that suppresses `/status` watch events for all resource types.
- FR-002 The blueprint MUST apply the same override in the bootstrap template `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` so that new consumers receive the fix on `make blueprint-init-repo` and existing consumers receive it on the next blueprint upgrade.
- FR-003 The blueprint MUST bump `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13` in `scripts/lib/infra/versions.sh` and `scripts/lib/infra/versions.baseline.sh`, tracking ArgoCD v3.4.1 as the current pinned version.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 N/A — no security surface changed by this fix.
- NFR-OBS-001 After the fix is applied, ArgoCD health status for standard Kubernetes resources (Deployment, Service, ExternalSecret) managed by `platform-local-core` MUST reflect actual pod readiness and MUST NOT remain permanently at `N/A`.
- NFR-REL-001 The values file change MUST be reversible by removing the `configs.cm` override; no data migration is required and no state is lost on rollback.
- NFR-OPS-001 After `make infra-deploy` applies the fix, operators MUST be able to verify correct health via `argocd app get platform-local-core` without additional manual steps.
- NFR-A11Y-001 N/A — no UI changes.

## Normative Option Decision
- Option A: Apply values override only — override `resource.customizations.ignoreResourceUpdates.all` to empty string; keep chart at 9.4.16.
- Option B: Apply values override AND bump chart to 9.5.13 (ArgoCD v3.4.1) in the same work item.
- Selected option: OPTION_B
- Rationale: The values override guarantees the fix regardless of ArgoCD version. The chart bump (9.4.16 → 9.5.13, ArgoCD v3.3.5 → v3.4.1) is a low-risk minor increment with ~5 weeks of upstream fixes; both changes touch the same files in the same diff; doing them together avoids an immediate follow-up P2 chart upgrade work item. The override acts as a permanent safety net even if a future chart version re-introduces the default.

## Contract Changes (Normative)
- Config/Env contract: `infra/local/helm/core/argocd.values.yaml` gains a `configs.cm` block overriding one Helm chart default key. `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` receives the identical change. `scripts/lib/infra/versions.sh` and `scripts/lib/infra/versions.baseline.sh` change `ARGOCD_CHART_VERSION` from `9.4.16` to `9.5.13`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no new or changed make targets
- Docs contract: none — the values file comment is sufficient; no platform docs page documents this key

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 A regression test MUST parse `infra/local/helm/core/argocd.values.yaml` and assert that `configs.cm["resource.customizations.ignoreResourceUpdates.all"]` is an empty string (not a jsonPointers block).
- AC-002 A regression test MUST parse `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` and assert the same empty-string override.
- AC-003 A regression test MUST read `scripts/lib/infra/versions.sh` and assert that `ARGOCD_CHART_VERSION` equals `9.5.13`.
- AC-004 All regression tests MUST pass in the existing test suite without a live cluster.
- AC-005 After running `make infra-deploy` on a Docker Desktop cluster with the fix applied, `argocd app get platform-local-core` SHALL NOT report `health=N/A` for Deployment or Service resources when all pods are in `Running/Ready` state. (Manual verification; no live-cluster CI gate.)

## Informative Notes (Non-Normative)
- Context: The argo-cd Helm chart 9.4.16 (bundling ArgoCD v3.3.5) ships `resource.customizations.ignoreResourceUpdates.all` with a `/status` jsonPointer as a default `configs.cm` entry. The intent is to reduce reconciliation churn from noisy status-only updates. In ArgoCD v3.x this optimization inadvertently suppresses the watch events that the health evaluator depends on, leaving all resources permanently at `health=N/A`. Setting the key to empty string restores standard health evaluation while keeping the per-resource-type entries (argoproj.io_Application, Rollout, HPA) that target genuinely noisy annotation churn.
- Tradeoffs: Removing the all-resource `/status` suppression can increase reconciliation CPU on large clusters with many status-updating controllers (e.g., HPA). For local Docker Desktop development this is not a concern.
- Clarifications: none

## Explicit Exclusions
- Cloud-lane ArgoCD configuration (STACKIT environments use ApplicationSet + different topology; this fix is local-lane only).
- Upgrading the argo-cd Helm chart version (out of scope; chart pin is managed separately).
- Per-resource-type health customizations beyond removing the all-scope suppression (no evidence of need; surfaced as a parked proposal if required later).
