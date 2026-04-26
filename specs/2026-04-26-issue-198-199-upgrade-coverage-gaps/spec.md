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
- Missing input blocker token:
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-198-199-upgrade-coverage-gaps.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Close three latent coverage gaps in the blueprint upgrade pipeline that allow regressions in consumer repos to go undetected until CI: (1) `blueprint-template-smoke` is absent from `VALIDATION_TARGETS`, so template-init regressions are never caught locally; (2) `infra-argocd-topology-validate` is absent from `VALIDATION_TARGETS`, so broken kustomize topology manifests (e.g. from the Stage 2 prune step) are not caught before push; (3) `apps/catalog` feature-gated paths are missing from `ownership_path_classes`, causing false-positive "uncovered file" warnings on every blueprint source-tree coverage audit.
- Success metric: (1) `blueprint-template-smoke` and `infra-argocd-topology-validate` appear in `VALIDATION_TARGETS`; (2) `apps/catalog*` paths are declared under a new `feature_gated` ownership class; (3) `audit_source_tree_coverage` accepts `feature_gated` paths; (4) `make infra-validate` passes on the blueprint repo; (5) all new and existing tests are green.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST add `"blueprint-template-smoke"` to `VALIDATION_TARGETS` in `scripts/lib/blueprint/upgrade_consumer_validate.py` so that the init-path smoke check runs in every generated-consumer repo after blueprint upgrade.
- FR-002 MUST add a `feature_gated` field to `RepositoryOwnershipPathClasses` in `scripts/lib/blueprint/contract_schema.py` that holds a list of paths that are owned by the platform under an opt-in feature flag, require no disk-presence check, and are not required to match the `optional_modules` equality invariant.
- FR-003 MUST pass `feature_gated` paths as a coverage set to `audit_source_tree_coverage` in `scripts/lib/blueprint/upgrade_consumer.py` so that feature-gated paths do not produce false-positive uncovered-file warnings.
- FR-004 MUST declare `apps/catalog`, `apps/catalog/manifest.yaml`, and `apps/catalog/versions.lock` under `feature_gated` in `blueprint/contract.yaml` `ownership_path_classes` (and mirror the change to the bootstrap template counterpart).
- FR-005 MUST add `"infra-argocd-topology-validate"` to `VALIDATION_TARGETS` in `scripts/lib/blueprint/upgrade_consumer_validate.py` so that broken kustomize topology manifests (e.g. introduced by the Stage 2 prune step) are caught locally before push, mirroring the `blueprint-quality` CI gate.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce any authn/authz bypass, secret exposure, or privilege escalation. This work is confined to Python schema/validation logic and YAML contract files; the security posture is unchanged.
- NFR-OBS-001 MUST update the `validate_plan_uncovered_source_files` error message to reference `feature_gated` alongside existing coverage sets so that operators can interpret any remaining warnings without consulting source code.
- NFR-REL-001 MUST NOT break `make infra-validate` on the blueprint repo or `make quality-hooks-fast` in consumer repos; rollback MUST be achievable by reverting the PR.
- NFR-OPS-001 MUST ensure `blueprint-template-smoke` and `infra-argocd-topology-validate` are runnable in generated-consumer repos after upgrade without any additional operator configuration. Both targets MUST be safe to invoke in a read-only context (no side effects on the consumer repo).

