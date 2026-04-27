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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-214-215-source-only-glob-and-validate.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale:
  - SDD-C-007: Blueprint tooling layer (standalone Python scripts); no DDD/Clean Architecture layer separation applies.
  - SDD-C-013: No STACKIT managed services in scope.
  - SDD-C-014: CLI tooling scripts — no k8s runtime, Crossplane, ESO, ArgoCD, or Keycloak involvement.
  - SDD-C-015: No app delivery workflow or Make-target contract affected.
  - SDD-C-018: N/A — this work item IS the upstream blueprint fix; no consumer-side workaround tracking needed here.
  - SDD-C-022: No HTTP routes, filters, or API endpoints touched.

## Implementation Stack Profile (Normative)
- Backend stack profile: python (pure Python 3 scripts; blueprint tooling only — no FastAPI or Pydantic runtime)
- Frontend stack profile: none
- Test automation profile: pytest (unit and fixture contract tests only)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint tooling scripts only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: blueprint CLI scripts run locally without k8s runtime; Crossplane/ESO/ArgoCD/Keycloak not involved in this tooling fix

## Objective
- Business outcome: Consumers upgrading to v1.8.0+ MUST NOT be blocked by false-positive `uncovered_source_files_count` errors caused by prune-globbed files, and MUST be able to declare directory-prefix or glob entries in `source_only` without the contract validator rejecting them. Closes issues #214 and #215, filed by dhe-marketplace during their v1.8.0 upgrade.
- Success metric: `blueprint-upgrade-consumer-apply` succeeds without uncovered-source-file errors for any consumer whose contract declares `source_artifact_prune_globs_on_init`; `infra-validate` accepts directory-prefix and glob entries in `source_only` without false-positive errors.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `audit_source_tree_coverage` in `scripts/lib/blueprint/upgrade_consumer.py` MUST extend `all_coverage_roots` with the resolved set of files in the source repository that match any glob in `consumer_init.source_artifact_prune_globs_on_init`, so that prune-glob-matched files do not appear in `uncovered_source_files` and do not increment `uncovered_source_files_count`.
- FR-002 `_validate_absent_files` in `scripts/bin/blueprint/validate_contract.py` MUST use `is_file()` instead of `exists()` for path-shaped `source_only` entries, so that directory paths that exist in the consumer do not falsely trigger absent-file validation errors.
- FR-003 `_validate_absent_files` MUST support glob-pattern entries in `source_only` (entries containing `*` or ending with `/`): for each such entry it MUST check whether any file under the consumer repo matching that pattern exists, and MUST NOT evaluate the raw pattern string as a literal file path.
- FR-004 A regression test fixture MUST assert: (a) a directory-prefix entry in `source_only` passes `_validate_absent_files` when the directory exists but contains no files matching the pattern not covered by other ownership classes; (b) a glob-pattern entry in `source_only` passes when no matching file exists in the consumer; (c) `uncovered_source_files_count` is 0 when prune-glob-matched files exist in the source repo.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 Glob expansion in `_validate_absent_files` and `audit_source_tree_coverage` MUST be bounded to the repository root using `Path.rglob` or `fnmatch` against pre-enumerated repo paths, and MUST NOT follow symlinks outside the root or invoke external processes.
- NFR-OBS-001 `audit_source_tree_coverage` MUST continue to emit a `WARNING` line to stderr for each file that is genuinely uncovered after accounting for prune-glob-resolved coverage.
- NFR-REL-001 Both changes MUST be backward-compatible: existing exact-file `source_only` entries MUST behave identically — a file entry that is present in the consumer MUST still trigger an absent-file error.
- NFR-OPS-001 All new regression test assertions MUST be runnable via `pytest` without requiring a live k8s cluster or external network access.

## Normative Option Decision
- Option A (prune-glob-as-coverage + is_file validator): extend `all_coverage_roots` with resolved prune-glob matches; change `_validate_absent_files` to `is_file()` for path entries and add glob expansion for glob-shaped entries.
- Option B (consumer-enumerates-each-file): consumers enumerate each prune-globbed file in `source_only` explicitly; no code changes.
- Selected option: OPTION_A
- Rationale: Prune-glob-matched files are definitionally covered by the prune action at consumer init; treating them as covered in the audit is semantically correct and eliminates unbounded per-release maintenance for all consumers. Option B imposes manual upkeep for every new blueprint ADR on every consumer, which scales poorly and is the root cause of issue #214.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new Make targets; `infra-validate` and `blueprint-upgrade-consumer-apply` output changes (false-positive errors removed)
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/214, https://github.com/sbonoc/stackit-platform-blueprint/issues/215
- Temporary workaround path: `blueprint/contract.yaml` → enumerate each blueprint-internal ADR file path explicitly under `source_only` (consumer-side)
- Replacement trigger: merged PR containing FR-001 through FR-004 fixes in this blueprint repo
- Workaround review date: 2026-07-27

## Normative Acceptance Criteria
- AC-001 GIVEN a source repo with `source_artifact_prune_globs_on_init: ["docs/blueprint/architecture/decisions/ADR-*.md"]` and N ADR files under that path, WHEN `audit_source_tree_coverage` runs, THEN none of those ADR files SHALL appear in the uncovered list and `uncovered_source_files_count` SHALL be 0.
- AC-002 GIVEN a consumer `source_only` entry of `docs/blueprint/architecture/decisions/` (directory), WHEN `_validate_absent_files` runs and that directory exists in the consumer with files, THEN no error SHALL be emitted for the directory-prefix entry itself.
- AC-003 GIVEN a consumer `source_only` glob entry `docs/blueprint/architecture/decisions/ADR-*.md` and a matching ADR file present in the consumer repo, WHEN `_validate_absent_files` runs, THEN an error SHALL be emitted for each matching file.
- AC-004 GIVEN a consumer `source_only` glob entry and NO matching file in the consumer, WHEN `_validate_absent_files` runs, THEN no error SHALL be emitted.
- AC-005 GIVEN an existing exact-file `source_only` entry (no glob characters, resolves to a file) and that file present in the consumer, WHEN `_validate_absent_files` runs, THEN an error SHALL be emitted (backward-compatible behavior preserved).

## Informative Notes (Non-Normative)
- Context: Issues #214 and #215 are two halves of the same ergonomics failure: #214 forces consumers to manually list prune-globbed files in `source_only`; #215 blocks the natural shortcut (single directory entry). The dhe-marketplace consumer discovered both during v1.8.0 upgrade and has a per-ADR workaround in place until this is fixed.
- Tradeoffs: FR-001 adds an `fnmatch`/`glob` pass over source tree files during audit. This adds negligible overhead (the list is already enumerated by `_source_repo_tracked_files`). FR-002/FR-003 add branch logic to `_validate_absent_files` but leave the hot path (exact-file entries) unchanged.

## Explicit Exclusions
- Glob support for `source_only` in paths other than `_validate_absent_files` (e.g., template coverage checks): out of scope for this fix.
- Changes to the `source_only` schema or contract.yaml structure: no schema changes required.
