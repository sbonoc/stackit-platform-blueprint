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
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-358-touchpoints-contracts-pre-push.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale: SDD-C-013 — template modification only, no managed service dependency introduced; SDD-C-014 — template file addition introduces no local Kubernetes runtime execution path; SDD-C-018 — no upstream blueprint defect workaround; SDD-C-022 — no HTTP route handlers or new API endpoints; SDD-C-023 — no filter or payload-transform logic

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: template modification only; no managed service dependency is introduced by this change
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: template file modification adds a pre-commit hook; no local Kubernetes or Docker Desktop runtime execution path is introduced; stack profile fields carry standard defaults per blueprint governance
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals found in title or labels (ci-cd, enhancement) — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: Consumers gain three file-scoped pre-push gates that catch regressions (Vitest composable failures, Pact interaction failures, pytest DSL/query regressions) before they reach CI, reducing review latency and CI noise across all test lanes.
- Success metric: All three hook IDs are present in the template with correct field values after blueprint upgrade; each invoked make target exits 0 when no matching files are staged or when the relevant test directory is absent.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The `touchpoints-test-unit-pre-push` hook MUST be added to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` with `id: touchpoints-test-unit-pre-push`, `name: touchpoints unit tests (pre-push)`, `language: system`, `entry: make touchpoints-test-unit`, `pass_filenames: false`, `stages: [pre-push]`, `files: ^apps/touchpoints/.*\.(ts|vue|tsx)$`, and `always_run: false`.
- FR-002 The `touchpoints-test-contracts-pre-push` hook MUST be added to the same template with `id: touchpoints-test-contracts-pre-push`, `name: touchpoints contract tests (pre-push)`, `language: system`, `entry: make touchpoints-test-contracts`, `pass_filenames: false`, `stages: [pre-push]`, `files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`, and `always_run: false`. The `files` pattern MUST be broader than FR-001 to cover api-client source changes that can break Pact interactions independently of touchpoints UI code.
- FR-003 The `backend-test-unit-pre-push` hook MUST be added to the same template with `id: backend-test-unit-pre-push`, `name: backend unit tests (pre-push)`, `language: system`, `entry: make backend-test-unit`, `pass_filenames: false`, `stages: [pre-push]`, `files: ^(apps/backend/|tests/backend/).*\.py$`, and `always_run: false`.
- FR-004 Each hook MUST NOT execute when no files matching its respective `files` regex are staged for the push; `always_run: false` SHALL guarantee this behaviour, making each hook a no-op for consumers without matching source files.
- FR-005 Consumers that upgrade their `.pre-commit-config.yaml` from the updated template MUST automatically gain all three pre-push gates without any manual configuration step beyond the standard blueprint upgrade flow.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 N/A — all three hooks invoke only local make targets (`touchpoints-test-unit`, `touchpoints-test-contracts`, `backend-test-unit`) with no secret-handling or credential-exposure surface; no new authn/authz path is introduced.
- NFR-OBS-001 N/A — pre-commit hook output is terminal-only; no log, metric, or trace infrastructure is required or modified by this change.
- NFR-REL-001 Each hook MUST exit 0 when its relevant test directory is absent or when no matching files are staged, preserving push-path availability for consumers that do not yet have the relevant test suite.
- NFR-OPS-001 Blueprint upgrade documentation MUST include a backport note for consumers running an earlier template version, describing all three new hook IDs, their `files` trigger patterns, and the make targets they invoke.
- NFR-A11Y-001 N/A — no user interface; this is a template file modification only.

## Normative Option Decision
- Option A: Add all three hooks (touchpoints-unit, touchpoints-contracts, backend-unit) with `always_run: false` and lane-specific file globs; each hook is skipped automatically when no matching files are staged.
- Option B: Add only `touchpoints-test-contracts-pre-push` as the original issue filed, leaving the unit and backend hooks consumer-local; new consumers bootstrapping from the template would lack the unit pre-push gates.
- Selected option: OPTION_A
- Rationale: OPTION_A ships the complete shift-left pattern as a single atomic template change. The unit and backend hooks are documented in dhe-marketplace with postmortems (PR #75, PR #78) that justify their presence; leaving them consumer-local means new consumers silently miss them. All three hooks follow the same `always_run: false` + file-scope pattern, so the template change is uniform. OPTION_B creates a template that is structurally incomplete relative to the known consumer need.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `touchpoints-test-unit`, `touchpoints-test-contracts`, and `backend-test-unit` make targets already exist in `make/platform.mk`; no new target is introduced
- Docs contract: blueprint upgrade release notes MUST document all three new hooks with their `files` trigger patterns; a backport note is required for consumers running an earlier template version

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [touchpoints-test-unit-pre-push present in template with all required fields] — verified by T-101, which MUST assert that `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` contains a hook with `id: touchpoints-test-unit-pre-push`, `entry: make touchpoints-test-unit`, `stages: [pre-push]`, `files: ^apps/touchpoints/.*\.(ts|vue|tsx)$`, `pass_filenames: false`, and `always_run: false`.
- AC-002 [touchpoints-test-contracts-pre-push present in template with all required fields] — verified by T-102, which MUST assert that the template contains a hook with `id: touchpoints-test-contracts-pre-push`, `entry: make touchpoints-test-contracts`, `stages: [pre-push]`, `files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`, `pass_filenames: false`, and `always_run: false`.
- AC-003 [backend-test-unit-pre-push present in template with all required fields] — verified by T-103, which MUST assert that the template contains a hook with `id: backend-test-unit-pre-push`, `entry: make backend-test-unit`, `stages: [pre-push]`, `files: ^(apps/backend/|tests/backend/).*\.py$`, `pass_filenames: false`, and `always_run: false`.
- AC-004 [no hook runs on commit-stage] — verified by T-104, which MUST assert that all three hook definitions set `always_run: false` and declare `stages: [pre-push]` only, confirming commit-time flows are not blocked.
- AC-005 [template drift check passes after all three hooks are added] — verified by T-105, which MUST assert that `make quality-validate-bootstrap-template-drift` exits 0 after the template modification, confirming no drift is introduced.

## Informative Notes (Non-Normative)
- Context: Issue #358 was filed by an agent in the context of the `sbonoc/dhe-marketplace` consumer repo. Investigation of that repo confirmed that `touchpoints-test-unit-pre-push` and `backend-test-unit-pre-push` exist consumer-locally and are not seeded by the blueprint template. Both carry PR postmortem comments (PR #75, PR #78) documenting real regressions they caught. Expanding scope to include all three hooks is the complete fix; shipping only the contracts hook would leave new consumers with an asymmetric template missing the unit gates. Three regression classes are addressed: Vitest composable failures (touchpoints-unit), Pact mock-server interaction failures and FFI timing differences (touchpoints-contracts), and pytest DSL/query regressions (backend-unit).
- Tradeoffs: File-scoped trigger (OPTION_A) adds no push latency for unrelated changes; the tradeoff is that a regression injected via a dependency update (with no source file touched) would not be caught by any of these gates.
- Clarifications: none

## Explicit Exclusions
- Modifying any of the three make targets (`touchpoints-test-unit`, `touchpoints-test-contracts`, `backend-test-unit`): all targets are declared correct in `make/platform.mk`; target implementation changes are out of scope.
- Modifying `blueprint/contract.yaml`: the issue explicitly states no contract.yaml impact.
- Adding `backend-test-contracts-pre-push` or `touchpoints-test-integration-pre-push` hooks: no consumer postmortem or active request recorded; these are separate work items if needed.

## Potential Deferred Proposals
- Add `backend-test-contracts-pre-push` hook: same file-scoped pre-push pattern; no active consumer postmortem recorded for Pact provider test regressions slipping through pre-push.
- Add `touchpoints-test-integration-pre-push` hook: applies if a consumer documents integration-lane regressions that pre-push would catch; no current postmortem evidence.