## Normative Option Decision
- Option A: Loosen `_optional_str_map` and extend `OptionalModuleContract.paths` to include `apps/catalog` paths; adapt the `conditional_scaffold` equality invariant to tolerate non-matched entries.
- Option B: Add a new `feature_gated` peer class to `RepositoryOwnershipPathClasses`; paths declared there are passed to `audit_source_tree_coverage` as an additional coverage set, with no disk-presence check and no equality constraint against `optional_modules`.
- Selected option: OPTION_B
- Rationale: Option A requires invasive changes across `contract_schema.py` (`_optional_str_map`, `OptionalModuleContract`, loader), `validate_contract.py` (equality invariant), and `contract.yaml` (module structure) — with non-trivial risk of breaking existing optional-module consumers. Option B isolates the change to ~15 lines across 3 Python files plus a YAML addition; it is semantically precise (feature-gated ≠ conditional-scaffold), and it generalises to future flag-gated paths without schema loosening.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `blueprint-template-smoke` and `infra-argocd-topology-validate` already exist as blueprint-managed targets; adding them to `VALIDATION_TARGETS` does not change their signatures.
- Docs contract: `validate_plan_uncovered_source_files` error string updated to mention `feature_gated`.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: a unit test confirms `"blueprint-template-smoke"` is present in `upgrade_consumer_validate.VALIDATION_TARGETS`.
- AC-002 MUST: `audit_source_tree_coverage` called with `feature_gated={"apps/catalog"}` does not flag `apps/catalog/manifest.yaml` as uncovered; confirmed by a new unit test.
- AC-003 MUST: `validate_contract.py` accepts a `contract.yaml` bearing `feature_gated: [apps/catalog, ...]` without emitting errors.
- AC-004 MUST: `make infra-validate` passes on the blueprint repo after all changes are applied.
- AC-005 MUST: all pre-existing `TestAuditSourceTreeCoverage` tests remain green; the new `feature_gated` parameter defaults to empty set to preserve backward compatibility at call sites not yet updated.
- AC-006 MUST: a unit test confirms `"infra-argocd-topology-validate"` is present in `upgrade_consumer_validate.VALIDATION_TARGETS`.
- AC-007 MUST: the `validate_plan_uncovered_source_files` error message in `scripts/lib/blueprint/upgrade_consumer.py` references `feature_gated` in its coverage-set description; verifiable by code inspection of the updated string at line 399.

## Informative Notes (Non-Normative)
- Context: Issue #198 — `apps/catalog*` paths are covered only by `app_catalog_scaffold_contract.required_paths_when_enabled` but that contract is a separate top-level key, not wired into `ownership_path_classes`. Issue #199 — `blueprint-template-smoke` was intentionally added as a Make target in an earlier issue but was never added to `VALIDATION_TARGETS`. Issue #199 comment — `infra-argocd-topology-validate` is also missing from `VALIDATION_TARGETS`; `infra-validate` calls `validate.sh` which does not run `kustomize build`, so broken topology manifests (e.g. from the Stage 2 prune step, as observed in dhe-marketplace #203) only surface at the CI `blueprint-quality` job. Issue #203 — Stage 2 prune deletes consumer-renamed blueprint-seeded files; adding `infra-argocd-topology-validate` to `VALIDATION_TARGETS` provides early detection of the symptom; the root cause (prune algorithm) is excluded (see Explicit Exclusions). Issue #204 — 3-way merge emits duplicate Terraform variable blocks; excluded as it requires a semantic .tf file parser or provider-dependent `terraform validate`; separate work item.
- Tradeoffs: Option B adds a new ownership class name that future developers must learn. The alternative (Option A) would have required touching the `OptionalModuleContract` schema more broadly and adjusting the equality invariant, risking regressions in all modules that use `conditional` scaffolding. `infra-argocd-topology-validate` degrades gracefully when kustomize is not installed (falls back to kustomization file check), so it is safe to include in VALIDATION_TARGETS without hard-requiring kustomize.
- Clarifications: none

## Explicit Exclusions
- Extending `_optional_str_map` or `OptionalModuleContract.paths` (Option A approach) is explicitly excluded.
- Disk-presence checks for `feature_gated` paths are explicitly excluded — these paths are only expected on-disk when the feature flag is enabled in the consumer repo.
- Consumer-repo migration guidance or docs updates for `apps/catalog` enablement are out of scope.
- Issue #203 root cause (Stage 2 prune algorithm deleting consumer-renamed seeded files) is explicitly excluded from this PR. The fix requires modifications to the prune algorithm in `upgrade_consumer.py` Stage 2 apply logic. The suggested fix in #203 (checking kustomization.yaml references before pruning) is too narrow — it handles only the kustomization case and not the general rename problem. Early detection is mitigated by FR-005 (`infra-argocd-topology-validate` in VALIDATION_TARGETS). Root cause fix is a separate work item.
- Issue #204 (3-way merge duplicate Terraform block declarations) is explicitly excluded from this PR. The fix requires either a semantic Terraform parser (new dependency/complexity) or running `terraform validate` during upgrade validation (provider-dependent, slow). Architecturally unrelated to VALIDATION_TARGETS gaps and feature_gated ownership class. Separate work item.
