# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260423-issue-160-bootstrap-consumer-seeded-paths-guard.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-012
- Control exception rationale: none

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
- Business outcome: Generated-consumer repos that replace blueprint placeholder manifests with consumer-specific ones can delete the placeholder files from git without `make infra-bootstrap` recreating them on every fresh checkout.
- Success metric: A consumer that declares a path as `consumer_seeded` in `blueprint/contract.yaml` can delete that file from git and run `make infra-bootstrap` without the file being recreated.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `ensure_infra_template_file` MUST, when running in a generated-consumer repo, skip template recreation for any path declared as `consumer_seeded` in `blueprint/contract.yaml`, regardless of whether the file is present on disk.
- FR-002 `ensure_infra_rendered_file` MUST, when running in a generated-consumer repo, skip rendered-file recreation for any path declared as `consumer_seeded` in `blueprint/contract.yaml`, regardless of whether the file is present on disk.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The consumer-seeded check MUST use the existing `blueprint_path_is_consumer_seeded` helper; no new env vars, subprocess calls, or shell-injection vectors are introduced.
- NFR-OBS-001 Bootstrap MUST emit an `infra_consumer_seeded_skip_count` metric counting total paths skipped due to consumer ownership, and MUST emit a `log_info` diagnostic per skipped path.
- NFR-REL-001 File absence on disk is valid consumer intent for consumer-seeded paths; bootstrap MUST not fail or warn when a consumer-seeded path is absent.
- NFR-OPS-001 The skip diagnostic MUST include the relative path so operators can identify which files were skipped during bootstrap.

## Normative Option Decision
- Option A: Add `blueprint_path_is_consumer_seeded` guard to `ensure_infra_template_file` and `ensure_infra_rendered_file`, mirroring the existing `blueprint_path_is_init_managed` guard.
- Option B: Leave as-is; document workaround (keep placeholder files committed at template content).
- Selected option: Option A
- Rationale: Option B is the current workaround documented in the issue; it leaves functionally inert files in git and creates confusion. Option A is consistent with the existing `init_managed` pattern and the blueprint's first-class `consumer_seeded` path class. No heuristics or new contracts are needed — the fix is purely additive.

## Contract Changes (Normative)
- Config/Env contract: none.
- API contract: none.
- Event contract: none.
- Make/CLI contract: none; `make infra-bootstrap` behavior extended non-destructively (new skip path for consumer-seeded paths).
- Docs contract: none.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/160
- Temporary workaround path: keep unwanted placeholder files committed at template content.
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 A path declared as `consumer_seeded` in `blueprint/contract.yaml` is NOT recreated by `make infra-bootstrap` when absent from disk in a generated-consumer repo.
- AC-002 `infra_consumer_seeded_skip_count` metric appears in bootstrap stdout output when at least one consumer-seeded path is skipped.
- AC-003 Paths NOT declared as `consumer_seeded` continue to be created from their template (no regression).

## Informative Notes (Non-Normative)
- Context: Issue #160 reports that consumers replacing generic placeholder manifests (e.g. `backend-api-deployment.yaml`) with consumer-specific ones cannot delete the placeholder files from git because bootstrap unconditionally recreates them.
- Tradeoffs: Explicit declaration in `contract.yaml` is preferred over auto-detection heuristics; the blueprint already uses this pattern for `init_managed_paths`.
- Clarifications: none

## Explicit Exclusions
- Changing the behavior of paths that are `init_managed` is out of scope; those paths still fail fatally when absent.
- Adding new `consumer_seeded` entries to the blueprint's own `contract.yaml` is out of scope; consumers manage their own declarations.
