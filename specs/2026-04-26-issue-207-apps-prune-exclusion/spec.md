# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-207-apps-prune-exclusion.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: This is a blueprint tooling fix with no managed service surface. No STACKIT-managed service is involved.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Consumer repositories whose teams rename or extend workload manifests in `infra/gitops/platform/base/apps/` can run `make blueprint-upgrade` with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true` without losing their deployment definitions.
- Success metric: `_classify_entries()` emits `action=skip, operation=none, ownership=consumer-owned-workload` for any non-kustomization YAML under `base/apps/` that is absent in the blueprint source; zero such files are enqueued for `OPERATION_DELETE`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST: When `_classify_entries()` processes a path that matches `infra/gitops/platform/base/apps/<name>.yaml` (where `<name>` is not `kustomization`) and the path is absent in the blueprint source tree, the resulting `UpgradeEntry` MUST have `action=skip` and `operation=none`, regardless of the `allow_delete` flag value.
- FR-002 MUST: The path `infra/gitops/platform/base/apps/kustomization.yaml` MUST NOT be affected by the new guard; it continues to flow through the existing upgrade classification logic (create/update/merge/delete as determined by blueprint ownership).
- FR-003 MUST: The new skip class MUST be visible in the upgrade plan output with a human-readable reason distinguishing it from `consumer-seeded` and `source-only` skip classes.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST: The new predicate MUST be a pure function with no file system reads, no subprocess calls, and no external state. It MUST be safe to call in any execution context.
- NFR-OBS-001 MUST: The `reason` field on the new skip entries MUST be unique enough that `grep` on plan JSON output can isolate consumer-owned-workload skips without false positives from other skip classes.
- NFR-REL-001 MUST: The fix MUST be additive — it MUST NOT alter the classification logic for any path that did not previously trigger the new predicate. Existing test coverage for all other path classes MUST continue to pass without modification.
- NFR-OPS-001 MUST: The `ownership` field value `"consumer-owned-workload"` MUST appear in the plan output JSON so operators can audit which files were protected during an upgrade run.

## Normative Option Decision
- Option A: Pure predicate `_is_consumer_owned_workload()` added to `upgrade_consumer.py`; check injected in `_classify_entries()` before the delete branch. No contract schema change.
- Option B: Add all consumer workload manifest paths to `contract.yaml` `consumer_seeded_paths` in the blueprint source. Requires contract file edits on every template change; places the burden on the blueprint author, not the consumer.
- Selected option: OPTION_A
- Rationale: Option A is zero-config for consumers, is additive to the upgrade planner, and is explicitly scoped to the `base/apps/` directory boundary. Option B leaks consumer-specific knowledge into the blueprint source contract. Option A is documented as a bridge until issue #206 delivers a general schema mechanism.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: Given a consumer repository with `my-api-deployment.yaml` and `my-api-service.yaml` under `infra/gitops/platform/base/apps/` that are absent from the blueprint source, a plan run with `allow_delete=True` MUST produce `UpgradeEntry` records with `action=skip`, `operation=none`, and `ownership="consumer-owned-workload"` for both paths; zero `OPERATION_DELETE` entries for those paths.
- AC-002 MUST: A plan run with `allow_delete=True` MUST continue to enqueue `OPERATION_DELETE` for `infra/gitops/platform/base/apps/kustomization.yaml` when that file is absent in the blueprint source (kustomization.yaml is not protected by the new guard).
- AC-003 MUST: The predicate `_is_consumer_owned_workload()` MUST return `False` for `infra/gitops/platform/base/apps/kustomization.yaml`.
- AC-004 MUST: The predicate MUST return `False` for any path not under `infra/gitops/platform/base/apps/`.
- AC-005 MUST: All existing tests in `tests/blueprint/test_upgrade_consumer.py` MUST pass without modification.

## Informative Notes (Non-Normative)
- Context: Issue #207 was filed by consumer sbonoc/dhe-marketplace during their v1.7.0 upgrade. Their workload manifests were deleted during a `blueprint-upgrade` run with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`.
- Tradeoffs: The path-prefix approach means blueprint cannot reclaim management of any `.yaml` in `base/apps/` (except `kustomization.yaml`) without a schema change. This is intentional — issue #206 will provide the correct long-term mechanism.
- Clarifications: The `consumer_seeded` mechanism requires explicit listing in `contract.yaml`; it is not a scalable solution for files that consumers can create dynamically. The new `consumer-owned-workload` ownership class fills this gap for the `base/apps/` directory specifically.

## Explicit Exclusions
- Contract schema changes for general consumer ownership declaration (issue #206).
- Any changes to how kustomization.yaml in `base/apps/` is managed.
- Changes to prune logic for directories other than `infra/gitops/platform/base/apps/`.
