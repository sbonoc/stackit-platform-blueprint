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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-284-302-local-dx-improvements.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-001 not applicable — no missing inputs. SDD-C-007 not applicable — tooling layer, no domain model. SDD-C-013 not applicable — local developer tooling, no managed service. SDD-C-014 not applicable — local-first IS the target profile for both changes. SDD-C-015 not applicable — no new make targets. SDD-C-018 not applicable — no blueprint-managed defect workaround. SDD-C-022, SDD-C-023, SDD-C-024 not applicable — no HTTP routes, filter logic, or smoke findings.

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: Both changes target the local development experience only. No STACKIT managed services are provisioned or modified.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none — both changes are exclusively local-lane improvements

## Objective
- Business outcome: Eliminate two friction points for engineers developing features on non-main branches in a local blueprint consumer environment: (1) local ArgoCD always syncing from `main` instead of the active branch, and (2) no standard place for persistent local env overrides that survives across shell sessions.
- Success metric: An engineer on a feature branch can run `make infra-deploy` and have ArgoCD track their branch without any manual `kubectl patch`. Any persistent local override (passwords, tokens, cluster settings) declared in `.env.local` is automatically picked up by every `make` target without a manual `source` step.

## Normative Requirements

### Functional Requirements (Normative)

#### Issue #302 — `.env.local` auto-load in bootstrap.sh

- FR-001: `scripts/lib/shell/bootstrap.sh` MUST call `load_env_file_defaults "$ROOT_DIR/.env.local"` so that `.env.local` is automatically sourced on every script and make target invocation that sources `bootstrap.sh`.
- FR-002: When `.env.local` is absent, `bootstrap.sh` MUST behave identically to its current behavior — `load_env_file_defaults` returns early with no side effects.
- FR-003: Variables already set in the caller's shell environment before `bootstrap.sh` is sourced MUST NOT be overridden by values in `.env.local` (shell env wins; `load_env_file_defaults` already preserves pre-existing exports).
- FR-004: `.env.local` MUST be added to the root `.gitignore`.
- FR-005: `.env.local` MUST be added to `scripts/templates/blueprint/bootstrap/.gitignore` so that every consumer repo generated from the template also ignores the file.

#### Issue #284 — `ARGOCD_LOCAL_TARGET_REVISION` in deploy.sh

- FR-006: `scripts/bin/infra/deploy.sh` MUST read `ARGOCD_LOCAL_TARGET_REVISION` (optional env var) after applying the local ArgoCD kustomize overlay and patch the ArgoCD Application `spec.source.targetRevision` when the effective revision differs from `main`.
- FR-007: When `ARGOCD_LOCAL_TARGET_REVISION` is unset or empty, `deploy.sh` MUST default to the current git branch via `git branch --show-current`.
- FR-008: The patch MUST be skipped (no `kubectl patch` executed) when the effective revision equals `main`.
- FR-009: The patch MUST be skipped when `git branch --show-current` returns an empty string (detached HEAD).
- FR-010: The patch MUST be skipped when the ArgoCD Application resource `platform-local-core` does not yet exist in the cluster (e.g., first deploy).
- FR-011: The `ARGOCD_LOCAL_TARGET_REVISION` env var MUST have no effect on any non-local `BLUEPRINT_PROFILE` value. STACKIT profiles MUST NOT patch the Application.
- FR-012: `deploy.sh` MUST log the effective `targetRevision` being patched when the patch is executed.
- FR-013: The patch operation MUST be idempotent — re-running `make infra-deploy` with the same revision MUST NOT produce an error.

### Non-Functional Requirements (Normative)
- NFR-SEC-001: `load_env_file_defaults` MUST NOT override variables already set in the caller's shell environment. This prevents `.env.local` from shadowing credentials or tokens exported by the CI/CD system or the developer's shell profile.
- NFR-SEC-002: `.env.local` MUST appear in both `.gitignore` files (FR-004, FR-005) to prevent accidental commits of local credential overrides.
- NFR-OBS-001: N/A — both changes are developer-tooling path only with no production runtime impact. The `deploy.sh` patch logs the effective revision (FR-012) as the only diagnostic requirement.
- NFR-REL-001: The `ARGOCD_LOCAL_TARGET_REVISION` patch MUST be idempotent (FR-013). `bootstrap.sh` auto-load MUST be a no-op when `.env.local` is absent (FR-002).
- NFR-OPS-001: No operator runbook changes required. Existing `make infra-deploy` documentation remains valid; the patch behavior is self-describing via log output (FR-012).
- NFR-A11Y-001: N/A — no UI surfaces introduced or modified.

