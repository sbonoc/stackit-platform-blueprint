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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-272-273-v110-docs-hotfix.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-007: Blueprint tooling layer (bash shell scripts); no DDD/Clean Architecture layer separation applies.
  - SDD-C-013: No STACKIT managed services in scope.
  - SDD-C-014: Shell script tooling — no k8s runtime, Crossplane, ESO, ArgoCD, or Keycloak involvement.
  - SDD-C-015: No app delivery workflow or Make-target contract affected.
  - SDD-C-018: N/A — this work item IS the upstream blueprint fix; no consumer-side workaround tracking is needed here.
  - SDD-C-022: No HTTP routes, filters, or API endpoints touched.
  - SDD-C-023: No filter or payload-transform logic introduced.

## Implementation Stack Profile (Normative)
- Backend stack profile: bash (pure shell script changes in `scripts/lib/docs/site.sh`; no Python modules or FastAPI involved)
- Frontend stack profile: none
- Test automation profile: pytest (content-level regression tests asserting bash script text)
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint tooling scripts only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: bash script executes without k8s runtime; Crossplane/ESO/ArgoCD/Keycloak not involved

## Objective
- Business outcome: Every consumer upgrading to v1.10.0 MUST be able to run `make docs-build` and `make docs-smoke` successfully without `docs/node_modules/` being silently empty on repos whose `pnpm-workspace.yaml` excludes `docs/`. The pnpm version mismatch error message MUST name all three sources of active pnpm version truth so consumers can resolve drift without manual investigation. Closes issues #272, #273.
- Success metric: A generated-consumer repo with a root `pnpm-workspace.yaml` that excludes `docs/` MUST pass `make docs-install && make docs-build` after upgrading to the fixed blueprint, with no consumer-side workaround required.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `docs_pnpm_install`, `docs_pnpm_build`, and `docs_pnpm_start` in `scripts/lib/docs/site.sh` MUST each pass the `--ignore-workspace` flag to their respective `pnpm` invocations, restoring the standalone-install contract that was present before v1.10.0. The explanatory comment documenting why `--ignore-workspace` is required MUST be restored alongside the `docs_pnpm_install` call.
- FR-002 The `log_fatal` message emitted by `_docs_assert_pnpm_version` on a version mismatch MUST enumerate all three sources of active pnpm version truth in the consumer repo: (1) the docs `package.json` `packageManager` field (the canonical contract the assertion enforces), (2) the root `package.json` `packageManager` field (auto-activated by corepack on any `pnpm install` from root), and (3) the CI prepare action's corepack prepare pin. The message MUST instruct the consumer to align all three to the docs `package.json` version.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 N/A — no authentication, authorization, or secret handling in scope; pnpm install flags and error message text do not affect security properties.
- NFR-OBS-001 Both fixes MUST preserve existing log output structure: `_docs_assert_pnpm_version` MUST continue to emit via `log_fatal` (not a different log function); the fatal-exit behavior on mismatch MUST remain unchanged.
- NFR-REL-001 Both fixes MUST be backward-compatible: consumers whose `pnpm-workspace.yaml` includes `docs/` continue to work; consumers who already pass the version assertion continue to pass.
- NFR-OPS-001 Regression tests for both fixes MUST be runnable via `uv run python3 -m pytest` without requiring a live k8s cluster, pnpm installation, or external network access.
- NFR-A11Y-001 N/A — no UI components; pure shell script changes with no user-facing rendering surface.

## Normative Option Decision
- Option A (minimal): Improve error message text in `_docs_assert_pnpm_version` only — enumerate all three pnpm version sources in the existing `log_fatal` call. No new Make targets, no new scripts, no new quality hooks.
- Option B (broader): Option A + add `make blueprint-align-pnpm-pins` Make target backed by `scripts/bin/blueprint/align_pnpm_pins.sh` that takes `docs/package.json` pin as canonical and rewrites all other `packageManager` fields in the repo to match (with dry-run support).
- Selected option: OPTION_A
- Rationale: This is a hotfix PR targeting a v1.10.0 regression. Option A fixes the exact user-visible problem (opaque error with no actionable guidance) with a one-line change and minimal blast radius. Option B introduces a new automation script and Make target in a hotfix context, expanding scope and review surface beyond what the blocking issue requires. The migration script is a valuable follow-on; it is parked as a proposal with `on-scope: blueprint` trigger for the next blueprint-scope work item.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no new Make targets; `make docs-install`, `make docs-build`, `make docs-smoke` behavior corrected (false-failure removed for consumers with non-workspace `docs/`)
- Docs contract: `docs/platform/consumer/troubleshooting.md` MUST be updated with a v1.10.0 docs build section documenting the --ignore-workspace regression and the pnpm version mismatch migration steps

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/272, https://github.com/sbonoc/stackit-platform-blueprint/issues/273
- Temporary workaround path: restore `--ignore-workspace` locally in consumer's `scripts/lib/docs/site.sh` (#272); manually align all `packageManager` fields to `docs/package.json` pin (#273)
- Replacement trigger: this PR merged to main and released; consumers MUST remove workarounds after adopting the patched blueprint version
- Workaround review date: 2026-08-12

## Normative Acceptance Criteria
- AC-001 Given a consumer repo whose `pnpm-workspace.yaml` globs do not include `docs/`, `make docs-install` MUST result in a populated `docs/node_modules/` and `make docs-build` MUST succeed (docusaurus binary found) after applying FR-001.
- AC-002 Given a repo where the active pnpm version differs from `docs/package.json#packageManager`, `_docs_assert_pnpm_version` MUST emit a `log_fatal` message that explicitly names the root `package.json` `packageManager` field and the CI corepack prepare pin as possible sources of the mismatched version, after applying FR-002.

## Informative Notes (Non-Normative)
- Context: Both defects were discovered during the dhe-marketplace consumer upgrade v1.7.0 → v1.10.0 (PR sbonoc/dhe-marketplace#62). The `--ignore-workspace` removal was a v1.10.0 regression; the explanatory comment that justified its presence was also removed. The strict pnpm version assertion was new in v1.10.0 and surfaced latent version drift that had accumulated without enforcement.
- Tradeoffs: Option A for #273 leaves consumers to manually update all `packageManager` fields (11 files in the reference consumer). A migration script (Option B) would reduce that toil but adds scope to this hotfix; it is deferred as a proposal.
- Clarifications: The `--ignore-workspace` flag is required because the docs site (`docs/`) is a self-contained Docusaurus workspace with its own `package.json` and `pnpm-lock.yaml`. It is intentionally excluded from consumer root `pnpm-workspace.yaml` to avoid dependency graph interference. Without `--ignore-workspace`, pnpm in workspace mode treats `docs/` as a workspace package and skips a standalone install, leaving `docs/node_modules/` empty.

## Explicit Exclusions
- A `blueprint-align-pnpm-pins` Make target or migration script is out of scope for this hotfix (parked as proposal).
- Preflight pnpm version drift detection via a new quality hook is out of scope (parked as proposal).
- Changes to the `python3 -c` inline one-liner used by `_docs_assert_pnpm_version` to read `packageManager` from `docs/package.json` are out of scope — the parsing logic is correct for the known input format.
- Consumer-side workaround removal is out of scope — consumers must remove workarounds themselves after adopting the patched blueprint version.
