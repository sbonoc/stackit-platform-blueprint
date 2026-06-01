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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-358-touchpoints-contracts-pre-push.md
- ADR status: proposed
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
- Business outcome: Consumers with Pact HTTP consumer contract tests gain a pre-push gate that catches contract regressions (broken request shapes, missing headers, FFI timing differences between macOS ARM64 and Linux x86_64) before they reach CI, reducing review latency and CI noise.
- Success metric: `make touchpoints-test-contracts` exits 0 when no matching files are staged or when the contracts directory is absent; the hook ID is present in the template with all required fields after the blueprint upgrade.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The `touchpoints-test-contracts-pre-push` hook MUST be added to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` with `id: touchpoints-test-contracts-pre-push`, `name: touchpoints contract tests (pre-push)`, `language: system`, `entry: make touchpoints-test-contracts`, `pass_filenames: false`, `stages: [pre-push]`, `files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`, and `always_run: false`.
- FR-002 The hook MUST NOT execute when no files matching the `files` regex are staged for the push; `always_run: false` SHALL guarantee this behaviour, making the hook a no-op for consumers without matching touchpoints or api-client source files.
- FR-003 Consumers that upgrade their `.pre-commit-config.yaml` from the updated template MUST automatically gain the pre-push contract gate without any manual configuration step beyond the standard blueprint upgrade flow.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 N/A — the hook invokes only `make touchpoints-test-contracts`, a local make target with no secret-handling or credential-exposure surface; no new authn/authz path is introduced.
- NFR-OBS-001 N/A — pre-commit hook output is terminal-only; no log, metric, or trace infrastructure is required or modified by this change.
- NFR-REL-001 The hook MUST exit 0 when the `tests/contracts/` directory is absent or when no matching files are staged, preserving push-path availability for consumers that do not yet have Pact contract tests.
- NFR-OPS-001 Blueprint upgrade documentation MUST include a backport note for consumers running an earlier template version that have Pact contract tests, describing the new hook ID, its `files` trigger pattern, and the make target it invokes.
- NFR-A11Y-001 N/A — no user interface; this is a template file modification only.

## Normative Option Decision
- Option A: Add the hook with `always_run: false` and the specific file glob `^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`; hook is skipped automatically when no matching files are staged.
- Option B: Add the hook with `always_run: true`; contract tests run on every push regardless of which files changed; simpler configuration but adds push latency for commits unrelated to touchpoints or api-client.
- Selected option: OPTION_A
- Rationale: OPTION_A mirrors the pattern used by every other pre-push hook in the template (audit-version, lockfile-sync, docs-check-changed) which use file-scoped triggers rather than always-run. Push latency stays minimal for pushes that do not touch touchpoints or api-client source.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `touchpoints-test-contracts` make target already exists in `make/platform.mk`; no new target is introduced
- Docs contract: blueprint upgrade release notes MUST document the new hook and its `files` trigger pattern; a backport note is required for consumers with Pact contract tests running an earlier blueprint template version

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [hook present in template with all required fields] — verified by T-101, which MUST assert that `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` contains a hook entry with `id: touchpoints-test-contracts-pre-push`, `entry: make touchpoints-test-contracts`, `stages: [pre-push]`, `files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$`, `pass_filenames: false`, and `always_run: false`.
- AC-002 [hook does not run on commit-stage and is absent from always-run hooks] — verified by T-102, which MUST assert that the hook definition sets `always_run: false` and that `pre-push` is the only declared stage, confirming commit-time flows are not blocked.
- AC-003 [template drift check passes after hook addition] — verified by T-103, which MUST assert that `make quality-validate-bootstrap-template-drift` exits 0 after the hook is added to the template, confirming no drift is introduced between the modified template and any blueprint-managed derived file.

## Informative Notes (Non-Normative)
- Context: Two regression classes motivate this gate — logic regressions (broken Pact interactions caught only by the contract lane, which starts a Pact mock server; the unit lane does not) and environment-dependent failures (FFI timing differences between macOS ARM64 developer machines and Linux x86_64 CI runners). Without a pre-push gate these regressions first appear as CI failures on the remote branch. Note: a grep of the current blueprint repository found no existing `touchpoints-test-unit-pre-push` hook in the template; the issue describes it as an existing companion, but it is possibly removed or lives in a consumer-local config outside the seeded template.
- Tradeoffs: File-scoped trigger (OPTION_A) adds no push latency for unrelated changes; the tradeoff is that a broken matcher injected via a dependency update (with no touchpoints source file touched) would not be caught by this gate alone.
- Clarifications: none

## Explicit Exclusions
- Adding `touchpoints-test-unit-pre-push` to the template if currently absent: the issue describes the unit hook as an existing companion; if verification finds it is absent, that is a separate work item.
- Modifying the `touchpoints-test-contracts` make target: the target is declared correct in `make/platform.mk`; target implementation changes are out of scope.
- Modifying `blueprint/contract.yaml`: the issue explicitly states no contract.yaml impact.
- Adding a pre-push hook for `backend-test-contracts`: the issue is scoped to the touchpoints (consumer frontend) contract lane only.

## Potential Deferred Proposals
- Add `touchpoints-test-unit-pre-push` to template if absent: the issue references this as an existing companion hook; if verification finds it is not in the current template, adding it is a separate work item with its own spec.
- Add `backend-test-contracts-pre-push` hook: the same dual-regression-class argument applies to backend Pact provider tests; no active consumer request recorded.
