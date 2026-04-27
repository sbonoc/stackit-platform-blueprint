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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-216-upgrade-source-only-filter.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale:
  - SDD-C-007: Blueprint tooling layer (standalone Python script); no DDD/Clean Architecture layer separation applies.
  - SDD-C-013: No STACKIT managed services in scope.
  - SDD-C-014: CLI tooling script — no k8s runtime, Crossplane, ESO, ArgoCD, or Keycloak involvement.
  - SDD-C-015: No app delivery workflow or Make-target contract affected.
  - SDD-C-018: N/A — this work item IS the upstream blueprint fix.
  - SDD-C-022: No HTTP routes, filters, or API endpoints touched.

## Implementation Stack Profile (Normative)
- Backend stack profile: python (pure Python 3 scripts; blueprint tooling only — no FastAPI or Pydantic runtime)
- Frontend stack profile: none
- Test automation profile: pytest (unit and fixture contract tests only)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint CLI tooling scripts only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: blueprint CLI scripts run locally without k8s runtime; Crossplane/ESO/ArgoCD/Keycloak not involved in this tooling fix

## Objective
- Business outcome: Consumers upgrading to v1.8.0 MUST NOT have their `source_only` contract field silently overwritten with the upstream 9-entry list, which causes `infra-validate` to fail for any consumer that has `specs/`, `CLAUDE.md`, `docs/src`, or other commonly-populated paths. Closes issue #216 filed by dhe-marketplace during their v1.8.0 upgrade.
- Success metric: After Stage 3 resolver runs, the consumer's upgraded `blueprint/contract.yaml` `source_only` field MUST NOT contain entries whose paths exist in the consumer repo, and consumer-added `source_only` entries MUST be preserved.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `resolve_contract_conflict` in `scripts/lib/blueprint/resolve_contract_upgrade.py` MUST apply a `_filter_source_only` step after resolving all other fields: it MUST drop source `source_only` entries whose paths exist on disk in the consumer repo (Phase 1), and MUST retain consumer-added `source_only` entries (paths in the consumer's `source_only` that are not in the source's `source_only`) whose paths exist on disk (Phase 2 carry-forward).
- FR-002 The `_filter_source_only` function MUST accept the source `source_only` list, the consumer's current `source_only` list, and the `repo_root` path, and MUST return the filtered list along with counts of dropped and carried-forward entries for decision-log output.
- FR-003 The `ContractResolveResult` dataclass MUST be extended with `dropped_source_only` and `kept_consumer_source_only` fields for transparency in logging and the decisions JSON artifact.
- FR-004 The `artifacts/blueprint/contract_resolve_decisions.json` MUST include `dropped_source_only` and `kept_consumer_source_only` arrays in the output.
- FR-005 A regression test fixture MUST assert: given a consumer with populated `specs/` and `CLAUDE.md` and a source contract containing those paths in `source_only`, after Stage 3 the resolved `source_only` SHALL NOT contain `specs` or `CLAUDE.md`, and the subsequent fixture-level `infra-validate` check SHALL pass.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 Path existence checks MUST use `Path.exists()` against `repo_root`-relative paths; no shell expansion or external process execution MUST be introduced.
- NFR-OBS-001 Stage 3 pipeline output MUST log the count of dropped source `source_only` entries (Phase 1) and count of consumer-added entries carried forward (Phase 2) to stdout.
- NFR-REL-001 The change MUST be backward-compatible: consumers with no consumer-added `source_only` entries and no conflicts between source and consumer paths MUST produce an identical result to the current behavior for those entries.
- NFR-OPS-001 All regression test assertions MUST be runnable via `pytest` without requiring a live k8s cluster or external network access.

## Normative Option Decision
- Option A (restore Phase 1 + Phase 2 filter inside Stage 3): add `_filter_source_only` to `resolve_contract_upgrade.py` implementing Phase 1 (drop source entries existing on disk) and Phase 2 (carry forward consumer additions existing on disk). Semantically equivalent to v1.7.0 behavior.
- Option B (document workaround; defer fix): consumers manually post-edit `source_only` after Stage 3 runs. No code changes. Imposes manual maintenance on every consumer after every upgrade.
- Selected option: OPTION_A
- Rationale: Option B is the current state — it IS the bug. The v1.7.0 resolver had the correct semantics. Option A restores them with an explicit, testable implementation. The filter is deterministic and bounded.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new Make targets; Stage 3 log output extended with dropped/carried-forward counts
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/216
- Temporary workaround path: `blueprint/contract.yaml` → manually post-edit `source_only` after Stage 3 to drop entries that exist in the consumer and re-add consumer extensions
- Replacement trigger: merged PR in this blueprint repo containing FR-001 through FR-005 fixes
- Workaround review date: 2026-07-27

## Normative Acceptance Criteria
- AC-001 GIVEN a consumer with `specs/` populated and a source contract with `specs` in `source_only`, WHEN Stage 3 runs, THEN the resolved `blueprint/contract.yaml` SHALL NOT contain `specs` in `source_only`.
- AC-002 GIVEN a consumer with `CLAUDE.md` present and a source contract with `CLAUDE.md` in `source_only`, WHEN Stage 3 runs, THEN the resolved `blueprint/contract.yaml` SHALL NOT contain `CLAUDE.md` in `source_only`.
- AC-003 GIVEN a consumer with a consumer-added `source_only` entry `docs/blueprint/architecture/decisions/ADR-specific.md` (not in source `source_only`) and that file exists on disk, WHEN Stage 3 runs, THEN that entry SHALL be preserved in the resolved `source_only`.
- AC-004 GIVEN the resolved contract from AC-001/AC-002, WHEN `make infra-validate` runs, THEN it SHALL pass with no `file must be absent` errors for `specs` or `CLAUDE.md`.
- AC-005 GIVEN a consumer with no consumer-added `source_only` entries and no on-disk conflicts, WHEN Stage 3 runs, THEN the resolved `source_only` SHALL equal the source `source_only` (backward-compatible behavior preserved).

## Informative Notes (Non-Normative)
- Context: The v1.8.0 `resolve_contract_upgrade.py` refactor simplified Stage 3 by taking everything except `required_files` and `prune_globs` wholesale from source. This accidentally removed the `_filter_source_only` logic that was responsible for dropping source entries conflicting with consumer-owned paths. The dhe-marketplace consumer discovered this when `infra-validate` failed for `specs`, `CLAUDE.md`, `docs/src`, and 4 other paths after their v1.8.0 upgrade.
- Tradeoffs: The Phase 1 filter adds one `Path.exists()` call per source `source_only` entry (≤10 entries in practice); negligible overhead. The Phase 2 carry-forward requires iterating the consumer's current `source_only` list (also ≤10 entries). Total overhead is immaterial.

## Explicit Exclusions
- Changes to the `source_only` schema or contract.yaml structure: no schema changes required.
- Glob/directory support in the Stage 3 resolver: separate concern (addressed in Group A, issues #214/#215).
