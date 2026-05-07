# Architecture

## Context
- Work item: 2026-04-27-issue-216-upgrade-source-only-filter
- Owner: Blueprint maintainer
- Date: 2026-04-27

## Stack and Execution Model
- Backend stack profile: Python 3 CLI scripts (blueprint tooling only)
- Frontend stack profile: none
- Test automation profile: pytest unit and fixture contract tests
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `resolve_contract_upgrade.py` Stage 3 starts with `resolved = source.copy()` then only overrides `required_files` and `source_artifact_prune_globs_on_init`. All other fields, including `spec.repository.ownership_path_classes.source_only`, are taken wholesale from source. The v1.7.0 resolver had `_filter_source_only` logic (FR-009) that dropped source entries existing on disk in the consumer and carried forward consumer additions. That logic was removed in the v1.8.0 refactor. After v1.8.0 upgrade, consumers with `specs/`, `CLAUDE.md`, `docs/src`, etc. get those paths in `source_only`, causing `infra-validate` to report `file must be absent` for consumer-owned files.
- Scope boundaries: One new function `_filter_source_only` added to `resolve_contract_upgrade.py`; two new fields in `ContractResolveResult`; extension of decision JSON output; one regression test fixture. No schema changes, no CLI flag changes, no Make target additions.
- Out of scope: Glob/directory support in the Stage 3 resolver (addressed in Group A); changes to the upgrade pipeline orchestration beyond Stage 3.

## Bounded Contexts and Responsibilities
- Context A — Stage 3 Contract Resolver (`scripts/lib/blueprint/resolve_contract_upgrade.py::resolve_contract_conflict`): resolves `blueprint/contract.yaml` using deterministic merge rules. Missing the FR-009 `source_only` filter step that prevents source entries from overwriting consumer-owned paths.
- Context B — Decision Log (`artifacts/blueprint/contract_resolve_decisions.json`): captures Stage 3 decisions for auditing. Extended to include `source_only` drop/keep decisions.

## High-Level Component Design
No diagram required — single function addition within an existing script; no new component boundaries.

- New function `_filter_source_only(source_list, consumer_list, repo_root)`:
  - Phase 1: drop source entries where `(repo_root / entry).exists()` (path exists in consumer) — prevents infra-validate failures for consumer-owned paths
  - Phase 2: carry forward consumer-added entries (in consumer_list but not source_list) where `(repo_root / entry).exists()` — preserves consumer extensions (e.g., per-ADR enumeration workaround for #214)
  - Returns `(merged_list, dropped_source, kept_consumer)` for logging and decision JSON

- Integration in `resolve_contract_conflict`: after FR-006 and FR-007, apply `_filter_source_only` to `resolved["spec"]["repository"]["ownership_path_classes"]["source_only"]` using source and target `source_only` lists.

- `ContractResolveResult` extension: add `dropped_source_only: list[str] = field(default_factory=list)` and `kept_consumer_source_only: list[str] = field(default_factory=list)`.

## Integration and Dependency Edges
- Upstream dependencies: `spec.repository.ownership_path_classes.source_only` parsed from source and target YAML in the conflict JSON (already available via `_get_nested`).
- Downstream dependencies: `make blueprint-upgrade-consumer-apply` (Stage 3 pipeline step); `artifacts/blueprint/contract_resolve_decisions.json` (additive extension).
- Data/API/event contracts touched: `contract_resolve_decisions.json` extended with `dropped_source_only` and `kept_consumer_source_only` arrays (additive; backward-compatible).

## Non-Functional Architecture Notes
- Security: Path checks use `Path.exists()` on `repo_root`-relative paths only; no shell expansion, no symlink traversal outside root, no subprocess execution (NFR-SEC-001).
- Observability: Pipeline stdout extended with dropped/kept counts matching existing logging pattern for `dropped_required_files` and `dropped_prune_globs` (NFR-OBS-001).
- Reliability and rollback: Filter is additive to existing FR-005/FR-006/FR-007 logic; no existing merge paths are changed. Rollback = revert the PR.
- Monitoring/alerting: No runtime alerting required for CLI tooling scripts.

## Risks and Tradeoffs
- Risk 1: A consumer that intentionally lists an on-disk path in `source_only` will have that entry silently dropped by Phase 1. Mitigation: decision log records all drops; this was also v1.7.0 behavior (known semantic).
- Tradeoff 1: Phase 2 carry-forward drops consumer-added entries for paths that don't exist on disk (orphaned entries). This matches v1.7.0 semantics and prevents stale source_only accumulation.
