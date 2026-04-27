# Architecture

## Context
- Work item: 2026-04-27-issue-214-215-source-only-glob-and-validate
- Owner: Blueprint maintainer
- Date: 2026-04-27

## Stack and Execution Model
- Backend stack profile: Python 3 CLI scripts (blueprint tooling only)
- Frontend stack profile: none
- Test automation profile: pytest unit and fixture contract tests
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Two independent functions handle `source_only` contract entries and both fail on non-file entries: `audit_source_tree_coverage` (upgrade_consumer.py) builds `all_coverage_roots` from ownership categories that exclude `source_artifact_prune_globs_on_init`, causing prune-globbed source files to appear as uncovered (#214). `_validate_absent_files` (validate_contract.py) calls `exists()` on every `source_only` entry — directories return `True` and falsely trigger an error (#215). Consumers cannot use a single directory prefix as a workaround for #214 because #215 blocks it.
- Scope boundaries: Two Python functions in two existing scripts; one new pytest fixture; one ADR. No schema changes, no new CLI flags, no Make target additions.
- Out of scope: Glob support for `source_only` entries in other validation contexts; changes to `contract.yaml` schema; changes to the upgrade pipeline beyond the audit step.

## Bounded Contexts and Responsibilities
- Context A — Upgrade audit (`scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage`): responsible for computing which source-repo files are "covered" by the consumer contract. Currently omits prune-glob-resolved files from coverage, causing false uncovered counts.
- Context B — Contract validation (`scripts/bin/blueprint/validate_contract.py::_validate_absent_files`): responsible for checking that `source_only` entries are absent in generated-consumer repos. Currently cannot distinguish file paths from directory paths.

## High-Level Component Design
No diagram required — changes are isolated two-function patches with no new component boundaries.

- Upgrade audit fix (FR-001): In `audit_source_tree_coverage`, after the existing coverage-roots union is built, resolve the prune-glob patterns from the `source_artifact_prune_globs_on_init` list against the tracked file list of the source repo (using `fnmatch.fnmatch`) and add the matched paths to `all_coverage_roots`. No structural change to the function signature or callers.
- Absent-file validator fix (FR-002 + FR-003): In `_validate_absent_files`, classify each entry before checking: (1) entries containing `*` or ending with `/` are glob/prefix patterns — check via `Path.rglob` or `fnmatch` against the consumer repo's file list; (2) all other entries use `is_file()` (existing behavior, changed from `exists()`). No signature or caller changes.

## Integration and Dependency Edges
- Upstream dependencies: `consumer_init.source_artifact_prune_globs_on_init` field in `blueprint/contract.yaml` (already parsed by the upgrade engine and available at audit call site).
- Downstream dependencies: `make blueprint-upgrade-consumer-apply` → calls `audit_source_tree_coverage`; `make infra-validate` → calls `_validate_absent_files`.
- Data/API/event contracts touched: none (internal Python function changes only).

## Non-Functional Architecture Notes
- Security: Glob expansion is bounded to the repository root path using `fnmatch` against pre-enumerated file lists — no shell glob expansion, no symlink traversal outside root, no subprocess execution (NFR-SEC-001).
- Observability: `audit_source_tree_coverage` stderr WARNING output is preserved for genuinely uncovered files (NFR-OBS-001). No new log lines required.
- Reliability and rollback: Both changes are backward-compatible by construction: exact-file entries are unchanged (FR-002 narrows `exists()` to `is_file()`, which is strictly safer for the stated purpose). Rollback = revert the PR.
- Monitoring/alerting: No runtime alerting required for CLI tooling scripts.

## Risks and Tradeoffs
- Risk 1: `fnmatch` glob semantics differ from shell glob semantics (e.g., `**` is not supported in `fnmatch.fnmatch`). Mitigation: use `fnmatch.fnmatch` for simple glob patterns; document that `**` is not supported in `source_artifact_prune_globs_on_init` entries (patterns already in use only use `*`).
- Tradeoff 1: Adding a glob-match pass over the source file list in `audit_source_tree_coverage` is O(N×M) where N = tracked files, M = prune-globs. In practice M ≤ 5 and N ≤ 500, so impact is negligible.
