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
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001
- Control exception rationale: pre-push hook wiring — no runtime logic, API, or security surface changed.

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
- Business outcome: Surface stale `blueprint/contract.yaml` `required_files` entries locally at pre-push rather than first in CI, so developers discover the gap before the `blueprint-quality` CI job fails.
- Success metric: Running `git push` after removing a `required_files`-listed path without updating `contract.yaml` fails locally with a clear error; all pre-push hooks continue to pass on a clean working tree.

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 `validate_contract.py` MUST expose a `--required-files-only` flag that runs only `_validate_required_files` against the mode-aware required_files list and exits non-zero when any listed path is absent.
- REQ-002 A `quality-validate-contract-required-files` make target MUST be defined in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and listed as PHONY; it MUST invoke `validate_contract.py --required-files-only`.
- REQ-003 An always-run `pre-push` hook named `quality-validate-contract-required-files` MUST be added to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` immediately before the `quality-validate-branch` hook.
- REQ-004 The same always-run `pre-push` hook MUST be added to the blueprint's own `.pre-commit-config.yaml` at the same position.

### Acceptance Criteria
- AC-001 `make quality-validate-contract-required-files` exits 0 on a clean working tree and exits non-zero after a `required_files`-listed path is temporarily removed.
- AC-002 `python3 scripts/bin/blueprint/validate_contract.py --required-files-only` exits 0 on a clean tree.
- AC-003 `make quality-hooks-fast` passes with no regressions.
- AC-004 `python3 -m pytest tests/blueprint/ -x -q` passes.
