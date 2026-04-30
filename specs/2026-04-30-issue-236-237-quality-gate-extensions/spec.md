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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260430-issue-236-237-quality-gate-extensions.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-001 not applicable (no blocked inputs); SDD-C-009 not applicable (no authn/authz or secret handling); SDD-C-010 not applicable (no new observability-operated paths — tooling-only change); SDD-C-013/SDD-C-014 not applicable (no STACKIT managed service or Kubernetes runtime); SDD-C-015 not applicable (no app onboarding Make-target contract changes); SDD-C-018 not applicable (no upstream workaround lifecycle); SDD-C-022/SDD-C-023/SDD-C-024 not applicable (no HTTP routes, filter logic, or pre-PR smoke findings)

## Implementation Stack Profile (Normative)
- Backend stack profile: N/A — blueprint tooling (Makefile, pre-commit YAML, Python contract tests)
- Frontend stack profile: N/A — no UI
- Test automation profile: pytest (contract assertions in test_quality_contracts.py)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: blueprint tooling and governance scope only; no consumer application code, no runtime infrastructure, no STACKIT managed service, no Kubernetes changes
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: blueprint tooling only; no runtime infrastructure or Kubernetes changes in this work item

## Objective
- Business outcome: Eliminate the class of CI failures caused by stale pnpm lockfiles (Issue #236) and the class of upgrade merge conflicts caused by consumer-added pre-push hooks or CI steps (Issue #237). Combined, these two changes give consumers a zero-conflict, framework-agnostic extension point for test tiers while surfacing lockfile drift locally before it reaches CI.
- Success metric: After upgrade: (1) consumers with `pnpm-lockfile-sync` hook catch stale lockfiles at pre-push instead of at CI; (2) consumers can override `quality-consumer-pre-push` and `quality-consumer-ci` in `platform.mk` without touching `.pre-commit-config.yaml` or `blueprint.generated.mk`, eliminating merge-conflict risk on blueprint upgrade.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The `.pre-commit-config.yaml` bootstrap template MUST include a `pnpm-lockfile-sync` pre-push hook that runs `pnpm install --frozen-lockfile --prefer-offline` and triggers on any file matching `(^|/)package\.json$` across the workspace.
- FR-002 The `pnpm-lockfile-sync` hook MUST set `pass_filenames: false` and `stages: [pre-push]` so it runs only at push time and does not pass file names to the pnpm command.
- FR-003 The `blueprint.generated.mk` template MUST define a `quality-consumer-pre-push` no-op `.PHONY` stub target with body `@true` and a doc comment indicating consumers override it in `platform.mk`.
- FR-004 The `blueprint.generated.mk` template MUST define a `quality-consumer-ci` no-op `.PHONY` stub target with body `@true` and a doc comment indicating consumers override it in `platform.mk`.
- FR-005 The `.pre-commit-config.yaml` bootstrap template MUST include a `quality-consumer-pre-push` pre-push hook that calls `make quality-consumer-pre-push`, with `pass_filenames: false`, `stages: [pre-push]`, and `always_run: true`.
- FR-006 The `quality-ci-blueprint` recipe in the `blueprint.generated.mk` template MUST call `@$(MAKE) quality-consumer-ci` as its final step so consumer CI extensions run as part of the standard CI lane.
- FR-007 The consumer-init AGENTS.md template (`scripts/templates/consumer/init/AGENTS.md.tmpl`) MUST be updated to document `quality-consumer-pre-push` and `quality-consumer-ci` in the quality gate section with tier placement convention (Tier 1/unit → `quality-consumer-pre-push`; Tier 2/component → `quality-consumer-ci`).

### Non-Functional Requirements (Normative)
- NFR-REL-001 All changes MUST be additive only — existing consumers who do not override the stubs MUST see no behavior change (stubs are no-ops; the lockfile hook exits 0 when the lockfile is consistent).
- NFR-UPG-001 Consumer test-tier overrides MUST be placeable in `platform.mk` (consumer-owned, never overwritten on blueprint upgrade) so consumers accumulate overrides without merge-conflict risk.
- NFR-A11Y-001 N/A — tooling and governance change; no UI components.

## Normative Option Decision
- Option A: Inline `make quality-consumer-ci` directly in `quality-ci-blueprint` (chosen).
- Option B: Document `make quality-consumer-ci` as a consumer-positioned step in `ci.yml` only, not wired into `quality-ci-blueprint`.
- Selected option: OPTION_A
- Rationale: Option A ensures the consumer CI extension always runs in the standard lane regardless of how the consumer structures their `ci.yml`. Option B requires consumers to remember to position the call manually and does not provide a contract-enforced extension point. Option A is consistent with how `quality-a11y-acr-check` was wired into `quality-hooks-fast` (PR #243).

## Contract Changes (Normative)
- Config/Env contract: None — no new environment variables.
- API contract: None — no HTTP endpoints.
- OpenAPI / Pact contract path: none
- Event contract: None — no async messaging.
- Make/CLI contract: Two new consumer Make targets added: `quality-consumer-pre-push` and `quality-consumer-ci` (both `.PHONY`, no-op by default). `quality-ci-blueprint` recipe extended with `@$(MAKE) quality-consumer-ci`.
- Docs contract: `docs/blueprint/governance/quality_hooks.md` updated with consumer extension target documentation. `docs/platform/consumer/` new or updated consumer guide for overriding the extension stubs. `scripts/templates/consumer/init/AGENTS.md.tmpl` updated to document `quality-consumer-pre-push` and `quality-consumer-ci` with tier placement convention.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` MUST contain an entry with `id: pnpm-lockfile-sync`, `stages: [pre-push]`, and `files: (^|/)package\.json$`.
- AC-002 `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` MUST contain an entry with `id: quality-consumer-pre-push` and `stages: [pre-push]`.
- AC-003 `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` MUST contain a `quality-consumer-pre-push` target with body `@true`.
- AC-004 `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` MUST contain a `quality-consumer-ci` target with body `@true`.
- AC-005 The `quality-ci-blueprint` recipe in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` MUST contain `$(MAKE) quality-consumer-ci`.
- AC-006 All six assertions above (AC-001 through AC-005 and AC-007) MUST pass as automated contract assertions in `tests/blueprint/test_quality_contracts.py` via `make infra-contract-test-fast`.
- AC-007 `scripts/templates/consumer/init/AGENTS.md.tmpl` MUST contain `quality-consumer-pre-push` and `quality-consumer-ci` strings with tier placement documentation.

## Informative Notes (Non-Normative)
- Context: The `pnpm-lockfile-sync` hook uses `--prefer-offline` to avoid network traffic at pre-push time; it relies on the local pnpm content-addressable store. The `files: (^|/)package\.json$` pattern covers both the workspace root and all sub-package manifests. The `quality-consumer-pre-push` and `quality-consumer-ci` stubs are no-ops until the consumer overrides them in `platform.mk`. The stubs are delivered via `blueprint.generated.mk` (blueprint-managed, not consumer-owned), so they are always present after upgrade without consumer action.
- Tradeoffs: By routing consumer pre-push hooks through a single make target, the consumer loses pre-commit's `files:` pattern filtering for their custom test tiers. This is acceptable for pre-push hooks (infrequent) and the consumer can implement changed-file checks inside the target body if needed.
- Clarifications: none

## Explicit Exclusions
- Consumer-specific test implementations: consumers own the body of `quality-consumer-pre-push` and `quality-consumer-ci` in `platform.mk`; this work item only delivers the stubs and wiring.
- The live blueprint repo's own `.pre-commit-config.yaml` (root) will receive the `quality-consumer-pre-push` hook to keep the blueprint repo consistent with consumer repos; the `pnpm-lockfile-sync` hook is omitted from the blueprint repo's own config as the blueprint repo does not manage a pnpm workspace.
- SDD-C-015 app onboarding minimum targets are unaffected; this work item adds no app delivery Make targets.
