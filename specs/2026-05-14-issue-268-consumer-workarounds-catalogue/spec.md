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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-268-consumer-workarounds-catalogue.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale:
  - SDD-C-010 (observability): pipeline logs are the only observability surface; no metrics, traces, or dashboards scope; logging requirements are captured in FR-007
  - SDD-C-013 (STACKIT managed services): N/A — no runtime capability provisioning
  - SDD-C-014 (local-first runtime baseline): N/A — no Kubernetes or Crossplane scope
  - SDD-C-015 (app onboarding make targets): N/A — no app delivery workflow scope
  - SDD-C-018 (blueprint upstream defect escalation): N/A — this spec implements the workaround catalogue mechanism itself; it does not apply a consumer-side workaround to a blueprint defect
  - SDD-C-022 (HTTP route/filter smoke): N/A — no HTTP endpoint scope

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none — skill tooling only; no UI components
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no runtime provisioning scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A — upgrade tooling only; no local runtime provisioning scope

## Objective
- Business outcome: Eliminate per-consumer rediscovery of blueprint-version-specific upstream defects by shipping a versioned workaround catalogue inside the consumer-upgrade skill. The pipeline automatically applies catalogue entries matching the target version, logs each application, and reverts them when the upstream fix is adopted in a later version. A representative upgrade that previously required ~30 min of trial-and-error to discover and apply 4 workarounds (as in dhe-marketplace v1.7.0 → v1.10.0) MUST complete with zero manual workaround steps.
- Success metric: (1) `workarounds/manifest.yaml` is present and schema-valid. (2) Pipeline applies all matching workarounds and logs each with id, title, and outcome. (3) `artifacts/blueprint/workarounds_applied.json` is written after application. (4) A `contract_merge` workaround applies and reverts cleanly in an automated test with a synthetic blueprint version. (5) A workaround whose `applies_when` does not match is skipped. (6) The initial catalogue ships entries for issues #258, #259, #260, #261.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001: Blueprint MUST ship a versioned workaround catalogue at `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml`. The manifest MUST declare per-target-blueprint-version workarounds. The manifest schema version MUST be `1`.

- FR-002: Each workaround entry in the manifest MUST carry the following fields: `id` (string, unique per version block), `upstream_issue` (URL string), `title` (string), `applies_when` (map or literal `always`), `action_kind` (one of `contract_merge`, `patch`, `python_script`), `action_path` (string, relative to skill root), `apply_phase` (one of `before_apply`, `after_apply`), `landed_in` (nullable version string).

- FR-003: The pipeline MUST execute workarounds in two phases keyed by the `apply_phase` field. Stage 1c (before Stage 2) MUST apply all entries with `apply_phase: before_apply`; Stage 2c (after Stage 2) MUST apply all entries with `apply_phase: after_apply`. In both phases the pipeline MUST evaluate `applies_when` against the consumer's current `blueprint/contract.yaml` (specifically `repo_mode`) and apply only matching entries in manifest order. This two-phase model (Option A, decided by owner comment on PR #292, 2026-05-14) makes execution ordering explicit in the manifest and enables `patch` workarounds on blueprint-managed files to survive Stage 2's file overwrite.

- FR-004: Each applied workaround MUST produce a log line: `[PIPELINE] Stage 1c: applied workaround #<id> — <title>`. Each skipped workaround MUST produce: `[PIPELINE] Stage 1c: skipped workaround #<id> — <title> (applies_when mismatch)`.

- FR-005: After all Stage 1c workarounds are applied, the pipeline MUST write `artifacts/blueprint/workarounds_applied.json` with the list of applied workaround ids, their titles, action kinds, and the target blueprint version.

- FR-006: When the target blueprint version is >= a workaround's `landed_in` value (non-null), AND the consumer's `artifacts/blueprint/workarounds_applied.json` lists that workaround as previously applied, the pipeline MUST revert the workaround before applying new workarounds for the current version.

- FR-007: The pipeline MUST log each revert: `[PIPELINE] Stage 1c: reverted workaround #<id> — <title> (landed in <version>)`.

- FR-008: The initial catalogue MUST ship workaround entries for v1.10.0 issues #258, #259, #260, and #261 as specified in the issue body. The v1.10.0 entries MUST ship with `landed_in: null` (fixes are on `main` via PR #274 but no new release tag has been cut yet). The catalogue maintainer MUST bump each `landed_in` value to the actual release tag in the same PR that cuts the next blueprint release. (Option A, decided by owner comment on PR #292, 2026-05-14.)

- FR-009: Workaround application MUST be idempotent — applying an already-applied workaround MUST produce a log entry and exit 0 without mutating the working tree again.

