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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: This is a blueprint contract YAML modification. No STACKIT-managed service surface is involved.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Consumer repositories whose teams rename, add, or remove workload manifests in `infra/gitops/platform/base/apps/` can run `blueprint-upgrade` without needing to re-patch their `blueprint/contract.yaml` after every upgrade. The four blueprint-seed manifest names are no longer part of the upgrade-sync contract.
- Success metric: After the implementing blueprint version is released, a consumer who runs `blueprint-upgrade` with renamed workload manifests sees no mention of `backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, or `touchpoints-web-service.yaml` in the upgrade plan's create/update/delete actions.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST: The four blueprint-seed workload manifest paths (`infra/gitops/platform/base/apps/backend-api-deployment.yaml`, `...backend-api-service.yaml`, `...touchpoints-web-deployment.yaml`, `...touchpoints-web-service.yaml`) MUST be removed from the global `required_files` list in `blueprint/contract.yaml`.
- FR-002 MUST: The four paths MUST be added to `source_only_paths` in `blueprint/contract.yaml` so that (a) template-source CI coverage checks continue to pass, and (b) the upgrade planner classifies them as `source-only / skip` during consumer upgrade runs.
- FR-003 MUST: The four paths MUST be removed from `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`. Only `infra/gitops/platform/base/apps` (directory) and `infra/gitops/platform/base/apps/kustomization.yaml` remain in that list.
- FR-004 MUST: After a consumer upgrades to the blueprint version that includes this fix, their `blueprint/contract.yaml` will no longer list the four paths in `required_files` or `required_paths_when_enabled`. No consumer manual patching is required for subsequent upgrades.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST: The change MUST NOT introduce any new file system write operations or credential handling.
- NFR-OBS-001 MUST: The upgrade plan output for consumers with the old seed manifest names MUST show those paths classified as `source-only / skip` after this fix is applied, making the behavioral change observable without running the full upgrade.
- NFR-REL-001 MUST: The change MUST be backward-compatible for consumers who have not yet renamed their manifests. For consumers with the original seed names, the upgrade planner will skip the files (source-only) rather than update them — the files remain unchanged in the consumer repo.
- NFR-OPS-001 MUST: The template-source CI coverage check (`audit_source_tree_coverage`) MUST continue to pass after the fix. The four seed files remain in the template source repo; their classification changes from `required` to `source-only`.

## Normative Option Decision
- Option A: Move the 4 paths from `required_files` to `source_only_paths`; remove from `required_paths_when_enabled`. Uses existing `source_only` mechanism with zero code changes.
- Option B: Introduce a new contract schema field `consumer_workload_manifest_paths: list[str]` on `app_runtime_gitops_contract` that allows consumers to declare their actual manifest names; the upgrade planner preserves this field across upgrades via a dedicated carry-forward mechanism.
- Selected option: OPTION_A
- Rationale: Option A is the minimal, zero-code-change fix that eliminates the mandatory re-patching. It uses an existing, tested mechanism (`source_only_paths`). Option B provides a richer long-term mechanism for consumers who want explicit contract-level validation of their manifest names, but it requires: (a) a new Pydantic schema field, (b) a new upgrade planner carry-forward mechanism for consumer-declared overrides, and (c) a migration path for existing consumers. Option B is not blocked — it can be implemented on top of Option A in a future work item once the domain boundary is stable (issues #207 and #208 establish that foundation). Option A ships the immediate relief without speculative complexity.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` — two list modifications (see FR-001–FR-003). The YAML structure is unchanged; only entries within existing lists are moved.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: none — ADR to be written during implementation.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: Consumers can manually patch their `blueprint/contract.yaml` to remove the 4 paths from `required_files` and `required_paths_when_enabled` until this blueprint version is released.
- Replacement trigger: This spec. The workaround patch is eliminated by implementing FR-001–FR-003.
- Workaround review date: none — the spec is ready for implementation.

## Normative Acceptance Criteria
- AC-001 MUST: After the fix is applied, the four seed manifest paths MUST appear in `source_only_paths` and NOT appear in `required_files` in `blueprint/contract.yaml`.
- AC-002 MUST: After the fix is applied, the four seed manifest paths MUST NOT appear in `app_runtime_gitops_contract.required_paths_when_enabled` in `blueprint/contract.yaml`.
- AC-003 MUST: The template-source unit test for `audit_source_tree_coverage` MUST pass without any uncovered-file warnings for the four seed paths.
- AC-004 MUST: A generated-consumer upgrade plan with `allow_delete=True`, run against a consumer repo that has renamed their workload manifests, MUST show zero `OPERATION_DELETE` entries for the four seed paths and zero `OPERATION_CREATE` entries attempting to recreate them.
- AC-005 MUST: A generated-consumer upgrade plan run against a consumer repo that still has the original seed manifest names MUST classify those files as `source-only / skip` (not `update` or `delete`), preserving them unchanged.

## Informative Notes (Non-Normative)
- Context: Issues #207 and #208 addressed the symptoms (prune deletion, smoke CI failures). Issue #206 addresses the root cause: the contract itself embeds consumer workload naming decisions as blueprint requirements.
- Tradeoffs: Moving paths to `source_only` means blueprint cannot push content updates to the 4 seed manifests via upgrade. This is intentional — consumers own their workload manifests. Blueprint only seeds them on `blueprint-init-repo`.
- Consequence accepted (explicit, 2026-04-27): Once merged, consumers who run `blueprint-upgrade` will never automatically receive future blueprint content improvements to the 4 seed manifest files (health probes, security contexts, resource limits, etc.). This is the intended tradeoff: workload manifests are consumer-domain after init; future seed improvements are the consumer's responsibility to apply manually. This is consistent with the apps.yaml long-term direction.
- Clarifications: Option B (consumer_workload_manifest_paths field) remains a valid future enhancement for teams that want explicit preflight validation of their actual manifest names. It is tracked as a separate follow-up item in the backlog.

## Explicit Exclusions
- Option B (consumer_workload_manifest_paths schema field): deferred to a future work item.
- Changes to `init_repo_contract.py` or the init-time scaffolding logic.
- Changes to the upgrade planner algorithm (issues #207 and #208 already handle the planner).
- Changes to any files other than `blueprint/contract.yaml` and the ADR.
