# Specification

## Spec Readiness Gate (Blocking)
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
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: chore
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001
- Control exception rationale: stub-template label cleanup — no runtime logic, API, event contract, or security surface changed. Templates emit `status=not_implemented` until consumers replace the body.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
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
- Business outcome: Align `managed-cache` module-wrapper stub templates with the established hyphenated state-file-label convention already in use by other multi-word modules (`secrets-manager`, `public-endpoints`), so observability data from the stub-invocation metric is consistent across modules.
- Success metric: All multi-word module-wrapper stub templates emit `write_state_file "<module-name>_<action>"` (hyphen between words inside the module name, underscore before the action).

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 The four `managed-cache` template wrappers (`managed_cache_apply.sh.tmpl`, `managed_cache_destroy.sh.tmpl`, `managed_cache_plan.sh.tmpl`, `managed_cache_smoke.sh.tmpl`) MUST call `write_state_file` with first arguments `"managed-cache_apply"`, `"managed-cache_destroy"`, `"managed-cache_plan"`, `"managed-cache_smoke"` respectively (hyphen between `managed` and `cache`).

### Acceptance Criteria
- AC-001 `grep -n 'write_state_file "managed_cache_' scripts/templates/infra/module_wrappers/managed-cache/` MUST return zero matches.
- AC-002 `grep -n 'write_state_file "managed-cache_' scripts/templates/infra/module_wrappers/managed-cache/` MUST return exactly four matches (one per template).
