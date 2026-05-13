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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-281-282-opensearch-bitnami-chart-fixes.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-015 excluded: no app delivery workflow scope; no Make-target contract changes for app onboarding.
  - SDD-C-018 excluded: this blueprint IS the upstream; SDD-C-018 applies to consumer work items applying blueprint workarounds, not to blueprint-side defect fixes.
  - SDD-C-022 excluded: no HTTP route handlers, query/filter logic, or API endpoints are in scope.
  - SDD-C-023 excluded: no filter or payload-transform logic is in scope.

## Implementation Stack Profile (Normative)
- Backend stack profile: none — YAML template config and Python pytest assertions only; no application-layer service code
- Frontend stack profile: none — infrastructure-only work item
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: stackit-managed-first
- Managed service exception rationale: fix is local-lane only (Bitnami Helm chart values); STACKIT-lane provisioning is unaffected and remains managed-service-first
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Local OpenSearch provisioning succeeds on Bitnami chart ≥ 1.6.x without consumer-side workarounds; `infra-opensearch-apply` reaches Running state for all blueprint consumers after the upgrade.
- Success metric: `infra-opensearch-apply` completes without Helm pre-install validation errors or init-container ImagePullBackOff; two new unit assertions in `test_opensearch_module.py` pass green; `make quality-hooks-fast` and `make infra-validate` both pass.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The local Helm values template (`scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`) MUST include `global.security.allowInsecureImages: true` as a static top-level key.
- FR-002 The local Helm values template MUST include `sysctlImage.enabled: false` as a static top-level key.
- FR-003 The blueprint seed values file (`infra/local/helm/opensearch/values.yaml`) MUST mirror both keys declared in FR-001 and FR-002.
- FR-004 The artifact rendered file (`artifacts/infra/rendered/opensearch.values.yaml`) MUST mirror both keys declared in FR-001 and FR-002.
- FR-005 The test class `OpenSearchLocalHelmChartTests` in `tests/infra/modules/opensearch/test_opensearch_module.py` MUST include `test_opensearch_seed_values_allow_insecure_images` asserting `global.security.allowInsecureImages: true` in the seed values file, and `test_opensearch_seed_values_sysctl_image_disabled` asserting `sysctlImage.enabled: false` in the seed values file.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 `global.security.allowInsecureImages: true` MUST be scoped to local-lane Helm values files only; STACKIT-lane provisioning (Terraform/managed service path) MUST NOT be affected by this change.
- NFR-OBS-001 N/A — no logs, metrics, or traces paths are affected by this change; the fix is limited to static YAML values and Python test assertions.
- NFR-REL-001 Local environments that re-run `helm upgrade` after the fix is applied MUST receive the corrected values on the next apply cycle without operator intervention or manual values file edits.
- NFR-OPS-001 N/A — no runbook changes are required; the fix is self-contained in the values files and requires no operational procedure updates.
- NFR-A11Y-001 N/A — infrastructure-only work item; no UI components.

## Normative Option Decision
- Option A: Add both keys as static YAML in the template and seed/artifact files (hardcoded; no new placeholder variables).
- Option B: Introduce placeholder variables (e.g. `{{OPENSEARCH_ALLOW_INSECURE_IMAGES}}`, `{{OPENSEARCH_SYSCTL_IMAGE_ENABLED}}`) wired through `opensearch.sh`, `versions.sh`, and `opensearch_render_values_file()`.
- Selected option: OPTION_A
- Rationale: `allowInsecureImages: true` is required whenever a `bitnamilegacy/` image is used and is harmless for alternative registries; the value is invariant for any consumer using the blueprint default. `sysctlImage.enabled: false` is always correct for the local single-node dev cluster (persistence disabled). No consumer override of `allowInsecureImages` or `sysctlImage.enabled` adds meaningful flexibility. Option B would add variable wiring across four files for zero consumer benefit and would introduce a new env-var API surface not warranted by the scope.

## Contract Changes (Normative)
- Config/Env contract: none — no new environment variables or `blueprint/contract.yaml` changes
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — existing make targets (`infra-opensearch-apply`, `infra-opensearch-plan`, `infra-opensearch-smoke`, `infra-opensearch-destroy`) are unaffected
- Docs contract: `docs/platform/modules/opensearch/README.md` and its blueprint template copy (`scripts/templates/blueprint/bootstrap/docs/platform/modules/opensearch/README.md`) MUST be reviewed for staleness; no behavioral change to existing contract text is expected, but a chart version compatibility note MUST be added if absent.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — this repository IS the blueprint upstream; the fix is applied directly
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `global.security.allowInsecureImages: true` MUST be present in `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`.
- AC-002 `sysctlImage.enabled: false` MUST be present in `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml`.
- AC-003 Both keys from AC-001 and AC-002 MUST be present in `infra/local/helm/opensearch/values.yaml`.
- AC-004 Both keys from AC-001 and AC-002 MUST be present in `artifacts/infra/rendered/opensearch.values.yaml`.
- AC-005 `test_opensearch_seed_values_allow_insecure_images` MUST pass; it MUST assert that `parsed["global"]["security"]["allowInsecureImages"]` is `True` in the seed values file.
- AC-006 `test_opensearch_seed_values_sysctl_image_disabled` MUST pass; it MUST assert that `parsed["sysctlImage"]["enabled"]` is `False` in the seed values file.
- AC-007 `make quality-hooks-fast` MUST pass with zero violations after all changes are applied.
- AC-008 `make infra-validate` MUST pass after all changes are applied.

## Informative Notes (Non-Normative)
- Context: Bitnami OpenSearch chart 1.6.x (April 2025) introduced two breaking changes for the local dev lane: (1) charts using `bitnamilegacy/` images now require `global.security.allowInsecureImages: true` in values, otherwise a pre-install validation hook rejects the deployment; (2) the `sysctlImage` init container (`bitnami/os-shell`) references a tag that has been removed from Docker Hub, causing all OpenSearch pods to remain in `Init:ImagePullBackOff`. Both issues affect only the local Bitnami Helm chart path; the STACKIT managed service lane is unaffected.
- Tradeoffs: Disabling `sysctlImage` means `vm.max_map_count` is not tuned on the host. For a single-node local dev cluster with `persistence.enabled: false`, this is acceptable. Production OpenSearch on STACKIT uses the managed service and is unaffected.
- Clarifications: no open clarifications; all inputs resolved from issue analysis and code inspection.

## Explicit Exclusions
- Changes to the STACKIT Terraform module or managed service path — STACKIT lane is unaffected.
- Pinning a different chart version to restore a working `sysctlImage` init container tag — `sysctlImage.enabled: false` is the correct minimal fix for local dev; chart version changes require separate validation scope.
- Consumer repository changes — blueprint fix propagates at next consumer upgrade.
- Any new placeholder variable wiring — Option A selected; no new env vars.