- FR-010: Workaround application failure MUST follow a per-`action_kind` policy (Option C, decided by owner comment on PR #292, 2026-05-14): `contract_merge` failures MUST be fatal (pipeline exits non-zero) because a partial YAML write corrupts `blueprint/contract.yaml` before Stage 2 reads it. `patch` failures MUST be non-fatal (log a warning, record `status: failed` in `workarounds_applied.json`, continue) because `git apply` returns non-zero when a patch is already applied, which is a safe no-op. `python_script` failures MUST be fatal because arbitrary mutation state after a partial apply is unknown and dangerous.

### Non-Functional Requirements (Normative)

- NFR-SEC-001: The `python_script` action kind MUST execute in an isolated subprocess with `cwd` set to the consumer repo root and MUST NOT receive the host shell environment except for a curated allowlist (`HOME`, `PATH`, `BLUEPRINT_UPGRADE_REF`, `BLUEPRINT_UPGRADE_SOURCE`). Blueprint authors committing a `python_script` workaround MUST obtain explicit Security sign-off on that entry before it is merged. No consumer-side opt-in flag is required — trust is inherited from the blueprint author model; the blueprint already ships and executes make targets, shell scripts, and Python helpers on every upgrade, and workaround scripts represent no additional trust surface. (Option A, decided by owner comment on PR #292, 2026-05-14.)

- NFR-REL-001: Workaround application and revert MUST complete in under 10 seconds for a catalogue of up to 20 workarounds. The pipeline exit code from Stage 1c MUST propagate correctly so `$pipeline_exit` is set on failure.

- NFR-REL-002: The manifest schema MUST be forward-compatible — adding a new version block MUST NOT break consumers running an older version of the pipeline that does not know about the new block.

- NFR-OPS-001: `artifacts/blueprint/workarounds_applied.json` MUST include a `catalogue_version`, `target_blueprint_version`, `applied_at` timestamp, and per-workaround `status` (`applied`, `skipped`, `failed`, `reverted`) so downstream tooling can reason about upgrade state without re-parsing logs.

- NFR-A11Y-001: N/A — no UI components.

## Normative Option Decision
- Selected option: OPTION_A — `apply_phase` field with two-phase execution (Stage 1c before apply, Stage 2c after apply)
- Rationale: Makes execution ordering explicit in the manifest; enables full coverage of consumer-owned and blueprint-managed file patches using the same action kinds; forward-compatible if new action kinds are added. Decided by owner comment on PR #292, 2026-05-14.

## Contract Changes (Normative)
- Config/Env contract: no new env vars required — trust is inherited from blueprint author model (Q-3 resolved Option A)
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new make targets required; Stage 1c is internal to the existing pipeline shell script
- Docs contract: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` MUST be updated to document the workaround catalogue mechanism and how to author a new entry; `docs/blueprint/architecture/decisions/ADR-issue-268-consumer-workarounds-catalogue.md` MUST be created

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — this spec implements the escalation mechanism itself
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001: `workarounds/manifest.yaml` is present at `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` and passes schema validation.

- AC-002: Per-version workaround directories exist at `.agents/skills/blueprint-consumer-upgrade/workarounds/v1.10.0/` with action files for #258, #259, #260, #261.

- AC-003: Pipeline Stage 1c logs each applied workaround: `[PIPELINE] Stage 1c: applied workaround #<id> — <title>`.

- AC-004: `artifacts/blueprint/workarounds_applied.json` is written after Stage 1c with correct fields: `catalogue_version`, `target_blueprint_version`, `applied_at`, and per-entry `status`.

- AC-005: A `contract_merge` workaround that adds YAML entries applies cleanly, records `status: applied`, and reverts cleanly when the next upgrade targets a version >= `landed_in`.

- AC-006: A workaround whose `applies_when.repo_mode` does not match the consumer's `repo_mode` is skipped and logged: `[PIPELINE] Stage 1c: skipped workaround #<id> — <title> (applies_when mismatch)`.

- AC-007: Test: synthetic blueprint version `v0.0.1-test` with a `contract_merge` workaround — apply emits correct log and `workarounds_applied.json`; subsequent run with version `>= landed_in` reverts the entry.

- AC-008: Test: `applies_when` mismatch — workaround with `repo_mode: generated-consumer` is skipped when consumer is `template-source` mode.

- AC-009: Per-action-kind failure policy is enforced: a `contract_merge` application failure exits non-zero (fatal); a `patch` application failure logs a warning, records `status: failed` in `workarounds_applied.json`, and continues (non-fatal); a `python_script` application failure exits non-zero (fatal).

## Informative Notes (Non-Normative)
- Context: This is the last open child of tracking issue #262. All Tier 1 items (#263–#267, #269) are closed; #270 and #271 are also closed. This item closes the per-consumer rediscovery cost for known upstream defects.
- Referenced upstream defects: #258 (source-tree coverage gap), #259 (behavioral check false-positive symbols), #260 (template-smoke skip for generated-consumer), #261 (volatile artifacts in fresh-env-gate). Fixes are in PR #274 (merged), not yet tagged.
- Tradeoffs: The catalogue adds complexity to the pipeline (new stage, new artefact, revert logic). The payoff is that every future blueprint release can ship workarounds for known defects rather than relying on consumer-side documentation and per-consumer rediscovery.
- Clarifications: All four open questions (Q-1 through Q-4) resolved by owner comment on PR #292, 2026-05-14. Q-1: Option A (apply_phase field). Q-2: Option C (per action-kind failure policy). Q-3: Option A (inherit blueprint trust). Q-4: Option A (landed_in: null, bumped at next release).

## Explicit Exclusions
- `env_var` action kind (modifying `.envrc`) — excluded from initial implementation; risk of persistent consumer environment pollution; revisit if a concrete use case arises.
- Workaround authoring CI validation (ensuring `action_path` files exist in the manifest) — excluded from initial scope; documented as a follow-up in `hardening_review.md`.
- Automatic `landed_in` bumping via CI — excluded; catalogue maintainer responsibility.
