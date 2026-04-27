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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-208-dynamic-workload-derivation.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-013: not applicable — no runtime STACKIT managed services involved; this is internal blueprint tooling.
  - SDD-C-014: not applicable — no local Kubernetes or cloud runtime paths affected; pure blueprint tooling change.
  - SDD-C-015: app onboarding minimum targets: not impacted by this change.
  - SDD-C-018: not applicable — this work item IS a blueprint-source fix; there is no upstream to escalate.
  - SDD-C-022: not applicable — no HTTP route handlers, query/filter logic, or API endpoints affected.
  - SDD-C-023: not applicable — no filter or payload-transform logic; this is a workload file derivation change.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_bash_scripts (Python script + Bash script; no FastAPI/Pydantic runtime)
- Frontend stack profile: none
- Test automation profile: pytest (unit tests only)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: internal blueprint tooling; no STACKIT managed services are provisioned or consumed by this change
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: no local Kubernetes or cloud runtime paths are affected by this change; only blueprint tooling scripts are modified

## Objective
- Business outcome: Eliminate the hardcoded app workload manifest name lists in `bootstrap.sh` and `template_smoke_assertions.py` so that consumers who rename their workloads no longer experience silent CI failures in `generated-consumer-smoke` with no local pre-commit signal.
- Success metric: (1) A consumer repo where only consumer-named manifests exist under `base/apps/` (referenced in `kustomization.yaml`) passes both bootstrap and smoke validation without modification to either blueprint script; (2) no existing `generated-consumer-smoke` scenario regresses; (3) no hardcoded seed manifest filenames remain in `bootstrap_infra_static_templates()`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `bootstrap_infra_static_templates()` in `scripts/bin/infra/bootstrap.sh` MUST replace the four hardcoded `ensure_infra_template_file` calls for app workload manifests with a loop that reads resource filenames from the infra template kustomization at `$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml` using `sed` at runtime.
- FR-002 `validate_app_runtime_conformance()` in `scripts/lib/blueprint/template_smoke_assertions.py` MUST replace the hardcoded `app_manifest_paths` list with a dynamic derivation from the consumer repo's `infra/gitops/platform/base/apps/kustomization.yaml` using `_extract_kustomization_resources()`.
- FR-003 A new private function `_extract_kustomization_resources(text: str) -> list[str]` MUST be added to `scripts/lib/blueprint/template_smoke_assertions.py`; it MUST parse the `resources:` section of a kustomization YAML using stdlib `re` only (no PyYAML dependency), returning a list of resource filename strings.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce any authn/authz bypass, secret exposure, or privilege escalation. This fix reads only local YAML files in the blueprint source tree or consumer repo; no network calls, no secret handling.
- NFR-OBS-001 When the template kustomization cannot be found, `bootstrap.sh` MUST call `log_fatal` and halt. When it cannot be found or its resources list is empty, `validate_app_runtime_conformance()` MUST raise `AssertionError` with a message identifying the missing file or empty resources list.
- NFR-REL-001 MUST NOT regress any existing `generated-consumer-smoke` scenario. Rollback MUST be achievable by reverting the PR with no consumer-side action required.
- NFR-OPS-001 No new operational requirements. The fix is purely internal to blueprint tooling; no consumer-side changes are required to benefit from it.

## Normative Option Decision
- Option A: Replace hardcoded lists with dynamic derivation reading the template kustomization at runtime (chosen approach).
- Option B: Sync hardcoded lists via a generator script invoked on every kustomization change.
- Selected option: OPTION_A
- Rationale: Option A eliminates the root cause (redundant hardcoded lists) directly. Option B preserves the redundancy and requires a separate generator update step, which is itself error-prone.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no Make target or CLI signatures change
- Docs contract: none — no consumer-facing behavior change

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this IS the upstream blueprint fix)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: `validate_app_runtime_conformance()` passes on a consumer repo containing only consumer-named manifests (e.g. `marketplace-api-deployment.yaml`, `marketplace-api-service.yaml`) under `base/apps/`, provided those files are listed in `infra/gitops/platform/base/apps/kustomization.yaml` and contain `kind: Deployment` or `kind: Service` respectively.
- AC-002 MUST: A unit test confirms that `bootstrap_infra_static_templates()` no longer contains any of the four hardcoded blueprint seed filenames (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) as literal strings in its function body.
- AC-003 MUST: A unit test confirms that `_extract_kustomization_resources("resources:\n  - foo-deployment.yaml\n  - foo-service.yaml\n")` returns `["foo-deployment.yaml", "foo-service.yaml"]`.
- AC-004 MUST: All pre-existing `generated-consumer-smoke` scenarios (`local-lite-baseline`, `local-full-baseline`, `stackit-dev-baseline`) pass without modification to any scenario fixture.
- AC-005 MUST: `make infra-validate` and `make quality-hooks-fast` pass on the blueprint repo after all changes.

## Informative Notes (Non-Normative)
- Context: Reported by consumer sbonoc/dhe-marketplace from their v1.7.0 upgrade experience. Related to #206 (contract schema) and #207 (prune exclusion), but mechanically independent — this fix requires no schema change.
- Tradeoffs: The `sed` parser in `bootstrap.sh` matches only `.yaml`-suffixed resource entries. This is acceptable because all Kubernetes manifest files use `.yaml`. The `_extract_kustomization_resources()` stdlib parser handles the simple flat `resources:` list format used by all blueprint-controlled kustomizations.
- Clarifications: none.

## Explicit Exclusions
- Contract schema changes to `required_files` and `required_paths_when_enabled` (tracked as #206).
- Prune exclusion for `infra/gitops/platform/base/apps/` (tracked as #207).
- Any changes to how kustomize build validates workload kinds (existing mechanism unchanged).
