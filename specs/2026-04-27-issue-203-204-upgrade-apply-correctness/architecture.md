# Architecture

## Context
- Work item: 2026-04-27-issue-203-204-upgrade-apply-correctness
- Owner: bonos
- Date: 2026-04-27

## Stack and Execution Model
- Backend stack profile: python_scripts (scripts/lib/blueprint)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Two correctness bugs in `scripts/lib/blueprint/upgrade_consumer.py` Stage 2 apply path. (1) The prune guard only covers `base/apps/` via a hardcoded path prefix; consumer files renamed outside that directory and referenced by a `kustomization.yaml` are silently deleted. (2) `git merge-file` does not detect duplicate Terraform block declarations; byte-identical blocks are emitted twice, producing `terraform validate` failures.
- Scope boundaries: `scripts/lib/blueprint/upgrade_consumer.py` and its test file `tests/blueprint/test_upgrade_consumer.py`. No contract schema, make targets, or CLI flags change.
- Out of scope: `apps.yaml` consumer app descriptor, non-Terraform structured file deduplication, `terraform validate` in VALIDATION_TARGETS.

## Bounded Contexts and Responsibilities
- Context A — Prune guard: `_classify_entries` in `upgrade_consumer.py` decides the action for each candidate path. The new `_is_kustomization_referenced` predicate extends this decision: if a file is absent in the blueprint source and referenced in a consumer kustomization.yaml, it is classified `consumer-kustomization-ref / skip` rather than proceeding to the delete branch.
- Context B — Terraform post-merge: `_three_way_merge` is a pure function returning `(merged_content, has_conflicts)`. A new `_tf_deduplicate_blocks` function processes its output for `.tf` files, returning `(cleaned_content, removed_blocks)`. The apply loop calls this after every clean merge on a `.tf` path.

## High-Level Component Design
- Domain layer: upgrade planner classification logic (`_classify_entries`) and apply loop in `upgrade_consumer.py`
- Application layer: `_is_kustomization_referenced(repo_root, relative_path) -> bool` — filesystem scan of kustomization.yaml files; `_tf_deduplicate_blocks(content: str) -> tuple[str, list[str]]` — regex-based top-level block scanner
- Infrastructure adapters: `yaml.safe_load` for kustomization.yaml parsing; `re` for Terraform block scanning; no new external dependencies
- Presentation/API/workflow boundaries: apply artifact JSON (`artifacts/blueprint/upgrade/upgrade_apply.json`) gains `consumer_kustomization_ref_count` and `tf_dedup_count` fields; `ApplyResult.reason` is enriched for dedup events

## Integration and Dependency Edges
- Upstream dependencies: `_classify_entries` called from `run_plan` and `run_apply`; `_three_way_merge` called from the apply loop — both within `upgrade_consumer.py`
- Downstream dependencies: apply artifact JSON consumed by `upgrade_consumer_postcheck.py` and surfaced in the scripted pipeline report
- Data/API/event contracts touched: apply artifact JSON schema (additive — new counters, no removed fields)

## Non-Functional Architecture Notes
- Security: `yaml.safe_load` prevents YAML deserialization of arbitrary Python objects; no shell execution in the ref-check path
- Observability: deduplication events logged to `ApplyResult.reason` and `deduplication_log` in apply artifact; kustomization-ref skips counted in `consumer_kustomization_ref_count`
- Reliability and rollback: both functions are additive — if `_is_kustomization_referenced` raises, it defaults to `False` (conservative: does not protect the file, but does not crash the pipeline); if `_tf_deduplicate_blocks` raises, the apply loop surfaces a conflict artifact rather than writing corrupted content
- Monitoring/alerting: non-zero `tf_dedup_count` in the apply artifact is a signal that a 3-way merge produced structural anomalies; consumers should review the `deduplication_log` entries

## Risks and Tradeoffs
- Risk 1: kustomization.yaml ref-scan adds filesystem reads per candidate delete path; mitigated by caching parsed kustomization.yaml content within a single apply run (keyed by absolute path)
- Tradeoff 1: Terraform block scanner uses regex, not a full HCL parser; may miss edge cases (multi-line block headers, comments inside headers); acceptable because the target case (duplicate `variable` blocks from 3-way merge) follows a simple single-line declaration pattern; a follow-up can add `terraform validate` to VALIDATION_TARGETS for broader coverage
