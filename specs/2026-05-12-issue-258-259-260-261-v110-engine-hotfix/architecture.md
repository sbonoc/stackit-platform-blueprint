# Architecture

## Context
- Work item: 2026-05-12-issue-258-259-260-261-v110-engine-hotfix
- Owner: Blueprint maintainer
- Date: 2026-05-12

## Stack and Execution Model
- Backend stack profile: python (pure Python 3 scripts and YAML; blueprint tooling only)
- Frontend stack profile: none
- Test automation profile: pytest (unit and regression tests only)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Four independent bugs in the v1.10.0 blueprint upgrade pipeline block every consumer upgrade. (1) `blueprint/contract.yaml` leaves four source files unclassified — `pyproject.toml`, `uv.lock`, `infra/local/helm/opensearch/values.yaml`, `infra/local/helm/kms/values.yaml` — so Stage 2 (apply) aborts with `BLOCKED`. (2) `upgrade_consumer_validate.py` includes `blueprint-template-smoke` in `VALIDATION_TARGETS` unconditionally; this target fails for generated-consumer repos because `blueprint-init-repo` refuses to rerun when `repo_mode=generated-consumer`. (3) `upgrade_fresh_env_gate.py` compares SHA-256 checksums of all non-volatile artifacts, but `upgrade_validate.json` and `required_files_status.json` embed absolute repo paths in their captured stdout, so checksums always diverge between the clean worktree and the working tree. (4) `upgrade_shell_behavioral_check.py` caps source resolution at depth 1, missing all functions defined in transitively sourced library files; this produces 29 false-positive unresolved symbols across 73 occurrences in blueprint-managed scripts.
- Scope boundaries: `blueprint/contract.yaml` (classification entries); `scripts/lib/blueprint/upgrade_consumer_validate.py` (`VALIDATION_TARGETS` filtering); `scripts/lib/blueprint/upgrade_fresh_env_gate.py` (`_VOLATILE_ARTIFACT_NAMES`); `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` (transitive resolver + bare-command suppression).
- Out of scope: Consumer-side workaround removal; JSON artifact schema changes; pipeline shell wrapper scripts (`upgrade_consumer_pipeline.sh`, `upgrade_consumer.sh`); behavioral check semantic analysis beyond source-chain function definitions.

## Bounded Contexts and Responsibilities
- Context A — Contract coverage audit (FR-001): `blueprint/contract.yaml` is the single source of truth for file ownership classification. `audit_source_tree_coverage` in `scripts/lib/blueprint/upgrade_consumer.py` merges the source contract with the consumer contract and computes `uncovered_source_files_count`. Adding the four missing entries to the appropriate classification sections closes the coverage gap with zero engine changes.
- Context B — Validate target filtering (FR-002): `upgrade_consumer_validate.py` runs a hard-coded `VALIDATION_TARGETS` tuple as the validation step. The `quality-hooks-strict` runner already applies a `repo_mode`-aware skip for `blueprint-template-smoke` (emits `quality_template_smoke_total status=skipped repo_mode=generated-consumer`). The validate module must apply the same skip so the postcheck gate is consistent between the two execution paths.
- Context C — Volatile artifact names (FR-003): `upgrade_fresh_env_gate.py` computes SHA-256 checksums of all files under `artifacts/blueprint/` that are not in `_VOLATILE_ARTIFACT_NAMES`. Artifacts that capture the output of `infra-contract-test-fast` (and similar) include absolute script paths in their stdout fields. These paths are inherently machine-specific. Adding both filenames to `_VOLATILE_ARTIFACT_NAMES` is the minimal correct fix; path normalization in the artifact writers is excluded to avoid schema risk.
- Context D — Transitive behavioral check (FR-004): `upgrade_shell_behavioral_check.py` resolves function definitions using `resolve_depth1_sources` and `collect_defined_functions_depth1`. Shell scripts in the blueprint commonly follow a two-level source pattern: `scripts/bin/infra/X.sh` sources `scripts/lib/infra/X.sh` which sources `scripts/lib/infra/common.sh` or module-specific helpers. Depth-1 sees only the direct sources of the script under analysis; all symbols defined one hop further are flagged as unresolved. The fix replaces the depth-1 traversal with a BFS over the full source chain, tracking visited paths to break cycles.

## High-Level Component Design
- Domain layer: N/A — blueprint tooling scripts, not a DDD application
- Application layer: N/A
- Infrastructure adapters: N/A
- Presentation/API/workflow boundaries: All four components are standalone Python modules invoked by make targets via shell wrappers. No HTTP boundaries or service calls.

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml` — read by `audit_source_tree_coverage` (Contexts A) and `upgrade_consumer_validate.py` (Context B)
  - Shell scripts under `scripts/bin/` and `scripts/lib/` — analyzed by the behavioral check (Context D)
- Downstream dependencies:
  - `make blueprint-upgrade-consumer` — calls all four fixed components in sequence
  - `make blueprint-upgrade-consumer-postcheck` — calls the validate and behavioral check components
  - `make blueprint-upgrade-fresh-env-gate` — calls the fresh-env gate
- Data/API/event contracts touched: JSON artifact schemas for `upgrade_validate.json`, `required_files_status.json`, `fresh_env_gate.json` — all preserved unchanged.

## Non-Functional Architecture Notes
- Security: No authentication or secrets handling involved. File reads in Context D are bounded to the consumer repo root via absolute-path resolution from `scripts/lib/shell/root_dir.sh`; the BFS traversal MUST NOT follow symlinks outside the root.
- Observability: All existing `WARNING`/`ERROR` log lines in the four affected modules are preserved. The BFS extension in Context D does not add new warning lines (the warnings are emitted by the caller, not the resolver).
- Reliability and rollback: Each fix is independently deployable — they touch separate files. Rollback = revert the relevant file change. No state migration or artifact schema change is required.
- Monitoring/alerting: N/A — no runtime service affected.

## Risks and Tradeoffs
- Risk 1 (Context D — cycle detection): A shell script that transitively sources itself (directly or indirectly) would cause infinite recursion without a visited-set guard. Mitigation: the BFS MUST maintain a `frozenset` of already-visited absolute paths and skip any path already in the set before opening the file.
- Tradeoff 1 (Context C — volatile-set vs. path normalization): Adding both filenames to `_VOLATILE_ARTIFACT_NAMES` means the fresh-env gate can never detect behavioral divergences in those two specific artifacts. The alternative — normalizing absolute paths to repo-relative before writing the artifacts — would be more precise but requires modifying three artifact writers and risks introducing field-level schema drift. The volatile-set approach is accepted because the divergences are purely cosmetic (absolute paths differ between machines) and the behavioral content that matters (make target pass/fail, validation results) is already validated by the make targets themselves.