## Normative Option Decision

### Issue #284 — deploy.sh runtime patch vs. kustomize overlay patch

- Option A: **deploy.sh runtime patch** — after `run_kustomize_apply "$overlay_path"` for the local profile, read `ARGOCD_LOCAL_TARGET_REVISION` and `kubectl patch` the Application if the effective revision differs from `main`. No manifest change needed.
- Option B: **Kustomize patch overlay** — add a `patches:` entry in `infra/gitops/argocd/overlays/local/kustomization.yaml` that reads `targetRevision` from an env-substituted or `.env`-sourced value.
- Selected option: OPTION_A
- Rationale: Option A keeps all manifests static and version-controlled as-is. Conditional patch logic is naturally expressed in shell. `deploy.sh` is already the orchestration point for local deploy and has `run_kubectl_with_active_access`. Option B would require either Kustomize `vars` (deprecated) or a generator plugin, adding complexity and coupling the manifest to a local-only mechanism. Option A matches the existing consumer workaround pattern (`kubectl patch` after apply) which the issue author already identified as the correct approach.

## Contract Changes (Normative)
- Config/Env contract: New optional env var `ARGOCD_LOCAL_TARGET_REVISION` (local profile only; default: `$(git branch --show-current)`; no effect on STACKIT profiles). New developer convention: `$ROOT_DIR/.env.local` is auto-loaded by `bootstrap.sh` and gitignored.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: No new make targets. `make infra-deploy` behavior changes on local profile when the effective revision differs from `main` — the ArgoCD Application is patched post-apply. No interface change for STACKIT profiles.
- Docs contract: `docs/platform/local-development.md` (if it exists) MUST be updated to document `ARGOCD_LOCAL_TARGET_REVISION` and `.env.local` conventions.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001: After `make infra-deploy` on a local profile with `ARGOCD_LOCAL_TARGET_REVISION=my-feature-branch` set, the ArgoCD Application `platform-local-core` in the cluster has `spec.source.targetRevision: my-feature-branch`.
- AC-002: After `make infra-deploy` on a local profile with `ARGOCD_LOCAL_TARGET_REVISION` unset and `git branch --show-current` returning `my-feature-branch`, the Application has `targetRevision: my-feature-branch`.
- AC-003: After `make infra-deploy` on a local profile with effective revision `main` (var unset and on main branch), no `kubectl patch` call is made.
- AC-004: `make infra-deploy` on any STACKIT profile never patches the Application `targetRevision` regardless of `ARGOCD_LOCAL_TARGET_REVISION` value.
- AC-005: A `.env.local` file containing `MY_TEST_VAR=from-env-local` causes `MY_TEST_VAR` to be present in the environment of any script sourcing `bootstrap.sh`, when `MY_TEST_VAR` was not already exported in the caller's shell.
- AC-006: A pre-existing `MY_TEST_VAR=from-shell` exported in the caller's shell is NOT overridden by `MY_TEST_VAR=from-env-local` in `.env.local`.
- AC-007: `.env.local` appears in `.gitignore` and in `scripts/templates/blueprint/bootstrap/.gitignore`.
- AC-008: At least 8 automated pytest assertions cover the above acceptance criteria.

## Informative Notes (Non-Normative)
- Context: The `kubectl patch` approach for #284 replicates the existing consumer-side workaround documented in `sbonoc/dhe-marketplace`. Bringing it into the blueprint ensures every consumer gets it automatically on the next uplift. The `.env.local` pattern for #302 is likewise sourced from the same consumer repo's local credential management PR.
- Tradeoffs: The runtime patch for #284 means ArgoCD's Application CRD in the cluster will diverge from the manifest on disk when not on `main`. This is intentional and expected for local development; the manifest is the canonical `main`-branch definition.
- Clarifications: none
